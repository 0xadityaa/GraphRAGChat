import os
import glob
import asyncio
from urllib.parse import urlunparse, urlparse
from langchain_google_spanner import SpannerGraphStore
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_text_splitters import MarkdownTextSplitter
from dotenv import load_dotenv
from google.oauth2 import service_account
from langchain_core.documents import Document
from langchain_community.graphs.graph_document import Node, GraphDocument

load_dotenv() # Load environment variables from .env file

# --- Configuration ---
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
SPANNER_INSTANCE_ID = os.getenv("SPANNER_INSTANCE_ID")
SPANNER_DATABASE_ID = os.getenv("SPANNER_DATABASE_ID")
CREDENTIALS_FILE_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH") 
EMBEDDING_MODEL_NAME = "text-embedding-004" # Or "text-embedding-005" / "gemini-embedding-001"

# Base URL for reconstructing source URLs from filenames
BASE_NESTLE_URL_SCHEME = "https"
BASE_NESTLE_URL_NETLOC = "www.madewithnestle.ca"

# Construct the absolute path to the data directory
# Assuming ingest_data.py is in backend/ and data/content/ is in the project root (sibling to backend/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # This goes one level up from backend/ to GraphRAG-Chatbot/
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "content")

print(f"Calculated DATA_DIR: {DATA_DIR}") # For debugging

def construct_source_url(filename):
    base_name = os.path.basename(filename)
    if base_name == "_.md": # Handle root path
        path_segment = "/"
    else:
        # Remove leading underscore and .md extension
        path_segment = base_name[1:-3] if base_name.startswith("_") and base_name.endswith(".md") else base_name[:-3]
        path_segment = "/" + path_segment # Ensure leading slash for path

    # A simple reconstruction, might need adjustment if there are complex paths
    return urlunparse((BASE_NESTLE_URL_SCHEME, BASE_NESTLE_URL_NETLOC, path_segment, "", "", ""))

async def main():
    print("Initializing SpannerGraphStore...")
    
    credentials = None
    if CREDENTIALS_FILE_PATH:
        try:
            credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE_PATH)
            print(f"Successfully loaded credentials from {CREDENTIALS_FILE_PATH}")
            # Ensure GCP_PROJECT_ID is set if credentials are to be used explicitly
            if not GCP_PROJECT_ID:
                print("Warning: CREDENTIALS_FILE_PATH is set, but GCP_PROJECT_ID is not. Project may not be inferred correctly.")
        except Exception as e:
            print(f"Error loading credentials from {CREDENTIALS_FILE_PATH}: {e}")
            print("Proceeding without explicit credentials, relying on application default credentials if available.")

    graph_store_params = {
        "instance_id": SPANNER_INSTANCE_ID,
        "database_id": SPANNER_DATABASE_ID,
        "graph_name": "nestle_knowledge_graph_main",
    }
    if credentials:
        graph_store_params["credentials"] = credentials
        if GCP_PROJECT_ID: # Pass project ID when explicit credentials are used
            graph_store_params["project"] = GCP_PROJECT_ID 
    
    # The SpannerGraphStore might instantiate its own spanner.Client()
    # We need to ensure that client knows the project.
    # One way is to set the GOOGLE_CLOUD_PROJECT env var before this call if not already effectively set.
    # python-dotenv should handle this if GOOGLE_CLOUD_PROJECT is in .env
    original_google_cloud_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    sanitized_gcp_project_id_for_env = None
    if not original_google_cloud_project and GCP_PROJECT_ID:
        print(f"Temporarily setting GOOGLE_CLOUD_PROJECT to {GCP_PROJECT_ID} for Spanner client initialization.")
        os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT_ID
        sanitized_gcp_project_id_for_env = GCP_PROJECT_ID

    try:
        graph_store = SpannerGraphStore(**graph_store_params)
    except TypeError as e:
        print(f"Initial SpannerGraphStore init failed: {e}")
        # Fallback for project vs project_id
        if "project" in graph_store_params and "project=" not in str(e).lower() and "project_id=" in str(e).lower() and GCP_PROJECT_ID:
            print("Retrying SpannerGraphStore with project_id instead of project.")
            graph_store_params.pop("project", None)
            graph_store_params["project_id"] = GCP_PROJECT_ID
            graph_store = SpannerGraphStore(**graph_store_params)
        elif "project_id" in graph_store_params and "project_id=" not in str(e).lower() and "project=" in str(e).lower() and GCP_PROJECT_ID:
            print("Retrying SpannerGraphStore with project instead of project_id.")
            graph_store_params.pop("project_id", None)
            graph_store_params["project"] = GCP_PROJECT_ID
            graph_store = SpannerGraphStore(**graph_store_params)
        else:
            print("SpannerGraphStore fallback attempts failed.")
            raise e
    finally:
        # Clean up temporarily set environment variable if we set it
        if sanitized_gcp_project_id_for_env:
            if original_google_cloud_project:
                os.environ["GOOGLE_CLOUD_PROJECT"] = original_google_cloud_project
            else:
                del os.environ["GOOGLE_CLOUD_PROJECT"]
            print("Restored original GOOGLE_CLOUD_PROJECT environment variable.")

    print(f"Initializing VertexAIEmbeddings with model: {EMBEDDING_MODEL_NAME}...")
    embeddings = VertexAIEmbeddings(model_name=EMBEDDING_MODEL_NAME, project=GCP_PROJECT_ID, credentials=credentials)

    print(f"Looking for markdown files in {DATA_DIR}...")
    md_files = glob.glob(os.path.join(DATA_DIR, "*.md"))

    if not md_files:
        print(f"No markdown files found in {DATA_DIR}. Exiting.")
        return

    print(f"Found {len(md_files)} markdown files.")

    text_splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100) # Adjust as needed

    graph_documents_to_add = []

    for md_file_path in md_files:
        source_url = construct_source_url(md_file_path)
        print(f"\nProcessing {md_file_path} (Source URL: {source_url})...")
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {md_file_path}: {e}")
            continue

        if not content.strip():
            print(f"Skipping empty file: {md_file_path}")
            continue

        chunks = text_splitter.split_text(content)
        print(f"Split into {len(chunks)} chunks.")

        doc_nodes = []
        for i, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                print(f"Skipping empty chunk from {md_file_path}")
                continue
            
            # It's more efficient to embed in batches, but SpannerGraphStore.add_node
            # typically takes one node at a time. Let's prepare node data.
            # The actual embedding generation will happen when adding the node if not pre-computed.
            # However, SpannerGraphVectorContextRetriever expects embeddings to be *in* the nodes.
            
            # Let's embed here and store it.
            try:
                chunk_embedding = await embeddings.aembed_query(chunk_text) # Use async version
                node_id = f"{source_url}#chunk{i}" # Create a unique node ID
                node_properties = {
                    "text": chunk_text,
                    "source_url": source_url,
                    "embedding": chunk_embedding, # Store the embedding directly
                    "doc_id": source_url # Group chunks by original document
                }
                # Create Node object for graph ingestion
                lc_node = Node(id=node_id, type="DocumentChunk", properties=node_properties)
                doc_nodes.append(lc_node)
                print(f"  Prepared node {node_id} for {source_url}")

            except Exception as e:
                print(f"Error embedding chunk {i} from {md_file_path}: {e}")
        
        if doc_nodes:
            # For add_graph_documents, it expects a list of GraphDocument.
            # A GraphDocument is composed of nodes and source document.
            # The source Document itself has page_content and metadata.
            # Let's adapt to this structure.
            # We'll make one GraphDocument per original markdown file.
            # The `page_content` of the source Document for GraphDocument might not be strictly necessary
            # if all data is in the nodes, but it's good to include the source URL.
            # Create a LangChain Document to represent the source file
            source_doc_for_graph = Document(page_content=content, metadata={"source": source_url})
            # Wrap nodes and relationships into a GraphDocument
            graph_doc = GraphDocument(nodes=doc_nodes, relationships=[], source=source_doc_for_graph)
            graph_documents_to_add.append(graph_doc)

    if graph_documents_to_add:
        print(f"\nAdding {len(graph_documents_to_add)} GraphDocuments (containing {sum(len(gd.nodes) for gd in graph_documents_to_add)} total nodes) to SpannerGraphStore...")
        try:
            graph_store.add_graph_documents(graph_documents_to_add)
            print("All GraphDocuments processed and attempted to add to Spanner.")
        except Exception as e:
            print(f"Error adding GraphDocuments to Spanner: {e}")
    else:
        print("No GraphDocuments were prepared to be added.")

    print("\nData ingestion process complete.")

if __name__ == "__main__":
    # For running asyncio code
    # Python 3.7+
    asyncio.run(main())
