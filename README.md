# 🦅 Cyber-Agent v3.0

Agent de cybersécurité 100% offline utilisant Ollama, LangChain et ChromaDB.

## ✨ Fonctionnalités
- **RAG Pentest** : Base de connaissances locale (Mitre, OWASP, HackTricks, ANSSI).
- **OSINT** : Recherche de sous-domaines, emails, profils sociaux.
- **Pentest** : Scans Nmap automatisés, analyses de vulnérabilités web.
- **Forensics** : Analyse de logs IA, aide à l'analyse mémoire.
- **Hardening** : Audit de config SSH et Docker.
- **Totalement Privé** : Toutes les données restent sur votre machine.

## 🛠️ Installation

```bash
cd cyber-agent
chmod +x install_cyberagent.sh
./install_cyberagent.sh
```

## 📖 Documentation
- [Manuel de l'Agent](DOCS/AGENT.md)
- [Base de Connaissances (RAG)](DOCS/RAG.md)

## 📊 Benchmark
Un outil de benchmark est inclus pour tester si votre matériel est suffisant pour faire tourner l'agent confortablement :
```bash
./venv/bin/python3 scripts/benchmark.py
```
Il testera la vitesse d'inférence du LLM et la latence de la recherche vectorielle.

## ⚖️ Licence
Ce projet est destiné à un usage éducatif et éthique uniquement.
