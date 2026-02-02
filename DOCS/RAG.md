# 📚 Manuel du Système RAG (Knowledge Base)

Le système RAG (Retrieval-Augmented Generation) permet à l'agent d'accéder à une base de connaissances locale (hors-ligne) contenant des méthodologies de pentest, des guides de l'ANSSI, des cheatsheets OWASP et des techniques d'attaques.

## 📡 Commandes RAG

- `rag <question>` : Pose une question à l'IA en utilisant la base de connaissances.
- `sources` : Liste les documents actuellement indexés dans la base.
- `learn <chemin>` : Ingeste un nouveau dossier ou fichier (PDF, MD, TXT).

## 🗂️ Structure de la Knowledge Base

La base est stockée dans `~/cyber-agent/knowledge_base/` et organisée par modules :
1. **01-mitre-attack** : Techniques et tactiques d'adversaires.
2. **02-owasp-cheatsheets** : Bonnes pratiques et tests de sécurité web.
3. **03-payloads** : Recueils de payloads et techniques de contournement.
4. **04-hacktricks** : Encyclopédie de techniques de pentest.
5. **08-anssi-guides** : Guides officiels de sécurité français.

## ⚙️ Maintenance

### Reconstruire la base
Si vous ajoutez massivement des documents, lancez :
```bash
./venv/bin/python3 build_rag.py
```

### Emplacement des données
- **Documents bruts** : `~/cyber-agent/knowledge_base/`
- **Base Vectorielle (ChromaDB)** : `~/cyber-agent/knowledge_db/`

## 💡 Astuces
- Plus vous ajoutez de documents Markdown (`.md`), plus la précision de l'IA augmente.
- L'agent cite ses sources sous la forme `[Source X]` dans ses réponses.
