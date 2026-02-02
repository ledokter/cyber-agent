#!/bin/bash
# setup_knowledge_base.sh

BASE_DIR="$HOME/cyber-agent/knowledge_base"
mkdir -p "$BASE_DIR"

echo "[*] Téléchargement des ressources..."

# 1. MITRE ATT&CK
echo "[+] MITRE ATT&CK..."
git clone --depth 1 https://github.com/mitre/cti.git "$BASE_DIR/01-mitre-attack" 2>/dev/null || echo "Déjà présent"

# 2. OWASP Cheat Sheets  
echo "[+] OWASP..."
git clone --depth 1 https://github.com/OWASP/CheatSheetSeries.git "$BASE_DIR/02-owasp-cheatsheets" 2>/dev/null || echo "Déjà présent"

# 3. Payloads
echo "[+] PayloadsAllTheThings..."
git clone --depth 1 https://github.com/swisskyrepo/PayloadsAllTheThings.git "$BASE_DIR/03-payloads" 2>/dev/null || echo "Déjà présent"

# 4. HackTricks (très complet mais gros)
echo "[+] HackTricks... (peut être long)"
git clone --depth 1 https://github.com/carlospolop/hacktricks.git "$BASE_DIR/04-hacktricks" 2>/dev/null || echo "Déjà présent"

# 5. exploit-db (pour recherche locale)
echo "[+] Exploit-DB..."
git clone --depth 1 https://gitlab.com/exploit-database/exploitdb.git "$BASE_DIR/09-exploitdb" 2>/dev/null || echo "Déjà présent"

# 6. Créer fichiers FR
mkdir -p "$BASE_DIR/08-anssi-guides"
cat > "$BASE_DIR/08-anssi-guides/mots-cles-pentest.md" << 'EOF'
## Méthodologie Pentest ANSSI

### Phase 1: Reconnaissance
- OSINT passif uniquement (pas d'interdirecte)
- Cartographie flux réseaux
- Identification surface d'attaque

### Phase 2: Analyse de vulnérabilités
- Scan sans perturbation
- Analyse configuration (CIS Benchmarks)
- Revue code si source dispo

### Phase 3: Exploitation
- Uniquement avec mandat écrit
- Privilégier DoS
- Documenter chaque étape pour preuve

### Phase 4: Post-exploitation
- Pivoting latéral documenté
- Extraction données chiffrées/anonymisées
- Nettoyage traces (respect RGPD)

### Référentiels
- PSSI (Politique Sécurité Systèmes Information)
- PCA/PRA (Plan Continuité/ Reprise d'Activité)
- LPM (Loi Programmation Militaire) - articles 413-1 à 413-11 CP
- RGPD - article 32 (sécurité traitements)
EOF

echo "[✓] Base de connaissances prête dans $BASE_DIR"
echo "[i] Pour indexer: lancer cyber-agent puis 'learn $BASE_DIR'"
