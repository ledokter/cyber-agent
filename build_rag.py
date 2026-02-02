#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_pentest import PentestRAG

def build():
    print("[*] Initializing RAG builder...")
    
    # Initialize RAG (will create/load DB)
    try:
        rag = PentestRAG()
    except Exception as e:
        print(f"[!] Error initializing RAG: {e}")
        print("Did you install dependencies? ./venv/bin/pip install langchain chromadb sentence-transformers langchain-community pypdf")
        sys.exit(1)
    
    base_kb = os.path.expanduser("~/cyber-agent/knowledge_base")
    
    if not os.path.exists(base_kb):
        print(f"[!] Knowledge base directory not found: {base_kb}")
        sys.exit(1)

    # Dictionary of directory -> priority/description
    # We process them in order using a list
    targets = [
        "02-owasp-cheatsheets", 
        "03-payloads",
        "08-anssi-guides",
        "04-hacktricks",
        "01-mitre-attack", 
        # "09-exploitdb" # Skipped by default due to size/relevance, can be added if needed
    ]
    
    print(f"[*] Starting ingestion from: {base_kb}")
    
    for target in targets:
        path = os.path.join(base_kb, target)
        if os.path.exists(path):
            print(f"\n[+] Processing module: {target}")
            print(f"    Path: {path}")
            
            # Simple check to avoid crashing on empty or massive folders
            # rag.ingest_documents handles MD, PDF, TXT
            try:
                rag.ingest_documents(path)
            except Exception as e:
                print(f"[!] Error processing {target}: {e}")
        else:
            print(f"[-] Module not found: {target} (skipping)")

    print("\n[+] RAG Build Complete!")
    print(f"    Database location: {rag.persist_dir}")
    print(f"    Number of sources: {len(rag.list_sources())}")

if __name__ == "__main__":
    build()
