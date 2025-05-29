import os
import asyncio
from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage
from langchain_google_spanner import SpannerGraphStore, SpannerGraphVectorContextRetriever
from langchain_google_vertexai import VertexAIEmbeddings, ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from google.oauth2 import service_account # Import for loading credentials object
from datetime import datetime

load_dotenv() # Load environment variables from .env file

# --- Configuration ---
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "graphrag-460523")
SPANNER_INSTANCE_ID = os.getenv("SPANNER_INSTANCE_ID", "graphrag-instance")
SPANNER_DATABASE_ID = os.getenv("SPANNER_DATABASE_ID", "graphrag-db")
CREDENTIALS_FILE_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH", "../GraphRAG-IAM-Admin.json")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

EMBEDDING_MODEL_NAME = "text-embedding-004" # Must match ingestion, Or "text-embedding-005" / "gemini-embedding-001"
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-05-20" # Using PaLM 2 which is more widely available

# --- URL Fixing Function ---
def fix_citation_url(url: str) -> str:
    """
    Fix citation URLs by:
    1. Converting the last underscore to a forward slash
    2. URL decoding any encoded characters (e.g., %C3%A9, C3A9 -> é)
    Example: 'kit-kat_kitkat-mega' -> 'kit-kat/kitkat-mega'
    Example: 'nescaf%C3%A9' -> 'nescafé'
    """
    if not url or url == "Unknown source":
        return url
    
    # First, decode any URL-encoded characters
    import urllib.parse
    try:
        decoded_url = urllib.parse.unquote(url)
    except Exception as e:
        print(f"Warning: Could not decode URL {url}: {e}")
        decoded_url = url
    
    # Then, find the last underscore and replace with forward slash
    last_underscore_index = decoded_url.rfind('_')
    if last_underscore_index != -1:
        # Replace the last underscore with a forward slash
        fixed_url = decoded_url[:last_underscore_index] + '/' + decoded_url[last_underscore_index + 1:]
        return fixed_url
    
    return decoded_url

# --- Initialize components ---
credentials = None

# On Cloud Run, prefer Application Default Credentials
# Only use service account file in local development
if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    # Running locally with service account file
    try:
        credentials = service_account.Credentials.from_service_account_file(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        print(f"Successfully loaded credentials from {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
    except Exception as e:
        print(f"Error loading credentials from file: {e}")
        credentials = None
elif CREDENTIALS_FILE_PATH and os.path.exists(CREDENTIALS_FILE_PATH):
    # Fallback to file path if it exists
    try:
        credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE_PATH)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_FILE_PATH
        print(f"Successfully loaded credentials from {CREDENTIALS_FILE_PATH}")
    except Exception as e:
        print(f"Error loading credentials from {CREDENTIALS_FILE_PATH}: {e}")
        credentials = None

if credentials is None:
    print("Using Application Default Credentials (good for Cloud Run)")

# Set the project ID environment variable if not already set
if GCP_PROJECT_ID and not os.environ.get("GOOGLE_CLOUD_PROJECT"):
    os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT_ID
    print(f"Set GOOGLE_CLOUD_PROJECT to {GCP_PROJECT_ID}")

graph_store_params = {
    "instance_id": SPANNER_INSTANCE_ID,
    "database_id": SPANNER_DATABASE_ID,
    "graph_name": "nestle_knowledge_graph_main",
}

try:
    graph_store = SpannerGraphStore(**graph_store_params)
    print("SpannerGraphStore initialized successfully")
except Exception as e:
    print(f"Failed to initialize SpannerGraphStore: {e}")
    raise e

embeddings = VertexAIEmbeddings(
    model_name=EMBEDDING_MODEL_NAME, 
    project=GCP_PROJECT_ID, 
    credentials=credentials,
    location=LOCATION
)

# The retriever expects embeddings to be a property of the nodes.
# The node_label should match what was used during ingestion (e.g., "DocumentChunk")
# The text_properties and embedding_properties should match the keys used in node properties.
retriever = SpannerGraphVectorContextRetriever(
    graph_store=graph_store,
    embedding_service=embeddings,
    node_label="DocumentChunk",  # Matches node_type in ingestion
    text_properties=["text"],    # Properties to consider as text
    embedding_properties=["embedding"],  # Embedding property
    expand_by_hops=0,  # 0 = direct vector search only
    top_k=5
)

# Try to initialize LLM with fallback models
FALLBACK_MODELS = ["text-bison@001", "text-bison", "chat-bison", "gemini-pro"]
llm = None

for model_name in [GEMINI_MODEL_NAME] + FALLBACK_MODELS:
    try:
        print(f"Trying to initialize LLM with model: {model_name}")
        llm = ChatVertexAI(
            model_name=model_name, 
            project=GCP_PROJECT_ID, 
            credentials=credentials, 
            temperature=0.3,
            location=LOCATION
        )
        print(f"Successfully initialized LLM with model: {model_name}")
        break
    except Exception as e:
        print(f"Failed to initialize with {model_name}: {e}")
        continue

if llm is None:
    raise Exception("Failed to initialize any LLM model. Please check your Vertex AI setup and enabled APIs.")

# --- Define Agent State ---
class GraphRAGState(TypedDict):
    question: str
    conversation_history: List[dict] # List of previous messages [{"role": "user/assistant", "content": "...", "timestamp": "..."}]
    context: List[dict] # List of retrieved documents (chunks with metadata)
    answer: str
    cited_sources: List[str]
    error: str | None

# --- Define Pydantic model for structured output with citations ---
class CitedAnswer(BaseModel):
    answer: str = Field(description="The textual answer to the question.")
    sources: List[str] = Field(description="A list of source URLs that support the answer.")

# --- Define Agent Nodes ---

async def retrieve_context(state: GraphRAGState):
    print("---RETRIEVING CONTEXT---")
    question = state["question"]
    try:
        # Use ainvoke instead of deprecated aget_relevant_documents
        retrieved_docs = await retriever.ainvoke(question)
        
        context_for_llm = []
        for doc in retrieved_docs:
            # The retriever returns Document objects where page_content contains JSON data
            # We need to parse this JSON to extract the actual text content
            try:
                import json
                if isinstance(doc.page_content, str) and doc.page_content.startswith('{"path":'):
                    # Parse the JSON structure to extract the actual text
                    data = json.loads(doc.page_content)
                    text = data.get("path", {}).get("properties", {}).get("text", "")
                    source = data.get("path", {}).get("properties", {}).get("source_url", "Unknown source")
                else:
                    # Fallback to original approach if the structure is different
                    text = doc.page_content
                    source = doc.metadata.get("source_url", "Unknown source")
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                print(f"Error parsing document content: {e}")
                print(f"Document content: {doc.page_content[:200]}...")
                # Fallback to original approach
                text = doc.page_content
                source = doc.metadata.get("source_url", "Unknown source")

            # Only add if we have actual text content
            if text and text.strip():
                context_for_llm.append({"text": text, "source_url": fix_citation_url(source)})
        
        print(f"Retrieved {len(context_for_llm)} chunks.")
        if not context_for_llm:
            return {"context": [], "error": "No relevant context found."}
        return {"context": context_for_llm, "error": None}
    except Exception as e:
        print(f"Error retrieving context: {e}")
        return {"context": [], "error": f"Failed to retrieve context: {e}"}

async def generate_answer(state: GraphRAGState):
    print("---GENERATING ANSWER---")
    question = state["question"]
    context = state["context"]
    conversation_history = state.get("conversation_history", [])
    error = state.get("error")

    if error and not context: # If retrieval failed completely
        return {"answer": "I couldn't find any information to answer your question.", "cited_sources": [], "error": error}
    if not context:
        return {"answer": "I couldn't find any relevant information to answer your question.", "cited_sources": []}

    context_str = "\n\n".join([
        f"Source URL: {item['source_url']}\nContent: {item['text']}" for item in context
    ])

    # Build conversation history string
    history_str = ""
    if conversation_history:
        history_str = "\n\nPrevious conversation:\n"
        for msg in conversation_history[-6:]:  # Include last 6 messages for context
            role = "Customer" if msg.get("role") == "user" else "Smartie"
            content = msg.get("content", "")[:200]  # Limit length
            history_str += f"{role}: {content}\n"

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are Smartie, Nestlé's friendly online shopping assistant chatbot. You provide helpful, accurate information about Nestlé products, services, and company matters with excellent customer service. "
                   "Keep your responses short, clear, and to the point. Always maintain a warm, professional tone. "
                   "IMPORTANT GUIDELINES: "
                   "- ONLY discuss Nestlé products, brands, services, and company-related topics "
                   "- DO NOT mention, recommend, or discuss any competitor brands or non-Nestlé products "
                   "- If asked about non-Nestlé topics, politely redirect to Nestlé-related matters "
                   "- Base your answers ONLY on the provided context about Nestlé "
                   "- Use conversation history to provide contextual responses (e.g., 'it' refers to previously mentioned items) "
                   "- After your answer, list the Source URLs you used under 'Sources:' "
                   "- If the context is insufficient for Nestlé-related questions, say so politely"),
        ("human", f"Question: {question}\n\nContext:\n{context_str}{history_str}\n\nAnswer with Citations:"),
    ])
    
    try:
        # Use regular LLM invocation instead of structured output for better compatibility
        messages = prompt_template.format_messages(question=question, context_str=context_str, history_str=history_str)
        response = await llm.ainvoke(messages)
        answer_text = response.content
        
        # Parse citations from the response
        lines = answer_text.splitlines()
        answer_part = []
        cited_sources_list = []
        parsing_sources = False
        
        for line in lines:
            if "cited sources:" in line.lower() or "sources:" in line.lower():
                parsing_sources = True
                continue
            if parsing_sources:
                # Look for URLs in the line
                if line.strip() and ("http" in line.lower() or line.strip().startswith("-") or line.strip().startswith("*")):
                    # Extract URL from line (remove bullet points, etc.)
                    clean_line = line.strip().lstrip("- *").strip()
                    if clean_line:
                        cited_sources_list.append(fix_citation_url(clean_line))
            else:
                answer_part.append(line)
        
        final_answer = "\n".join(answer_part).strip()
        
        # If no sources were found in the text, try to extract unique sources from context
        if not cited_sources_list:
            cited_sources_list = [fix_citation_url(item['source_url']) for item in context if item['source_url'] != "Unknown source"]

        print(f"Generated Answer: {final_answer}")
        print(f"Cited Sources: {cited_sources_list}")
        return {"answer": final_answer, "cited_sources": cited_sources_list, "error": state.get("error")}
        
    except Exception as e:
        import traceback
        print(f"Error generating answer: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        return {"answer": "Sorry, I encountered an error while generating the answer.", "cited_sources": [], "error": f"LLM generation failed: {e}"}


# --- Build the Graph ---
workflow = StateGraph(GraphRAGState)

workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("generate_answer", generate_answer)

workflow.set_entry_point("retrieve_context")
workflow.add_edge("retrieve_context", "generate_answer")
workflow.add_edge("generate_answer", END)

app = workflow.compile()

# --- Function to run the agent ---
async def run_agent(question: str, conversation_history: List[dict] = None):
    if conversation_history is None:
        conversation_history = []
    
    inputs = {
        "question": question, 
        "conversation_history": conversation_history
    }
    async for output_event in app.astream(inputs):
        for key, value in output_event.items():
            print(f"--- Event from node: {key} ---")
            # print(value) # Full state or output of the node
    # Get the final state
    final_state = await app.ainvoke(inputs)
    return final_state


async def main_chat():
    print("GraphRAG Agent is ready. Ask a question about Nestle (or type 'exit').")
    conversation_history = []
    
    while True:
        user_question = input("You: ")
        if user_question.lower() == 'exit':
            break
        if not user_question.strip():
            continue

        # Add user message to history before calling agent
        conversation_history.append({
            "role": "user",
            "content": user_question,
            "timestamp": datetime.now().isoformat()
        })

        final_state = await run_agent(user_question, conversation_history)
        
        # Add assistant response to history
        conversation_history.append({
            "role": "assistant", 
            "content": final_state['answer'],
            "timestamp": datetime.now().isoformat()
        })
        
        print("\n--- Final Answer ---")
        print(f"Q: {final_state['question']}")
        print(f"A: {final_state['answer']}")
        if final_state.get('cited_sources'):
            print("\nCited Sources:")
            for source in final_state['cited_sources']:
                print(f"- {fix_citation_url(source)}")
        if final_state.get('error') and "No relevant context found" not in final_state['error'] and "LLM generation failed" not in final_state['error']: # Print error if it's not handled in answer
            print(f"\nError during processing: {final_state['error']}")
        print("-" * 30 + "\n")

if __name__ == "__main__":
    # Check if the credentials file exists
    if not os.path.exists(CREDENTIALS_FILE_PATH):
        print(f"ERROR: Credentials file not found at {CREDENTIALS_FILE_PATH}")
        print("Please ensure the GraphRAG-IAM-Admin.json file is in the correct location.")
    else:
        print(f"Using project: {GCP_PROJECT_ID}")
        print(f"Using credentials: {CREDENTIALS_FILE_PATH}")
        asyncio.run(main_chat())
