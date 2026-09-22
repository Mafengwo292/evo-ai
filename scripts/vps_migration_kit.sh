#!/bin/bash
# VPS Migration Kit - run on NEW 2GB+ VPS to restore everything

set -e

echo "🚀 EVO-AI VPS Migration Kit"
echo "=========================="

# 1. Install Python 3.11
apt update
apt install -y python3.11 python3.11-venv python3-pip tmux cron curl

# 2. Create directory
mkdir -p /root/evo-ai
cd /root/evo-ai

# 3. Clone repo
git clone https://github.com/Mafengwo292/evo-ai.git .

# 4. Setup Python env
python3.11 -m venv venv
source venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install flask flask-sock requests numpy scipy

# 5. Restore state from S3/curl
# (Use the public state files from GitHub)
curl -s https://raw.githubusercontent.com/Mafengwo292/evo-ai/main/state/RECOVERY_LOG_2.md > /root/evo-ai/state/RECOVERY_LOG_2.md

# 6. Restore systemd services
for svc in evo-api evo-pub evo-test; do
    cat /etc/systemd/system/${svc}.service.bak > /etc/systemd/system/${svc}.service 2>/dev/null || echo "Backup of ${svc}.service not found - skip"
done

# 7. Restore cron
# crontab content is in /workspace/evo-ai/state/cron_backup.txt
curl -s https://raw.githubusercontent.com/Mafengwo292/evo-ai/main/state/cron_backup.txt > /tmp/cron_backup.txt
crontab /tmp/cron_backup.txt

# 8. Restore iptables NAT (will be lost on reboot - add to /etc/rc.local)
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8765
grep -q 'iptables -t nat -A PREROUTING -p tcp --dport 80' /etc/rc.local 2>/dev/null || cat >> /etc/rc.local << 'EOF'
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8765
EOF

# 9. Start services
systemctl daemon-reload
systemctl enable evo-api evo-pub evo-test crond
systemctl start evo-api evo-pub evo-test crond

# 10. Start tunnels
tmux new-session -d -s pinggy 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -p 443 -R 0:127.0.0.1:8765 a.pinggy.io'
tmux new-session -d -s serveo 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:127.0.0.1:8765 serveo.net'

# 11. Verify
sleep 15
curl -s -o /dev/null -w "Public HTTP: %{http_code}\n" http://127.0.0.1:80/api/info

echo ""
echo "✅ Migration complete!"
echo "Check tunnel URLs in /root/evo-ai/data/current_*.txt"
echo ""
echo "⚠️ DON'T FORGET:"
echo "  - Update Aliyun security group (port 80, 443, 8765 open)"
echo "  - Restore SSH key access"
echo "  - Update DNS if you have a domain"
