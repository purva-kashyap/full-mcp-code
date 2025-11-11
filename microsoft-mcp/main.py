#!/usr/bin/env python3
"""
Microsoft MCP Server
Main entry point to start the server
"""
import os
import sys

# Add src directory to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import and run the server
from src.microsoft_mcp.server import run_server

if __name__ == "__main__":
    run_server()
