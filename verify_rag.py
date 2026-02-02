#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from rag_pentest import PentestRAG
    
    print("[*] Testing RAG Database...")
    rag = PentestRAG()
    
    sources = rag.list_sources()
    print(f"[+] Found {len(sources)} sources")
    if len(sources) > 0:
        print(f"    First 5 sources: {sources[:5]}")
        
    query = "pivoting windows"
    print(f"\n[*] Querying: '{query}'")
    result = rag.query(query)
    
    if "error" in result:
        print(f"[-] Error: {result['error']}")
    else:
        print(f"[+] Context length: {len(result['context'])}")
        print(f"[+] Sources found: {len(result['sources'])}")
        for src in result['sources']:
            print(f"    - {src['source']} (score: {src['score']:.2f})")
            
except Exception as e:
    print(f"[-] Failure: {e}")
