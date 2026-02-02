#!/bin/bash
# Cyber-Agent Model Manager v1.0
# Gestion des modèles Ollama avec conservation du contexte

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

CONFIG_DIR="$HOME/.config/cyber-agent"
CONFIG_FILE="$CONFIG_DIR/config.json"
MODELS_DIR="$HOME/.ollama/models"
INSTALL_DIR="$HOME/cyber-agent"  # Adapte si différent

# Détection hardware
detect_hardware() {
    CPU_MODEL=$(grep -m1 'model name' /proc/cpuinfo | cut -d':' -f2 | xargs)
    RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
    
    if echo "$CPU_MODEL" | grep -q "8650U"; then
        DEVICE_TYPE="thinkpad20kh"
        DEFAULT_THREADS=6
        MAX_MODEL_SIZE="16"  # GB
    elif echo "$CPU_MODEL" | grep -q "8550U"; then
        DEVICE_TYPE="miix520"
        DEFAULT_THREADS=4
        MAX_MODEL_SIZE="12"  # GB thermique limité
    else
        DEVICE_TYPE="generic"
        DEFAULT_THREADS=4
        MAX_MODEL_SIZE="8"
    fi
    echo -e "${BLUE}[INFO] Hardware: $DEVICE_TYPE | RAM: ${RAM_GB}GB | Threads recommandés: $DEFAULT_THREADS${NC}"
}

# Lecture config
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        CURRENT_MODEL=$(jq -r '.model // "non défini"' "$CONFIG_FILE" 2>/dev/null || echo "non défini")
        CURRENT_TEMP=$(jq -r '.temperature // "0.1"' "$CONFIG_FILE")
        CURRENT_CTX=$(jq -r '.num_ctx // "32768"' "$CONFIG_FILE")
    else
        mkdir -p "$CONFIG_DIR"
        CURRENT_MODEL="non défini"
        CURRENT_TEMP="0.1"
        CURRENT_CTX="32768"
    fi
}

# Sauvegarde config
save_config() {
    local model=$1
    local temp=${2:-0.1}
    local ctx=${3:-32768}
    local threads=${4:-$DEFAULT_THREADS}
    
    cat > "$CONFIG_FILE" << EOF
{
    "model": "$model",
    "device_type": "$DEVICE_TYPE",
    "temperature": $temp,
    "num_ctx": $ctx,
    "num_thread": $threads,
    "install_dir": "$INSTALL_DIR",
    "last_updated": "$(date '+%Y-%m-%d %H:%M:%S')",
    "hardware": {
        "cpu": "$CPU_MODEL",
        "ram_gb": $RAM_GB,
        "threads": $threads
    }
}
EOF
    echo -e "${GREEN}[✓] Configuration sauvegardée${NC}"
}

# Taille modèle estimation (approximative)
get_model_size() {
    local model=$1
    case "$model" in
        *:8b|*8b) echo "5" ;;
        *:12b|*12b) echo "8" ;;
        *:14b|*14b) echo "9" ;;
        *:32b|*32b) echo "20" ;;
        *:70b|*70b) echo "40" ;;
        *) echo "10" ;;  # Défaut
    esac
}

# Liste modèles installés
list_installed() {
    echo -e "\n${CYAN}═══ MODÈLES INSTALLÉS ═══${NC}"
    ollama list 2>/dev/null | tail -n +2 | while read -r line; do
        name=$(echo "$line" | awk '{print $1}')
        size=$(echo "$line" | awk '{print $3}')
        modified=$(echo "$line" | awk '{print $4, $5, $6}')
        
        if [ "$name" == "$CURRENT_MODEL" ]; then
            echo -e "${GREEN}▶ $name${NC} (actif) - $size - $modified"
        else
            echo -e "  $name - $size - $modified"
        fi
    done
    echo ""
}

# Installer nouveau modèle
install_model() {
    echo -e "${CYAN}═══ INSTALLATION NOUVEAU MODÈLE ═══${NC}"
    echo "Modèles recommandés pour ton hardware (${RAM_GB}GB RAM) :"
    echo "1) llama3.1:8b        (~5GB)   - Rapide, bon pour 8GB RAM"
    echo "2) qwen2.5:14b        (~9GB)   - Équilibré, multilingue FR"
    echo "3) mistral-nemo:12b   (~7GB)   - Spécialisé code technique"
    echo "4) gemma3:12b         (~8GB)   - Nouveau, contexte long"
    echo "5) qwen2.5:32b        (~20GB)  - Puissant (si 32GB RAM)"
    echo "6) Autre (saisie manuelle)"
    
    read -p "Choix [2]: " choice
    case $choice in
        1) MODEL="llama3.1:8b" ;;
        2) MODEL="qwen2.5:14b" ;;
        3) MODEL="mistral-nemo:12b" ;;
        4) MODEL="gemma3:12b" ;;
        5) 
            if [ "$RAM_GB" -lt 32 ]; then
                echo -e "${RED}[WARN] 32B requiert ~20GB RAM, tu as ${RAM_GB}GB. Continuer quand même ? (o/n)${NC}"
                read -p "" confirm
                [[ $confirm != "o" ]] && return
            fi
            MODEL="qwen2.5:32b" 
            ;;
        6) read -p "Nom exact du modèle Ollama (ex: mixtral:8x7b): " MODEL ;;
        *) MODEL="qwen2.5:14b" ;;
    esac
    
    # Vérification taille
    est_size=$(get_model_size "$MODEL")
    if [ "$est_size" -gt "$MAX_MODEL_SIZE" ]; then
        echo -e "${YELLOW}[WARN] Modèle potentiellement trop gros (${est_size}GB > ${MAX_MODEL_SIZE}GB recommandé)${NC}"
        read -p "Continuer quand même ? (o/n): " confirm
        [[ $confirm != "o" ]] && return
    fi
    
    echo -e "${BLUE}[*] Téléchargement de $MODEL...${NC}"
    if ollama pull "$MODEL"; then
        echo -e "${GREEN}[✓] Modèle installé${NC}"
        
        # Créer une config personnalisée (Modelfile)
        create_custom_model "$MODEL"
        
        # Proposer de switcher immédiatement
        read -p "Activer ce modèle maintenant ? (O/n): " activate
        if [[ "$activate" != "n" ]]; then
            switch_model "$MODEL"
        fi
    else
        echo -e "${RED}[✗] Échec téléchargement${NC}"
    fi
}

# Créer modèle custom avec paramètres optimaux
create_custom_model() {
    local base_model=$1
    local custom_name="cyber-$(echo $base_model | tr ':' '-')"
    
    echo -e "${BLUE}[*] Création du profil optimisé '$custom_name'...${NC}"
    
    # Détection du nombre de threads optimal
    if [ "$DEVICE_TYPE" == "thinkpad20kh" ]; then
        THREADS=6
        CONTEXT=32768
    else
        THREADS=4
        CONTEXT=24576  # Un peu moins pour le Miix pour laisser de la marge
    fi
    
    cat > /tmp/Modelfile-cyber << EOF
FROM $base_model
PARAMETER num_ctx $CONTEXT
PARAMETER num_thread $THREADS
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
SYSTEM Tu es un expert en cybersécurité offensive, défensive et forensics sous Arch Linux/BlackArch. Tu maîtrises les outils nmap, metasploit, volatility, sleuthkit, aircrack, et frameworks d'investigation numérique. Tu fournis des commandes précises, analyses techniques détaillées, et privilégies la sécurité et la légalité. Tu réponds en français sauf demande contraire pour les termes techniques internationaux.
EOF
    
    ollama create "$custom_name" -f /tmp/Modelfile-cyber 2>/dev/null || {
        echo -e "${YELLOW}[!] Création modèle custom échouée, utilisation du modèle de base${NC}"
        custom_name="$base_model"
    }
    
    echo -e "${GREEN}[✓] Profil créé: $custom_name${NC}"
    rm /tmp/Modelfile-cyber
}

# Changer de modèle actif
switch_model() {
    local target_model=$1
    
    if [ -z "$target_model" ]; then
        echo -e "${CYAN}═══ CHANGEMENT DE MODÈLE ═══${NC}"
        list_installed
        
        read -p "Nom du modèle à activer (ex: qwen2.5:14b): " target_model
    fi
    
    # Vérifier si modèle existe
    if ! ollama list | grep -q "^$target_model"; then
        echo -e "${RED}[✗] Modèle '$target_model' non trouvé${NC}"
        echo -e "${YELLOW}[!] Modèles disponibles :${NC}"
        ollama list | tail -n +2 | awk '{print "  - " $1}'
        return 1
    fi
    
    # Vérifier mémoire disponible
    est_size=$(get_model_size "$target_model")
    free_ram=$(free -g | awk '/^Mem:/{print $7}')
    
    if [ "$est_size" -gt "$free_ram" ]; then
        echo -e "${YELLOW}[WARN] RAM disponible insuffisante (${free_ram}GB libre, ${est_size}GB nécessaire)${NC}"
        echo -e "${YELLOW}      Fermez d'abord cyber-agent et autres applications lourdes${NC}"
        read -p "Forcer le changement ? (o/N): " force
        [[ "$force" != "o" ]] && return
    fi
    
    # Sauvegarder l'ancien contexte si on veut revenir
    if [ "$CURRENT_MODEL" != "non défini" ]; then
        cp "$CONFIG_FILE" "$CONFIG_DIR/config-backup-$(date +%Y%m%d-%H%M).json" 2>/dev/null || true
    fi
    
    # Sauvegarder nouvelle config
    save_config "$target_model" "$CURRENT_TEMP" "$CURRENT_CTX" "$DEFAULT_THREADS"
    
    echo -e "${GREEN}[✓] Modèle actif changé : $target_model${NC}"
    echo -e "${CYAN}[INFO] Redémarrez cyber-agent pour appliquer le changement${NC}"
    echo -e "${YELLOW}      (ou utilisez 'reload' dans le shell si implémenté)${NC}"
}

# Configurer paramètres avancés
configure_advanced() {
    echo -e "${CYAN}═══ PARAMÈTRES AVANCÉS ═══${NC}"
    echo "Modèle actuel : $CURRENT_MODEL"
    echo ""
    
    read -p "Température [${CURRENT_TEMP}]: " new_temp
    new_temp=${new_temp:-$CURRENT_TEMP}
    
    read -p "Contexte (tokens) [${CURRENT_CTX}]: " new_ctx
    new_ctx=${new_ctx:-$CURRENT_CTX}
    
    read -p "Threads CPU [${DEFAULT_THREADS}]: " new_threads
    new_threads=${new_threads:-$DEFAULT_THREADS}
    
    read -p "Sauvegarder comme profil par défaut ? (O/n): " save_default
    
    save_config "$CURRENT_MODEL" "$new_temp" "$new_ctx" "$new_threads"
    
    # Option : recréer le modèle custom avec nouveaux paramètres
    if [[ "$save_default" != "n" ]]; then
        create_custom_model "$CURRENT_MODEL"
    fi
    
    echo -e "${GREEN}[✓] Paramètres mis à jour${NC}"
}

# Voir config actuelle
show_config() {
    echo -e "${CYAN}═══ CONFIGURATION ACTUELLE ═══${NC}"
    if [ -f "$CONFIG_FILE" ]; then
        cat "$CONFIG_FILE" | jq . 2>/dev/null || cat "$CONFIG_FILE"
    else
        echo "Aucune config trouvée"
    fi
    echo ""
    
    echo -e "${CYAN}═══ MÉMOIRE SYSTÈME ═══${NC}"
    free -h | grep -E "(Mem|Swap)"
    echo ""
    
    echo -e "${CYAN}═══ MODÈLES OLLAMA ═══${NC}"
    ollama list 2>/dev/null | head -20
}

# Menu principal
main_menu() {
    detect_hardware
    load_config
    
    while true; do
        echo -e "\n${CYAN}╔══════════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║     CYBER-AGENT MODEL MANAGER v1.0       ║${NC}"
        echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
        echo -e "Modèle actif : ${GREEN}$CURRENT_MODEL${NC} | Hardware : ${YELLOW}$DEVICE_TYPE${NC}"
        echo ""
        echo "1) 📋 Lister modèles installés"
        echo "2) ⬇️  Installer nouveau modèle"
        echo "3) 🔄 Changer de modèle actif"
        echo "4) ⚙️  Configurer paramètres (température, contexte)"
        echo "5) 👁️  Voir configuration complète"
        echo "6) 🗑️  Supprimer un modèle (libérer espace)"
        echo "7) 💾 Créer modèle custom optimisé"
        echo "8) 🚪 Quitter"
        echo ""
        read -p "Choix [1-8]: " choice
        
        case $choice in
            1) list_installed ;;
            2) install_model ;;
            3) switch_model ;;
            4) configure_advanced ;;
            5) show_config ;;
            6) 
                read -p "Modèle à supprimer: " del_model
                read -p "Confirmer suppression $del_model ? (o/N): " confirm
                [[ "$confirm" == "o" ]] && ollama rm "$del_model" && echo "Supprimé."
                ;;
            7) 
                read -p "Modèle de base à optimiser: " base
                create_custom_model "$base"
                ;;
            8) echo "Bye!"; exit 0 ;;
            *) echo "Choix invalide" ;;
        esac
    done
}

# Si argument fourni (mode rapide)
case "$1" in
    --switch|-s)
        switch_model "$2"
        ;;
    --install|-i)
        install_model
        ;;
    --list|-l)
        load_config
        list_installed
        ;;
    *)
        main_menu
        ;;
esac
