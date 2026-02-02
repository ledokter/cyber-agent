# 🚀 Procédure d'Upload sur GitHub

Cette procédure vous guide pour mettre en ligne le projet tout en respectant la structure et en évitant d'envoyer les fichiers lourds (bases de données).

## 1. Initialisation Git
Si ce n'est pas déjà fait sur votre machine :
```bash
cd ~/cyber-agent
git init
git add .
git commit -m "Initial commit: Cyber-Agent v3.0 with RAG and Benchmark"
```

## 2. Création du Repository sur GitHub
1. Allez sur [github.com/new](https://github.com/new).
2. Nommez le repository (ex: `cyber-agent`).
3. Ne l'initialisez **pas** avec un README ou une licence (nous les avons déjà).
4. Cliquez sur "Create repository".

## 3. Liaison et Push
Copiez l'URL de votre repo (ex: `https://github.com/VOTRE_NOM/cyber-agent.git`) et exécutez :
```bash
git remote add origin https://github.com/VOTRE_NOM/cyber-agent.git
git branch -M main
git push -u origin main
```

## ⚠️ Notes Importantes
- **Documents RAG** : Le fichier `.gitignore` empêche d'envoyer le dossier `knowledge_base` et `knowledge_db`. C'est normal, car ils font plusieurs Gigas. L'utilisateur final devra lancer `./install_cyberagent.sh` pour les reconstruire localement.
- **Sécurité** : Ne mettez jamais de clés d'API réelles dans le code si vous rendez le repo public.
- **Mises à jour** : Pour envoyer une mise à jour sur GitHub plus tard :
  ```bash
  git add .
  git commit -m "Description de la modif"
  git push
  ```
