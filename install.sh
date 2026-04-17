#!/bin/bash

# Configuration
UUID="mint-screenshot@antigravity"
APPLET_DIR="$HOME/.local/share/cinnamon/applets/$UUID"
PROJECT_DIR="$(pwd)"

echo "🚀 Installing Mint Screenshot Applet..."

# 1. Ensure directories exist
mkdir -p "$APPLET_DIR"

# 2. Create symbolic links
echo "🔗 Creating symbolic links..."
ln -sf "$PROJECT_DIR/applet.js" "$APPLET_DIR/"
ln -sf "$PROJECT_DIR/metadata.json" "$APPLET_DIR/"
ln -sf "$PROJECT_DIR/main.py" "$APPLET_DIR/"

# 3. Make the backend executable
chmod +x "$PROJECT_DIR/main.py"

# 4. Check dependencies (optional but recommended)
echo "📦 Checking dependencies..."
if ! dpkg -l | grep -q "python3-gi"; then
    echo "⚠️ Warning: python3-gi is not installed. You may need: sudo apt install python3-gi"
fi
if ! dpkg -l | grep -q "libwnck-3-0"; then
    echo "⚠️ Warning: libwnck-3-0 is not installed. You may need: sudo apt install libwnck-3-0"
fi

echo ""
echo "✅ Installation complete!"
echo "--------------------------------------------------"
echo "To enable the applet:"
echo "1. Right-click your Cinnamon panel -> Applets"
echo "2. Search for 'Mint Screenshot'"
echo "3. Click the (+) button to add it"
echo ""
echo "To restart Cinnamon (if it doesn't appear):"
echo "Press Alt+F2, type 'r', and press Enter"
echo "--------------------------------------------------"
