#!/usr/bin/env python3
import time
import os
import sys
import json
import subprocess
from datetime import datetime

# Import agent core logic for testing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from cyber_agent_complete import SecurityAgent, Colors
except ImportError:
    print("[-] Error: Could not import SecurityAgent. Run from the project root.")
    sys.exit(1)

def run_benchmark():
    print(f"{Colors.CYAN}╔════════════════════════════════════════════════════════╗{C.END if 'C' in globals() else Colors.END}")
    print(f"{Colors.CYAN}║           CYBER-AGENT HARDWARE BENCHMARK               ║{C.END if 'C' in globals() else Colors.END}")
    print(f"{Colors.CYAN}╚════════════════════════════════════════════════════════╝{C.END if 'C' in globals() else Colors.END}\n")

    # 1. System Info
    print(f"{Colors.YELLOW}[*] Étape 1: Caractéristiques Système{Colors.END}")
    try:
        cpu = subprocess.check_output("grep -m1 'model name' /proc/cpuinfo | cut -d':' -f2", shell=True).decode().strip()
        ram = subprocess.check_output("free -h | awk '/^Mem:/{print $2}'", shell=True).decode().strip()
        print(f"    CPU: {cpu}")
        print(f"    RAM: {ram}")
    except:
        print("    Impossible de récupérer les infos système.")

    # 2. LLM Performance
    print(f"\n{Colors.YELLOW}[*] Étape 2: Performance LLM (Inférence){Colors.END}")
    try:
        agent = SecurityAgent()
        prompt = "Explique brièvement ce qu'est un buffer overflow en 3 phrases."
        
        start_time = time.time()
        response = agent.chat(prompt)
        duration = time.time() - start_time
        
        # Approximate tokens (4 chars per token)
        token_count = len(response) / 4
        tps = token_count / duration
        
        print(f"    Temps de réponse: {duration:.2f}s")
        print(f"    Vitesse approx: {tps:.2f} tokens/sec")
        
        if tps > 15:
            print(f"    {Colors.GREEN}[✓] EXCELLENT: Inférence fluide.{Colors.END}")
        elif tps > 5:
            print(f"    {Colors.GREEN}[✓] CORRECT: Utilisable pour du texte.{Colors.END}")
        else:
            print(f"    {Colors.RED}[!] LENT: Votre CPU risque de peiner sur des analyses longues.{Colors.END}")
            
    except Exception as e:
        print(f"    {Colors.RED}[✗] Erreur LLM: {e}{Colors.END}")

    # 3. RAG Performance
    print(f"\n{Colors.YELLOW}[*] Étape 3: Performance RAG (Recherche Vectorielle){Colors.END}")
    if agent.rag:
        try:
            query = "pivoting techniques"
            start_time = time.time()
            res = agent.rag.query(query)
            duration = time.time() - start_time
            
            print(f"    Temps de recherche: {duration:.2f}s")
            if duration < 0.5:
                print(f"    {Colors.GREEN}[✓] RAPIDE: Accès base instantané.{Colors.END}")
            else:
                print(f"    {Colors.YELLOW}[!] MOYEN: La recherche vectorielle est un peu lente.{Colors.END}")
        except Exception as e:
            print(f"    {Colors.RED}[✗] Erreur RAG: {e}{Colors.END}")
    else:
        print("    [!] RAG non disponible pour le test.")

    print(f"\n{Colors.CYAN}=== VERDICT ==={Colors.END}")
    if tps > 8:
        print("Votre ordinateur est PARFAIT pour Cyber-Agent.")
    elif tps > 3:
        print("Votre ordinateur peut faire tourner l'agent, mais prévoyez un peu d'attente sur les rapports OSINT.")
    else:
        print("Configuration limite. Utilisez un modèle plus léger comme 'llama3.1:8b'.")

if __name__ == "__main__":
    run_benchmark()
