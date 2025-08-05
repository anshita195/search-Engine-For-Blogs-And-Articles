#!/usr/bin/env python3
"""
Deploy Personal Blog Search Engine
Simple deployment script to run all components
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import json

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('sentence-transformers', 'sentence_transformers'),
        ('beautifulsoup4', 'bs4'),
        ('requests', 'requests'),
        ('scikit-learn', 'sklearn')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - missing")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_models():
    """Check if required models are available."""
    print("\n🔍 Checking models...")
    
    # Check if embeddings exist
    embeddings_file = Path("models/prototype_embeddings.pkl")
    if embeddings_file.exists():
        print("✅ Prototype embeddings")
    else:
        print("❌ Prototype embeddings - missing")
        print("Run: python classifier/embedding_classifier.py")
        return False
    
    # Check if search index exists
    search_index_file = Path("data/search_index.json")
    if search_index_file.exists():
        with open(search_index_file, 'r') as f:
            index_data = json.load(f)
        print(f"✅ Search index ({len(index_data)} documents)")
    else:
        print("❌ Search index - missing")
        print("Run: python scripts/create_search_index.py")
        return False
    
    return True

def start_api():
    """Start the FastAPI server."""
    print("\n🚀 Starting Personal Blog Search Engine API...")
    
    try:
        # Start the API server
        process = subprocess.Popen([
            sys.executable, "api/main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        import requests
        try:
            response = requests.get("http://localhost:8001/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server started successfully")
                print("🌐 API URL: http://localhost:8001")
                print("📊 Health check: http://localhost:8001/api/health")
                return process
            else:
                print("❌ API server failed to start")
                return None
        except requests.exceptions.RequestException:
            print("❌ API server failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start API: {e}")
        return None

def open_web_interface():
    """Open the web interface in browser."""
    print("\n🌐 Opening web interface...")
    
    ui_file = Path("ui/index.html")
    if ui_file.exists():
        # Open the HTML file in browser
        webbrowser.open(f"file://{ui_file.absolute()}")
        print("✅ Web interface opened in browser")
        print("💡 Tip: Use the search box to find personal blogs!")
    else:
        print("❌ Web interface file not found")

def main():
    """Main deployment function."""
    print("🚀 Personal Blog Search Engine - Deployment")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependencies check failed. Please install missing packages.")
        return
    
    # Check models
    if not check_models():
        print("\n❌ Models check failed. Please run the required scripts.")
        return
    
    # Start API
    api_process = start_api()
    if not api_process:
        print("\n❌ Failed to start API server.")
        return
    
    # Open web interface
    open_web_interface()
    
    print("\n🎉 Personal Blog Search Engine is running!")
    print("=" * 50)
    print("📊 API: http://localhost:8001")
    print("🔍 Web UI: ui/index.html")
    print("📋 Health: http://localhost:8001/api/health")
    print("🔍 Search: http://localhost:8001/api/search?q=your_query")
    print("\n💡 Press Ctrl+C to stop the server")
    
    try:
        # Keep the server running
        api_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        api_process.terminate()
        print("✅ Server stopped")

if __name__ == "__main__":
    main() 