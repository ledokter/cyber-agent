#!/usr/bin/env python3
"""
Cyber-Agent Complete v2.2 - AVEC RAG PENTEST
Agent de cybersécurité 100% offline - Ollama + BlackArch + RAG
Tout-en-un : OSINT, Pentest, Forensics, Hardening, Knowledge Base
"""

import json
import subprocess
import os
import sys
import re
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Imports LangChain
try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    print("[-] Erreur: langchain non installé")
    print("[-] Exécutez: pip install langchain langchain-ollama")
    sys.exit(1)

# Imports RAG (optionnels)
try:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
    from langchain_core.documents import Document
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print(f"[!] Module RAG non installé. Pour l'activer:")
    print(f"    pip install chromadb sentence-transformers langchain-community pypdf")

# Couleurs terminal
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    END = '\033[0m'

@dataclass
class MissionContext:
    target: str
    mission_type: str
    start_time: datetime = field(default_factory=datetime.now)
    findings: List[Dict] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)

# ============================================================================
# MODULE RAG PENTEST
# ============================================================================
class PentestRAG:
    def __init__(self, persist_dir: str = "~/cyber-agent/knowledge_db"):
        if not RAG_AVAILABLE:
            raise ImportError("Modules RAG non installés")
        
        self.persist_dir = os.path.expanduser(persist_dir)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            cache_folder=os.path.expanduser("~/.cache/sentence_transformers")
        )
        self.db = None
        self._init_db()
    
    def _init_db(self):
        """Initialise ou charge la base vectorielle"""
        if os.path.exists(self.persist_dir) and os.listdir(self.persist_dir):
            print(f"{Colors.GREEN}[RAG]{Colors.END} Chargement base: {self.persist_dir}")
            self.db = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings
            )
        else:
            print(f"{Colors.YELLOW}[RAG]{Colors.END} Nouvelle base à créer: {self.persist_dir}")
            os.makedirs(self.persist_dir, exist_ok=True)
            self.db = None
    
    def ingest_documents(self, docs_path: str):
        """Ingestion de documents pentest"""
        print(f"{Colors.CYAN}[RAG]{Colors.END} Ingestion de: {docs_path}")
        
        docs_path = os.path.expanduser(docs_path)
        documents = []
        
        if os.path.isdir(docs_path):
            # Markdown et textes
            try:
                loader = DirectoryLoader(docs_path, glob="**/*.md", loader_cls=TextLoader, silent=True)
                documents.extend(loader.load())
            except: pass
            
            try:
                loader = DirectoryLoader(docs_path, glob="**/*.txt", loader_cls=TextLoader, silent=True)
                documents.extend(loader.load())
            except: pass
            
            # PDFs
            try:
                pdf_loader = DirectoryLoader(docs_path, glob="**/*.pdf", loader_cls=PyPDFLoader, silent=True)
                documents.extend(pdf_loader.load())
            except: pass
                
        elif docs_path.endswith('.pdf'):
            loader = PyPDFLoader(docs_path)
            documents = loader.load()
        else:
            loader = TextLoader(docs_path)
            documents = loader.load()
        
        if not documents:
            print(f"{Colors.RED}[RAG]{Colors.END} Aucun document trouvé")
            return False
        
        print(f"{Colors.GREEN}[RAG]{Colors.END} {len(documents)} documents chargés")
        
        # Split en chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        print(f"{Colors.GREEN}[RAG]{Colors.END} {len(chunks)} chunks créés")
        
        # Création/Update base
        if self.db is None:
            self.db = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_dir
            )
        else:
            self.db.add_documents(chunks)
        
        self.db.persist()
        print(f"{Colors.GREEN}[RAG]{Colors.END} {len(chunks)} chunks indexés et sauvegardés")
        return True
    
    def query(self, question: str, k: int = 4) -> Dict:
        """Recherche dans la base de connaissances"""
        if self.db is None:
            return {"error": "Base vide. Utilisez 'learn <dossier>' pour ajouter des documents."}
        
        print(f"{Colors.BLUE}[RAG]{Colors.END} Recherche: {question[:50]}...")
        
        docs = self.db.similarity_search_with_score(question, k=k)
        
        context = "\n\n".join([f"[Source {i+1}] {doc.page_content}" 
                              for i, (doc, score) in enumerate(docs)])
        
        sources = [{
            "content": doc.page_content[:200] + "...",
            "score": float(score),
            "source": doc.metadata.get('source', 'inconnu')
        } for doc, score in docs]
        
        return {
            "context": context,
            "sources": sources,
            "query": question
        }

    def list_sources(self):
        """Liste les sources dans la base"""
        if self.db is None:
            return []
        data = self.db.get()
        sources = set()
        for meta in data.get('metadatas', []):
            if meta and 'source' in meta:
                sources.add(meta['source'])
        return list(sources)

# ============================================================================
# SECURITY AGENT
# ============================================================================
class SecurityAgent:
    def __init__(self, model_name: str = "qwen2.5:14b", device_type: str = "generic"):
        self.device_type = device_type
        self.model_name = model_name
        
        # Optimisation selon hardware
        num_threads = 6 if device_type == "thinkpad20kh" else 4
        
        self.llm = ChatOllama(
            model=model_name,
            base_url="http://localhost:11434",
            temperature=0.3, # Augmenté légèrement pour plus de fluidité
            num_ctx=32768,
            num_thread=num_threads,
            keep_alive="30m"
        )
        
        self.system_prompt = "Tu es Cyber-Agent v2.2, un assistant spécialisé en cybersécurité. Tu réponds TOUJOURS en FRANÇAIS. Tu es concis, technique et utile."
        
        self.missions: List[MissionContext] = []
        self.current_mission: Optional[MissionContext] = None
        
        # Initialisation RAG
        self.rag = None
        if RAG_AVAILABLE:
            try:
                self.rag = PentestRAG()
                print(f"{Colors.GREEN}[+]{Colors.END} Module RAG prêt")
            except Exception as e:
                print(f"{Colors.YELLOW}[!]{Colors.END} RAG erreur: {e}")
        else:
            print(f"{Colors.YELLOW}[!]{Colors.END} RAG désactivé (pip install chromadb sentence-transformers)")
        
        print(f"{Colors.GREEN}[+]{Colors.END} Agent prêt ({device_type}, {num_threads} threads)")

    def safe_execute(self, command: str, timeout: int = 300, sandbox: bool = True) -> Dict:
        """Exécute une commande système avec sécurité"""
        dangerous = ['rm -rf /', ':(){ :|:& };:', '> /dev/sda', 'mkfs.', 'dd if=/dev/zero']
        for d in dangerous:
            if d in command:
                return {"error": "Commande dangereuse bloquée par sécurité", "command": command}
        
        if sandbox and not command.startswith("firejail"):
            cmd_exec = f"firejail --net=none --private-tmp --timeout=00:05:00 {command}"
        else:
            cmd_exec = command
        
        try:
            result = subprocess.run(
                cmd_exec, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": cmd_exec
            }
        except subprocess.TimeoutExpired:
            return {"error": "Timeout - commande trop longue", "command": command}
        except Exception as e:
            return {"error": str(e), "command": command}

    # =========================================================================
    # RAG METHODS
    # =========================================================================
    def rag_query(self, question: str) -> str:
        """Questionnement avec contexte RAG"""
        if not self.rag:
            return f"{Colors.RED}[!]{Colors.END} RAG non initialisé. Installez: pip install chromadb sentence-transformers langchain-community"
        
        rag_result = self.rag.query(question)
        if "error" in rag_result:
            return f"{Colors.RED}[!]{Colors.END} {rag_result['error']}"
        
        # Prompt enrichi
        prompt = f"""Tu es un expert en cybersécurité offensive. Réponds en utilisant le contexte fourni.

CONTEXTE RAG (Base de connaissances Pentest):
{rag_result['context']}

QUESTION: {question}

Instructions:
1. Réponds précisément en t'appuyant sur le contexte ci-dessus
2. Cite les sources [Source X] si pertinent
3. Propose des commandes/outils concrets
4. Si le contexte ne suffit pas, indique-le"""

        try:
            response = self.llm.invoke(prompt)
            sources = "\n".join([f"  📄 {s['source']}" for s in rag_result['sources'][:2]])
            return f"{response.content}\n\n{Colors.YELLOW}Sources consultées:{Colors.END}\n{sources}"
        except Exception as e:
            return f"{Colors.RED}[!]{Colors.END} Erreur: {e}"

    def ingest_knowledge(self, path: str) -> str:
        """Ajoute des documents à la base RAG"""
        if not self.rag:
            return f"{Colors.RED}[!]{Colors.END} RAG non disponible"
        if not os.path.exists(os.path.expanduser(path)):
            return f"{Colors.RED}[!]{Colors.END} Chemin introuvable: {path}"
        
        try:
            success = self.rag.ingest_documents(path)
            if success:
                return f"{Colors.GREEN}[+]{Colors.END} Documents ingérés avec succès"
            else:
                return f"{Colors.RED}[!]{Colors.END} Échec ingestion"
        except Exception as e:
            return f"{Colors.RED}[!]{Colors.END} Erreur: {e}"

    def list_rag_sources(self) -> str:
        """Liste les sources RAG"""
        if not self.rag:
            return "RAG non disponible"
        sources = self.rag.list_sources()
        if not sources:
            return "Base vide. Utilisez 'learn <dossier>' pour ajouter des documents."
        result = [f"{Colors.GREEN}[+]{Colors.END} {len(sources)} sources indexées:"]
        for s in sources[:15]:  # Limite à 15 pour l'affichage
            result.append(f"  - {os.path.basename(s)}")
        if len(sources) > 15:
            result.append(f"  ... et {len(sources)-15} autres")
        return "\n".join(result)

    # =========================================================================
    # OSINT MODULE
    # =========================================================================
    def osint_domain(self, domain: str, deep: bool = False) -> Dict:
        """Reconnaissance passive complète d'un domaine"""
        print(f"{Colors.CYAN}[*]{Colors.END} OSINT Reconnaissance: {domain}")
        
        data = {
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "subdomains": [],
            "emails": [],
            "ips": [],
            "hosts": [],
            "technologies": []
        }
        
        # 1. Subfinder
        try:
            result = subprocess.run(
                f"subfinder -d {domain} -silent -all", 
                shell=True, capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                data["subdomains"] = list(set(filter(None, result.stdout.strip().split('\n'))))
                print(f"{Colors.GREEN}[+]{Colors.END} {len(data['subdomains'])} sous-domaines trouvés")
        except Exception as e:
            print(f"{Colors.YELLOW}[!]{Colors.END} Subfinder: {e}")
        
        # 2. TheHarvester
        try:
            output_file = f"/tmp/th_{domain.replace('.', '_')}"
            subprocess.run(
                f"theHarvester -d {domain} -b all -f {output_file}",
                shell=True, timeout=120
            )
            xml_file = f"{output_file}.xml"
            if os.path.exists(xml_file):
                with open(xml_file, 'r', errors='ignore') as f:
                    content = f.read()
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                    data["emails"] = list(set(emails))
                    ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', content)
                    data["ips"] = list(set(ips))
                print(f"{Colors.GREEN}[+]{Colors.END} {len(data['emails'])} emails, {len(data['ips'])} IPs")
        except Exception as e:
            print(f"{Colors.YELLOW}[!]{Colors.END} theHarvester: {e}")
        
        # 3. Wayback Machine
        try:
            url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&collapse=urlkey&limit=1000"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                wayback_data = response.json()
                interesting = []
                for entry in wayback_data[1:]:
                    if len(entry) > 2:
                        url_found = entry[2]
                        if any(x in url_found.lower() for x in ['admin', 'api', 'backup', '.sql', '.env', 'config', 'internal']):
                            interesting.append(url_found)
                data["wayback_urls"] = list(set(interesting))[:50]
                print(f"{Colors.GREEN}[+]{Colors.END} {len(data['wayback_urls'])} URLs sensibles dans Wayback")
        except Exception as e:
            print(f"{Colors.YELLOW}[!]{Colors.END} Wayback: {e}")
        
        # Analyse IA
        if data["subdomains"] or data["emails"]:
            analysis_prompt = f"""Analyse OSINT pour {domain}:
- {len(data['subdomains'])} sous-domaines dont: {', '.join(data['subdomains'][:5])}
- {len(data['emails'])} emails collectés
- {len(data.get('wayback_urls', []))} URLs historiques sensibles

Identifie:
1. Le sous-domaine le plus critique (dev/staging/admin ?)
2. Schéma de nommage emails (prenom.nom ?)
3. Fuites potentielles à investiguer
4. Recommandations prioritaires"""

            try:
                analysis = self.llm.invoke(analysis_prompt)
                data["analysis"] = analysis.content
                print(f"\n{Colors.CYAN}=== ANALYSE IA ==={Colors.END}")
                print(analysis.content)
                print(f"{Colors.CYAN}=================={Colors.END}\n")
            except Exception as e:
                print(f"{Colors.RED}[!]{Colors.END} Erreur analyse IA: {e}")
        
        self._save_osint_report(domain, data)
        return data

    def osint_email(self, email: str) -> Dict:
        """Investigation email"""
        print(f"{Colors.CYAN}[*]{Colors.END} Investigation email: {email}")
        
        result = {"email": email, "services": [], "risk": "LOW"}
        
        try:
            cmd = f"holehe {email}"
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            services_found = []
            for line in process.stdout.split('\n'):
                if '[+]' in line:
                    service = line.split('[+]')[1].strip()
                    services_found.append(service)
            
            result["services"] = services_found
            result["risk"] = "HIGH" if len(services_found) > 5 else "MEDIUM" if services_found else "LOW"
            
            print(f"{Colors.GREEN}[+]{Colors.END} Trouvé sur {len(services_found)} services")
            for svc in services_found[:10]:
                print(f"  - {svc}")
                
        except Exception as e:
            print(f"{Colors.YELLOW}[!]{Colors.END} Holehe: {e}")
            result["error"] = str(e)
        
        return result

    def osint_username(self, username: str) -> Dict:
        """Recherche username"""
        print(f"{Colors.CYAN}[*]{Colors.END} Recherche username: {username}")
        
        sites = {
            "github": f"https://github.com/{username}",
            "twitter": f"https://twitter.com/{username}",
            "reddit": f"https://reddit.com/user/{username}",
            "linkedin": f"https://linkedin.com/in/{username}"
        }
        
        found = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        for site, url in sites.items():
            try:
                resp = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
                if resp.status_code == 200:
                    found.append({"platform": site, "url": url, "exists": True})
                    print(f"{Colors.GREEN}[+]{Colors.END} {site}: trouvé")
                else:
                    print(f"{Colors.RED}[-]{Colors.END} {site}: non trouvé")
            except Exception:
                print(f"{Colors.YELLOW}[!]{Colors.END} {site}: timeout")
        
        return {
            "username": username,
            "profiles": found,
            "recommendation": "Vérifier manuellement les profils pour fuites d'informations"
        }

    # =========================================================================
    # PENTEST MODULE
    # =========================================================================
    def run_recon(self, target: str, intensity: str = "normal") -> Dict:
        """Reconnaissance réseau"""
        print(f"{Colors.CYAN}[*]{Colors.END} Scan {intensity} sur {target}")
        
        if intensity == "stealth":
            cmd = f"nmap -sS -T2 -p- --open --max-retries 2 {target}"
            print(f"{Colors.YELLOW}[i]{Colors.END} Mode furtif")
        elif intensity == "aggressive":
            cmd = f"nmap -sC -sV -O -A -T4 {target}"
            print(f"{Colors.RED}[!]{Colors.END} Mode agressif")
        else:
            cmd = f"nmap -sV -sC --top-ports 1000 {target}"
        
        results = {"target": target, "intensity": intensity}
        results["nmap"] = self.safe_execute(cmd, timeout=600)
        
        if results["nmap"]["returncode"] == 0:
            print(f"{Colors.GREEN}[+]{Colors.END} Scan terminé, analyse IA...")
            
            analysis_prompt = f"""Analyse nmap pour {target}:
{results['nmap']['stdout'][:4000]}

Extraits: services, versions, OS, vulnérabilités potentielles, recommandations."""

            try:
                analysis = self.llm.invoke(analysis_prompt)
                results["analysis"] = analysis.content
                print(f"\n{Colors.CYAN}=== ANALYSE ==={Colors.END}")
                print(analysis.content)
                print(f"{Colors.CYAN}==============={Colors.END}\n")
            except Exception as e:
                print(f"{Colors.RED}[!]{Colors.END} Erreur: {e}")
        
        return results

    def web_scan(self, url: str) -> Dict:
        """Scan web"""
        print(f"{Colors.CYAN}[*]{Colors.END} Scan web: {url}")
        results = {"url": url}
        
        results["whatweb"] = self.safe_execute(f"whatweb -v {url}", timeout=60)
        
        wordlist = "/usr/share/wordlists/dirb/common.txt"
        if os.path.exists(wordlist):
            results["gobuster"] = self.safe_execute(
                f"gobuster dir -u {url} -w {wordlist} -t 30 -b 404,403", 
                timeout=300
            )
        
        if results["whatweb"]["returncode"] == 0:
            analysis = self.llm.invoke(f"""Analyse web {url}:
{results['whatweb']['stdout'][:2000]}
{results.get('gobuster',{}).get('stdout','')[:2000]}
Trouvetechnologies vulnérables et répertoires sensibles.""")
            results["analysis"] = analysis.content
            print(f"\n{Colors.CYAN}=== ANALYSE WEB ==={Colors.END}")
            print(analysis.content)
        
        return results

    def privesc_check(self) -> str:
        """Vérification privilèges"""
        print(f"{Colors.CYAN}[*]{Colors.END} Analyse privilèges locaux...")
        
        checks = {
            "suid": "find / -perm -4000 -type f 2>/dev/null | head -20",
            "sudo": "sudo -l 2>/dev/null",
            "kernel": "uname -a",
            "docker": "id | grep docker"
        }
        
        results = {k: self.safe_execute(v, sandbox=False) for k, v in checks.items()}
        
        return self.llm.invoke(f"""Analyse privesc Linux:
{json.dumps(results, indent=2)}
Vecteurs d'escalade? Priorité Critical/High/Medium/Low.""").content

    # =========================================================================
    # FORENSICS MODULE
    # =========================================================================
    def analyze_logs(self, log_path: str, log_type: str = "auto") -> str:
        """Analyse logs"""
        if not os.path.exists(log_path):
            return f"{Colors.RED}[!]{Colors.END} Fichier introuvable"
        
        print(f"{Colors.CYAN}[*]{Colors.END} Analyse logs: {log_path}")
        
        if log_type == "auto":
            if "auth" in log_path.lower():
                log_type = "auth"
            elif "access" in log_path.lower():
                log_type = "web"
            else:
                log_type = "generic"
        
        try:
            with open(log_path, 'r', errors='ignore') as f:
                lines = f.readlines()[-500:]
                logs = ''.join(lines)
            
            return self.llm.invoke(f"""Analyse forensics logs {log_type}:
{logs[:4000]}
Timeline, attaques détectées, IPs suspectes, recommandations.""").content
            
        except Exception as e:
            return f"{Colors.RED}[!]{Colors.END} Erreur: {e}"

    def memory_analysis_helper(self, dump_path: str) -> str:
        """Helper mémoire"""
        if not os.path.exists(dump_path):
            return f"{Colors.RED}[!]{Colors.END} Dump introuvable"
        
        pslist = self.safe_execute(f"volatility3 -f {dump_path} linux.pslist 2>/dev/null || volatility3 -f {dump_path} windows.pslist", timeout=120)
        
        return self.llm.invoke(f"""Analyse mémoire:
{pslist['stdout'][:2000]}
Processus suspects?""").content

    # =========================================================================
    # HARDENING MODULE
    # =========================================================================
    def ssh_audit(self, target: str = "localhost") -> str:
        """Audit SSH"""
        result = self.safe_execute(f"ssh-audit {target} 2>/dev/null || cat /etc/ssh/sshd_config", timeout=30)
        
        return self.llm.invoke(f"""Audit SSH:
{result['stdout']}
Algorithmes obsolètes? Génère sshd_config durci.""").content

    def docker_security_audit(self) -> str:
        """Audit Docker"""
        checks = {
            "images": "docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null || echo 'Docker non dispo'",
            "containers": "docker ps -a 2>/dev/null || echo 'N/A'"
        }
        results = {k: self.safe_execute(v, sandbox=False) for k, v in checks.items()}
        
        return self.llm.invoke(f"""Audit Docker:
{json.dumps(results)}
Risques et hardening.""").content

    # =========================================================================
    # UTILITAIRES
    # =========================================================================
    def _save_osint_report(self, target: str, data: Dict):
        """Sauvegarde rapport OSINT"""
        try:
            filename = f"osint_{target}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            filepath = os.path.join(os.path.expanduser("~/cyber-agent/exports"), filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"{Colors.GREEN}[+]{Colors.END} Rapport: {filepath}")
        except Exception as e:
            pass

    def chat(self, message: str) -> str:
        """Chat libre avec mémoire de système"""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=message)
        ]
        return self.llm.invoke(messages).content

    def interactive_wizard(self):
        """Guide interactif pour débutants"""
        print(f"\n{Colors.CYAN}🪄  CONFIGURATION GUIDÉE DU CYBER-AGENT{Colors.END}")
        print("------------------------------------------")
        target = input(f"{Colors.YELLOW}?> Nom ou IP de votre cible actuelle (ex: scanme.nmap.org): {Colors.END}").strip()
        if not target: return
        
        print(f"\n{Colors.GREEN}[*]{Colors.END} Très bien. Que souhaitez-vous faire avec {target} ?")
        print("1. Scan de ports et services (Recon)")
        print("2. Recherche d'informations publiques (OSINT)")
        print("3. Scan de vulnérabilités Web")
        
        choice = input(f"{Colors.YELLOW}?> Choix [1-3]: {Colors.END}").strip()
        
        if choice == "1":
            self.run_recon(target)
        elif choice == "2":
            self.osint_domain(target)
        elif choice == "3":
            url = f"http://{target}" if not target.startswith("http") else target
            self.web_scan(url)
        else:
            print("Retour au shell principal.")

    def start_mission(self, mission_type: str, target: str) -> MissionContext:
        """Démarrer mission"""
        mission = MissionContext(target=target, mission_type=mission_type)
        self.missions.append(mission)
        self.current_mission = mission
        print(f"{Colors.GREEN}[+]{Colors.END} Mission '{mission_type}' sur {target}")
        return mission

# ============================================================================
# SHELL INTERACTIF
# ============================================================================
class CyberShell:
    def __init__(self):
        self.config = self._load_config()
        self.agent = SecurityAgent(
            model_name=self.config.get("model", "qwen2.5:14b"),
            device_type=self.config.get("device_type", "generic")
        )
    
    def _load_config(self) -> Dict:
        config_path = os.path.expanduser("~/.config/cyber-agent/config.json")
        defaults = {
            "model": "qwen2.5:14b",
            "device_type": "generic"
        }
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    return {**defaults, **json.load(f)}
            except:
                return defaults
        return defaults
    
    def banner(self):
        print(f"""{Colors.CYAN}
    ┌──────────────────────────────────────────────────────────┐
    │  🔒 CYBER-AGENT v2.2 + RAG [ACTIF]                        │
    │  Assistant Cybersécurité Décentralisé & Offline          │
    └──────────────────────────────────────────────────────────┘{Colors.END}""")
        if not RAG_AVAILABLE:
            print(f"{Colors.YELLOW}[!] Mode RAG dégradé (installez chromadb/sentence-transformers){Colors.END}\n")
    
    def help(self):
        print(f"""
{Colors.GREEN}OSINT:{Colors.END}          osint domain|email|user <cible>
{Colors.GREEN}PENTEST:{Colors.END}        recon <target>, web <url>, privesc
{Colors.GREEN}FORENSICS:{Colors.END}      logs <fichier>, memory <dump>
{Colors.GREEN}HARDENING:{Colors.END}      ssh [target], docker
{Colors.CYAN}RAG KNOWLEDGE:{Colors.END}  rag <question> | learn <dossier> | sources
{Colors.MAGENTA}GUIDE:{Colors.END}          wizard (mode interactif)
{Colors.GREEN}AUTRES:{Colors.END}         chat <msg>, mission <type> <target>, quit
{Colors.YELLOW}NOTE:{Colors.END}           Toute commande non reconnue est envoyée au Chat IA.
""")

    def run(self):
        self.banner()
        self.help()
        
        # Onboarding interactif au démarrage
        print(f"\n{Colors.CYAN}[i]{Colors.END} Tapez '{Colors.MAGENTA}wizard{Colors.END}' pour lancer le guide interactif.")
        
        while True:
            try:
                user_input = input(f"\n{Colors.MAGENTA}[CyberAgent]{Colors.END} > ").strip()
                if not user_input:
                    continue
                
                parts = user_input.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                if cmd in ["quit", "exit"]:
                    print(f"{Colors.YELLOW}[*]{Colors.END} Au revoir!")
                    break
                
                elif cmd == "help":
                    self.help()
                
                # OSINT
                elif cmd == "osint":
                    if len(args) < 2:
                        print(f"{Colors.RED}[!]{Colors.END} Usage: osint <domain|email|user> <cible>")
                        continue
                    subcmd, target = args[0], args[1]
                    
                    if subcmd == "domain":
                        self.agent.osint_domain(target)
                    elif subcmd == "email":
                        result = self.agent.osint_email(target)
                        print(f"Risque: {result.get('risk', 'N/A')}")
                    elif subcmd in ["user", "username"]:
                        result = self.agent.osint_username(target)
                        print(f"Profils: {len(result.get('profiles', []))}")
                    else:
                        print(f"{Colors.RED}[!]{Colors.END} Sous-commande inconnue")
                
                # PENTEST
                elif cmd == "recon":
                    if not args:
                        print(f"{Colors.RED}[!]{Colors.END} Usage: recon <target>")
                        continue
                    intensity = input("Intensité [normal/stealth/aggressive]: ").strip() or "normal"
                    self.agent.run_recon(args[0], intensity)
                
                elif cmd == "web":
                    if not args:
                        print(f"{Colors.RED}[!]{Colors.END} Usage: web <url>")
                        continue
                    self.agent.web_scan(args[0])
                
                elif cmd == "privesc":
                    print(self.agent.privesc_check())
                
                # FORENSICS
                elif cmd == "logs":
                    if not args:
                        print(f"{Colors.RED}[!]{Colors.END} Usage: logs <fichier>")
                        continue
                    log_type = args[1] if len(args) > 1 else "auto"
                    print(self.agent.analyze_logs(args[0], log_type))
                
                elif cmd == "memory":
                    if not args:
                        print(f"{Colors.RED}[!]{Colors.END} Usage: memory <chemin_dump>")
                        continue
                    print(self.agent.memory_analysis_helper(args[0]))
                
                # HARDENING
                elif cmd == "ssh":
                    target = args[0] if args else "localhost"
                    print(self.agent.ssh_audit(target))
                
                elif cmd == "docker":
                    print(self.agent.docker_security_audit())
                
                # RAG - NOUVEAUTÉS
                elif cmd == "rag":
                    if not args:
                        print(f"{Colors.RED}[!]{Colors.END} Usage: rag <question>")
                        continue
                    question = " ".join(args)
                    print(self.agent.rag_query(question))
                
                elif cmd == "learn":
                    if not args:
                        print(f"{Colors.RED}[!]{Colors.END} Usage: learn <chemin_dossier_ou_fichier>")
                        continue
                    print(self.agent.ingest_knowledge(args[0]))
                
                elif cmd == "sources":
                    print(self.agent.list_rag_sources())
                
                # AUTRES
                elif cmd == "mission":
                    if len(args) < 2:
                        print(f"{Colors.RED}[!]{Colors.END} Usage: mission <type> <target>")
                        continue
                    self.agent.start_mission(args[0], args[1])

                elif cmd == "wizard":
                    self.agent.interactive_wizard()

                elif cmd == "chat":
                    if not args:
                        print(f"{Colors.RED}[!]{Colors.END} Usage: chat <message>")
                        continue
                    response = self.agent.chat(" ".join(args))
                    print(f"\n{Colors.CYAN}AI>{Colors.END} {response}\n")
                
                else:
                    # Fallback intelligent vers le Chat
                    print(f"{Colors.YELLOW}[*]{Colors.END} Commande non reconnue. Envoi à l'IA...")
                    response = self.agent.chat(user_input)
                    print(f"\n{Colors.CYAN}AI>{Colors.END} {response}\n")
            
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[!]{Colors.END} Ctrl+C - Tapez 'quit' pour sortir")
            except Exception as e:
                print(f"{Colors.RED}[ERROR]{Colors.END} {e}")

def main():
    try:
        shell = CyberShell()
        shell.run()
    except KeyboardInterrupt:
        print("\n[*] Interrompu")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}[FATAL]{Colors.END} {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
