#!/usr/bin/env python3
"""
Startup script for the GraphRAG FastAPI server
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_requirements():
    """Check if all required environment variables and files are present"""
    required_env_vars = [
        "GCP_PROJECT_ID",
        "SPANNER_INSTANCE_ID", 
        "SPANNER_DATABASE_ID",
        "GOOGLE_APPLICATION_CREDENTIALS_PATH"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with these variables.")
        return False
    
    # Check credentials file
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH")
    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found: {creds_path}")
        return False
    
    print("✅ All requirements check passed!")
    return True

def main():
    """Main function to start the server"""
    print("🚀 Starting GraphRAG FastAPI Server...")
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"📍 Server will run on: http://{host}:{port}")
    print(f"🔄 Reload mode: {'enabled' if reload else 'disabled'}")
    print(f"📝 Log level: {log_level}")
    print("📖 API documentation: http://localhost:8000/docs")
    print("🔧 Interactive API: http://localhost:8000/redoc")
    print("\n" + "="*50)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    main() 