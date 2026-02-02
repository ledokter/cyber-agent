#!/usr/bin/env python3
import json, subprocess, os, sys
from datetime import datetime
try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage
except:
    print("[-] pip install langchain langchain-ollama")
    sys.exit(1)

class SecurityAgent:
    def __init__(self, model="qwen2.5:14b", device="generic"):
        self.device = device
        threads = 6 if device == "thinkpad20kh" else 4
        self.llm = ChatOllama(
            model=model, 
            base_url="http://localhost:11434",
            temperature=0.1, 
            num_ctx=32768, 
            num_thread=threads
        )
        print(f"[+] Agent pret ({device}, {threads} threads)")
    
    def safe_run(self, cmd, timeout=300):
        bad = ['rm -rf /', ':(){ :|:& };:', '> /dev/sda']
        for b in bad:
            if b in cmd:
                return {"error": "Dangerous command blocked"}
        safe = f"firejail --net=none --private-tmp {cmd}"
        try:
            r = subprocess.run(safe, shell=True, capture_output=True, text=True, timeout=timeout)
            return {"stdout": r.stdout, "stderr": r.stderr, "code": r.returncode}
        except:
            return {"error": "Execution failed"}
    
    def recon(self, target, intensity="normal"):
        if intensity == "stealth":
            c = f"nmap -sS -T2 -p- --open {target}"
        elif intensity == "aggressive":
            c = f"nmap -sC -sV -O -A -T4 {target}"
        else:
            c = f"nmap -sV -sC --top-ports 1000 {target}"
        res = self.safe_run(c, 600)
        if res.get("code") == 0:
            analysis = self.llm.invoke(f"Analyse nmap en FRANCAIS:\n{res['stdout'][:3000]}")
            res["analysis"] = analysis.content
        return res
    
    def logs(self, path):
        if not os.path.exists(path):
            return "Fichier introuvable"
        with open(path, errors='ignore') as f:
            lines = f.readlines()[:500]
        return self.llm.invoke(f"Analyse logs:\n{''.join(lines)[:4000]}").content
    
    def chat(self, msg):
        return self.llm.invoke(msg).content
