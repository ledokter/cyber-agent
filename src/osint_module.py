import subprocess, re, os
from datetime import datetime

class OSINTAgent:
    def __init__(self, llm):
        self.llm = llm
        os.makedirs(os.path.expanduser("~/.cache/osint"), exist_ok=True)
    
    def domain(self, domain):
        data = {"domain": domain, "subs": set(), "emails": set()}
        try:
            r = subprocess.run(f"subfinder -d {domain} -silent", shell=True, capture_output=True, text=True, timeout=60)
            data["subs"] = set(r.stdout.strip().split('\n'))
        except:
            pass
        data["subs"] = list(data["subs"])
        data["analysis"] = self.llm.invoke(f"Analyse OSINT {domain}: {len(data['subs'])} subs").content
        return data
