#!/usr/bin/env python3
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from agent_core import SecurityAgent
from osint_module import OSINTAgent

class C:
    CYAN, GRN, YEL, RED, MAG = '\033[96m','\033[92m','\033[93m','\033[91m','\033[95m'
    END = '\033[0m'

class Shell:
    def __init__(self):
        with open(os.path.expanduser("~/.config/cyber-agent/config.json")) as f:
            cfg = json.load(f)
        self.agent = SecurityAgent(cfg["model"], cfg.get("device_type","generic"))
        self.osint = OSINTAgent(self.agent.llm)
    
    def banner(self):
        print(f"{C.CYAN}╔════════════════════════════════╗{C.END}")
        print(f"{C.CYAN}║    CYBER-AGENT v2.1           ║{C.END}")
        print(f"{C.CYAN}╚════════════════════════════════╝{C.END}")
    
    def run(self):
        self.banner()
        while True:
            try:
                inp = input(f"\n{C.MAG}[Agent]{C.END} > ").strip().split()
                if not inp:
                    continue
                cmd = inp[0]
                args = inp[1:]
                
                if cmd in ["quit","exit"]:
                    break
                elif cmd == "recon" and args:
                    r = self.agent.recon(args[0])
                    print(r.get("analysis","No analysis"))
                elif cmd == "logs" and args:
                    print(self.agent.logs(args[0]))
                elif cmd == "chat":
                    print(f"{C.CYAN}AI>{C.END} {self.agent.chat(' '.join(args))}")
                elif cmd == "osint" and len(args)>1:
                    r = self.osint.domain(args[1])
                    print(f"{C.GRN}[+]{C.END} {len(r['subs'])} subdomains")
                    print(r['analysis'])
                else:
                    print("Commandes: recon, logs, osint, chat, quit")
            except KeyboardInterrupt:
                print(f"\n{C.YEL}Ctrl+C{C.END}")
            except Exception as e:
                print(f"{C.RED}Error: {e}{C.END}")

if __name__ == "__main__":
    Shell().run()
