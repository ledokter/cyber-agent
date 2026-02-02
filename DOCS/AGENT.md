# 🤖 Manuel d'Utilisation - Cyber Agent

Le **Cyber Agent** est un assistant de cybersécurité offline utilisant un LLM (via Ollama) combiné à un système RAG (Retrieval-Augmented Generation) pour fournir des conseils, exécuter des scans et analyser des données de sécurité.

## 🚀 Démarrage Rapide

Pour lancer l'agent :
```bash
cyber-agent
```
Ou manuellement :
```bash
./venv/bin/python3 cyber_agent_complete.py
```

## 🛠️ Modules et Commandes

### 1. OSINT (Open Source Intelligence)
Reconnaissance passive sur des cibles publiques.
- `osint domain <cible.com>` : Recherche les sous-domaines, emails et analyse via Wayback Machine.
- `osint email <user@example.com>` : Vérifie la présence de l'email sur divers services (via Holehe).
- `osint user <username>` : Recherche le profil sur les réseaux sociaux.

### 2. PENTEST (Tests d'intrusion)
Assistance à la reconnaissance active et scan de vulnérabilités.
- `recon <target>` : Lance un scan Nmap (normal/stealth/aggressive) et analyse les résultats via l'IA.
- `web <url>` : Scan de technologies web (WhatWeb) et énumération de répertoires (Gobuster).
- `privesc` : Vérification automatique des vecteurs d'élévation de privilèges Linux locaux.

### 3. FORENSICS (Analyse de logs)
- `logs <fichier>` : Analyse de logs système ou web pour détecter des intrusions ou comportements suspects.
- `memory <dump>` : Aide à l'analyse de dumps mémoire (nécessite Volatility3).

### 4. HARDENING (Durcissement)
- `ssh [target]` : Audit de configuration SSH.
- `docker` : Audit de sécurité de l'environnement Docker local.

## 💬 Interaction Chat
Vous pouvez poser n'importe quelle question technique directement dans le shell :
- `chat comment configurer firejail ?`
- `quelle est la CVE la plus critique pour Apache 2.4 ?`

## 🏁 Missions
Utilisez `mission <type> <cible>` pour créer un contexte de mission persistant.
Example: `mission InternalPentest 192.168.1.0/24`
