#!/bin/bash
# Optimisations i7-8650U pour Cyber-Agent/Ollama

echo "[*] Optimisation i7-8650U (ThinkPad) pour LLM..."

# 1. HugePages (CRITIQUE pour Ollama - réduction TLB misses)
# Alloue 4 hugepages de 1GB pour les gros modèles
echo "[*] Configuration HugePages..."
echo 4 | sudo tee /proc/sys/vm/nr_hugepages
echo "vm.nr_hugepages = 4" | sudo tee /etc/sysctl.d/99-hugepages.conf

# 2. Swappiness agressive (garde RAM pour le modèle, swap pour le système)
echo "[*] Tuning mémoire..."
echo "vm.swappiness = 10" | sudo tee /etc/sysctl.d/99-memory.conf
echo "vm.vfs_cache_pressure = 50" | sudo tee -a /etc/sysctl.d/99-memory.conf
echo "vm.dirty_ratio = 15" | sudo tee -a /etc/sysctl.d/99-memory.conf

# 3. zram avec compression zstd (au lieu de swap disque lent)
echo "[*] Configuration zram..."
sudo modprobe zram num_devices=1
echo zstd | sudo tee /sys/block/zram0/comp_algorithm
echo 8G | sudo tee /sys/block/zram0/disksize  # 50% de ta RAM
sudo mkswap /dev/zram0
sudo swapon /dev/zram0 -p 100  # Priorité haute

# 4. CPU Governor performance quand branché, powersave sur batterie
echo "[*] CPU Governor..."
sudo pacman -S --needed power-profiles-daemon thermald
sudo systemctl enable --now power-profiles-daemon
sudo systemctl enable --now thermald

# 5. Affinité Ollama (isoler les cores pour inference)
# Créer un service override pour Ollama
sudo mkdir -p /etc/systemd/system/ollama.service.d/
sudo tee /etc/systemd/system/ollama.service.d/affinity.conf << EOF
[Service]
CPUAffinity=0-5  # Réserve cores 6-7 pour le système/dispatch
MemoryMax=12G    # Limite pour éviter OOM killer
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama

# 6. I/O Scheduler (deadline pour NVMe, pas mq-deadline)
echo "[*] I/O Optimisation..."
for disk in /sys/block/nvme*; do
    echo deadline | sudo tee $disk/queue/scheduler 2>/dev/null || true
done

# 7. Network buffers (pour forensics/scans réseau)
echo "[*] Network tuning..."
echo "net.core.rmem_max = 134217728" | sudo tee /etc/sysctl.d/99-network.conf
echo "net.core.wmem_max = 134217728" | sudo tee -a /etc/sysctl.d/99-network.conf
echo "net.ipv4.tcp_rmem = 4096 87380 134217728" | sudo tee -a /etc/sysctl.d/99-network.conf
sudo sysctl --system

echo "[✓] Optimisations appliquées. Redémarrage recommandé."
