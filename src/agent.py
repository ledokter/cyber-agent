#!/usr/bin/env python3
import json, subprocess, os, sys
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

class Agent:
    def __init__(self):
        config_path = os.path.expanduser("~/.config/cyber-agent/config.json")
        with open(config_path) as f:
            self.cfg = json.load(f)
        
        threads = 6 if self.cfg.get("device_type") == "thinkpad20kh" else 4
        self.llm = ChatOllama(
            model=self.cfg["model"],
            base_url="http://localhost:11434",
            temperature=0.1,
            num_ctx=32768,
            num_thread=threads
        )
        print(f"[+] Agent prêt ({self.cfg['device_type']})")
    
    def safe_run(self, cmd, timeout=300):
        bad = ['rm -rf /', ':(){ :|:& };:', '> /dev/sda']
        for b in bad:
            if b in cmd:
                return {"error": "Dangerous"}
        safe = f"firejail --net=none --private-tmp {cmd}"
        r = subprocess.run(safe, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout, "stderr": r.stderr, "code": r.returncode}
    
    def recon(self, target):
        cmd = f"nmap -sV -sC --top-ports 1000 {target}"
        res = self.safe_run(cmd, 600)
        if res["code"] == 0:
            analysis = self.llm.invoke(f"Analyse ce scan nmap en Français:\n{res['stdout'][:3000]}")
            print(f"\n=== ANALYSIS ===\n{analysis.content}\n===============")
        return res
    
    def logs(self, path):
        if not os.path.exists(path):
            return "Fichier introuvable"
        with open(path, errors='ignore') as f:
            content = f.read()[:4000]
        return self.llm.invoke(f"Analyse forensics:\n{content}").content
    
    def osint_domain(self, domain):
        print(f"[*] OSINT {domain}...")
        try:
            r = subprocess.run(f"subfinder -d {domain} -silent", shell=True, capture_output=True, text=True, timeout=60)
            subs = r.stdout.strip().split('\n')[:20]
            print(f"[+] {len(subs)} subdomains found")
            if subs:
                analysis = self.llm.invoke(f"Analyse risques pour {domain}: sous-domaines {subs}. Quels sont les plus critiques?")
                print(analysis.content)
        except Exception as e:
            print(f"[!] Error: {e}")
    
    def chat(self, msg):
        return self.llm.invoke(msg).content
    
    def run(self):
        print("Commandes: recon <target>, logs <file>, osint <domain>, chat <msg>, quit")
        while True:
            try:
                inp = input("\n[Agent]> ").strip().split()
                if not inp:
                    continue
                cmd = inp[0]
                args = inp[1:]
                
                if cmd == "quit":
                    break
                elif cmd == "recon" and args:
                    self.recon(args[0])
                elif cmd == "logs" and args:
                    print(self.logs(args[0]))
                elif cmd == "osint" and args:
                    self.osint_domain(args[0])
                elif cmd == "chat":
                    print(self.chat(" ".join(args)))
                else:
                    print("Commandes: recon, logs, osint, chat, quit")
            except KeyboardInterrupt:
                print("\n[!] Ctrl+C")
            except Exception as e:
                print(f"[!] Error: {e}")

if __name__ == "__main__":
    Agent().run()
