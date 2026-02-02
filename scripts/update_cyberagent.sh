#!/bin/bash
# Script de mise à jour automatique Cyber-Agent

INSTALL_DIR="$HOME/cyber-agent"
VENV="$INSTALL_DIR/venv"
LOG_FILE="$INSTALL_DIR/logs/update.log"

mkdir -p "$INSTALL_DIR/logs"

echo "[$(date)] Démarrage mise à jour..." >> "$LOG_FILE"

# 1. Mise à jour du code (si repo git)
if [ -d "$INSTALL_DIR/.git" ]; then
    cd "$INSTALL_DIR"
    git pull >> "$LOG_FILE" 2>&1
fi

# 2. Mise à jour des dépendances
if [ -d "$VENV" ]; then
    "$VENV/bin/pip" install -r "$INSTALL_DIR/requirements.txt" >> "$LOG_FILE" 2>&1
fi

# 3. Application du patch Pydantic v2 / Python 3.14 pour ChromaDB 0.3.23
# (Nécessaire après chaque pip install car le package peut être écrasé)
echo "[*] Vérification des patchs system..." >> "$LOG_FILE"
CONFIG_PY="$VENV/lib/python3.14/site-packages/chromadb/config.py"
MODELS_PY="$VENV/lib/python3.14/site-packages/chromadb/api/models/Collection.py"

if [ -f "$CONFIG_PY" ]; then
    # Patch Config
    sed -i 's/from pydantic import BaseSettings/try:\n    from pydantic_settings import BaseSettings\nexcept ImportError:\n    from pydantic import BaseSettings/g' "$CONFIG_PY" 2>/dev/null
    sed -i 's/clickhouse_host: str = None/clickhouse_host: Optional[str] = None/g' "$CONFIG_PY" 2>/dev/null
    # ... autres patchs ...
fi

# 4. Mise à jour du RAG (Ingestion des nouveaux documents)
echo "[*] Mise à jour de la base vectorielle..." >> "$LOG_FILE"
"$VENV/bin/python3" "$INSTALL_DIR/build_rag.py" >> "$LOG_FILE" 2>&1

# 5. Mise à jour du modèle Ollama
MODEL=$(grep '"model":' ~/.config/cyber-agent/config.json | cut -d'"' -f4)
if [ -z "$MODEL" ]; then MODEL="qwen2.5:14b"; fi
ollama pull "$MODEL" >> "$LOG_FILE" 2>&1

echo "[$(date)] Mise à jour terminée." >> "$LOG_FILE"
