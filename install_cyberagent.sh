#!/bin/bash
# Cyber-Agent Installer v3.0 - Edition "Patched 3.14"
# Agent de cybersécurité complet avec RAG Pentest

# Couleurs
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

INSTALL_DIR="$HOME/cyber-agent"
CONFIG_DIR="$HOME/.config/cyber-agent"
VENV="$INSTALL_DIR/venv"

echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     CYBER-AGENT v3.0 - INSTALLATEUR AUTOMATIQUE        ║${NC}"
echo -e "${CYAN}║    Compatible Arch/BlackArch - Python 3.14 + RAG       ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"

# 1. Détection Système
echo -e "\n${BLUE}[*] Étape 1: Installation des dépendances système...${NC}"
sudo pacman -Syu --noconfirm --needed python python-pip python-virtualenv ollama firejail git nmap gobuster whatweb theharvester amass subfinder holehe lynis curl

if ! systemctl is-active --quiet ollama; then
    sudo systemctl enable --now ollama
fi

# 2. Setup Environnement
echo -e "\n${BLUE}[*] Étape 2: Préparation de l'environnement virtuel...${NC}"
mkdir -p "$INSTALL_DIR" "$INSTALL_DIR/knowledge_db" "$INSTALL_DIR/exports" "$INSTALL_DIR/logs" "$CONFIG_DIR"
if [ ! -d "$VENV" ]; then
    python -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install --upgrade pip
pip install -r "$INSTALL_DIR/requirements.txt"

# 3. Application des Patchs ChromaDB (Critique pour Python 3.14)
echo -e "\n${BLUE}[*] Étape 3: Application des correctifs de compatibilité...${NC}"
PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
CHROMA_PATH="$VENV/lib/python$PYTHON_VERSION/site-packages/chromadb"

if [ -d "$CHROMA_PATH" ]; then
    echo -e "${YELLOW}[i] Patching ChromaDB in $CHROMA_PATH...${NC}"
    
    # Patch config.py
    python << EOF
import os
path = "$CHROMA_PATH/config.py"
with open(path, 'r') as f: content = f.read()
content = content.replace("from pydantic import BaseSettings", "try:\n    from pydantic_settings import BaseSettings\nexcept ImportError:\n    from pydantic import BaseSettings")
content = content.replace("from typing import List", "from typing import List, Optional")
for field in ["clickhouse_host", "clickhouse_port", "chroma_server_host", "chroma_server_http_port", "chroma_server_grpc_port"]:
    content = content.replace(f"{field}: str = None", f"{field}: Optional[str] = None")
with open(path, 'w') as f: f.write(content)
EOF

    # Patch Collection.py
    python << EOF
import os
path = "$CHROMA_PATH/api/models/Collection.py"
with open(path, 'r') as f: content = f.read()
if "super().__init__(name=name, metadata=metadata, id=id)" in content:
    lines = content.split('\n')
    new_lines = []
    in_init = False
    for line in lines:
        if "def __init__" in line: in_init = True
        if in_init and "super().__init__" in line:
            # On ne l'ajoute pas ici, on le mettra au début
            continue
        if in_init and "self._client = client" in line:
            new_lines.append("        super().__init__(name=name, metadata=metadata, id=id)")
            new_lines.append(line)
            in_init = False # On a fini l'insertion
            continue
        new_lines.append(line)
    with open(path, 'w') as f: f.write('\n'.join(new_lines))
EOF
    echo -e "${GREEN}[✓] ChromaDB patché avec succès${NC}"
fi

# 4. Hardware et Modèle
echo -e "\n${BLUE}[*] Étape 4: Configuration hardware...${NC}"
CPU=$(grep -m1 'model name' /proc/cpuinfo | cut -d':' -f2 | xargs)
RAM=$(free -g | awk '/^Mem:/{print $2}')
DEVICE="generic"
THREADS=4

if echo "$CPU" | grep -q "8650U"; then DEVICE="thinkpad20kh"; THREADS=6; fi

cat > "$CONFIG_DIR/config.json" << EOF
{
    "model": "qwen2.5:14b",
    "device_type": "$DEVICE",
    "num_thread": $THREADS
}
EOF

echo -e "${YELLOW}[*] Téléchargement du modèle (peut être long)...${NC}"
ollama pull qwen2.5:14b

# 5. Ingestion Initiale
echo -e "\n${BLUE}[*] Étape 5: Construction de la base de connaissances...${NC}"
"$VENV/bin/python3" "$INSTALL_DIR/build_rag.py"

# 6. Automatisation (Cron)
echo -e "\n${BLUE}[*] Étape 6: Configuration de l'auto-update...${NC}"
chmod +x "$INSTALL_DIR/scripts/update_cyberagent.sh"
(crontab -l 2>/dev/null | grep -v "update_cyberagent.sh"; echo "0 4 * * * $INSTALL_DIR/scripts/update_cyberagent.sh") | crontab -
echo -e "${GREEN}[✓] Mise à jour programmée tous les jours à 4h00${NC}"

# 7. Finalisation
echo -e "\n${BLUE}[*] Étape 7: Installation du lanceur système...${NC}"
sudo tee /usr/local/bin/cyber-agent > /dev/null << EOF
#!/bin/bash
cd $INSTALL_DIR
source venv/bin/activate
python cyber_agent_complete.py
EOF
sudo chmod +x /usr/local/bin/cyber-agent

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   CYBER-AGENT EST MAINTENANT PRÊT !                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo -e "Tapez '${CYAN}cyber-agent${NC}' pour démarrer."

read -p "Lancer le benchmark de performance ? (O/n): " bench
if [ "$bench" != "n" ] && [ "$bench" != "N" ]; then
    "$VENV/bin/python3" "$INSTALL_DIR/scripts/benchmark.py"
fi

read -p "Lancer l'agent maintenant ? (O/n): " go
if [ "$go" != "n" ] && [ "$go" != "N" ]; then
    cyber-agent
fi
