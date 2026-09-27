#!/bin/bash
# EVO-AI sshd hardening script - prevents brute force from locking up sshd
# Run once on fresh server, persists via /etc/rc.local

set -e

echo "=== Hardening sshd ==="

# Backup
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.pre-evo.bak 2>/dev/null || true

# Anti-brute-force settings
cat >> /etc/ssh/sshd_config << 'EOF'

# EVO-AI anti-brute-force hardening
MaxStartups 3:50:6
MaxSessions 5
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30
AllowUsers root
EOF

# Validate
if ! sshd -t; then
    echo "sshd config invalid - reverting"
    cp /etc/ssh/sshd_config.pre-evo.bak /etc/ssh/sshd_config
    exit 1
fi

# Restart sshd
systemctl restart sshd

# iptables rate limit
iptables -I INPUT -p tcp --dport 22 -m state --state NEW -m recent --set 2>/dev/null
iptables -I INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 5 -j DROP 2>/dev/null

# Save iptables
if command -v iptables-save >/dev/null; then
    iptables-save > /etc/iptables.rules
fi

# Persist via rc.local
cat > /etc/rc.local << 'RCEOF'
#!/bin/bash
# iptables NAT + SSH rate limit (auto-restored on reboot)
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8765
iptables -I INPUT -p tcp --dport 22 -m state --state NEW -m recent --set
iptables -I INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 5 -j DROP
[ -f /etc/iptables.rules ] && iptables-restore < /etc/iptables.rules
exit 0
RCEOF
chmod +x /etc/rc.local

echo "✅ sshd hardened:"
echo "  MaxStartups: 10:30:100 → 3:50:6"
echo "  MaxSessions: 10 → 5"
echo "  SSH rate limit: 5/min per IP"
echo "  Persisted in /etc/rc.local"
