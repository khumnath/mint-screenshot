#!/bin/bash

# Configuration
UUID="mint-screenshot@khumnath"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1. Determine Installation Type
INSTALL_TYPE="auto"
for arg in "$@"; do
    case $arg in
        --standalone) INSTALL_TYPE="standalone" ;;
        --applet) INSTALL_TYPE="applet" ;;
    esac
done

if [ "$INSTALL_TYPE" == "auto" ]; then
    if [[ "$XDG_CURRENT_DESKTOP" == *"Cinnamon"* ]] || [[ "$DESKTOP_SESSION" == *"cinnamon"* ]]; then
        INSTALL_TYPE="applet"
    else
        INSTALL_TYPE="standalone"
    fi
fi

if [ "$INSTALL_TYPE" == "applet" ]; then
    TARGET_DIR="$HOME/.local/share/cinnamon/applets/$UUID"
    echo "🚀 Installing as Cinnamon Applet..."
else
    TARGET_DIR="$HOME/.local/share/mint-screenshot"
    echo "🚀 Installing as Standalone Application..."
fi

# 2. Detect package manager and install dependencies
detect_pkg_manager() {
    if command -v apt &>/dev/null; then echo "apt";
    elif command -v pacman &>/dev/null; then echo "pacman";
    elif command -v dnf &>/dev/null; then echo "dnf";
    elif command -v zypper &>/dev/null; then echo "zypper";
    else echo "unknown"; fi
}

PKG_MANAGER=$(detect_pkg_manager)
echo "🔍 Detected package manager: $PKG_MANAGER"
# Package names per distro
case "$PKG_MANAGER" in
    apt) 
        DEPS="python3 python3-gi python3-gi-cairo python3-cairo python3-pil"
        X11_DEPS="gir1.2-wnck-3.0"
        WAYLAND_DEPS="python3-dbus"
        INSTALL_CMD="sudo apt-get install -y"; CHECK_CMD="dpkg -s" ;;
    pacman) 
        DEPS="python python-gobject python-cairo python-pillow"
        X11_DEPS="libwnck3"
        WAYLAND_DEPS="python-dbus"
        INSTALL_CMD="sudo pacman -S --noconfirm"; CHECK_CMD="pacman -Qi" ;;
    dnf) 
        DEPS="python3 python3-gobject python3-cairo python3-pillow"
        X11_DEPS="libwnck3"
        WAYLAND_DEPS="python3-dbus"
        INSTALL_CMD="sudo dnf install -y"; CHECK_CMD="rpm -q" ;;
    zypper) 
        DEPS="python3 python3-gobject python3-cairo python3-pillow"
        X11_DEPS="typelib-1_0-Wnck-3_0"
        WAYLAND_DEPS="python3-dbus"
        INSTALL_CMD="sudo zypper install -y"; CHECK_CMD="rpm -q" ;;
    *) echo "⚠️  Unknown system. Please ensure python3-gi, python3-cairo, and Pillow are installed."; DEPS="" ;;
esac

# Append session-specific dependencies
IS_WAYLAND=false
if [[ "$XDG_SESSION_TYPE" == "wayland" ]] || [[ "$WAYLAND_DISPLAY" != "" ]]; then
    IS_WAYLAND=true
fi

if [ "$IS_WAYLAND" = true ]; then
    DEPS="$DEPS $WAYLAND_DEPS"
    echo "🌐 Environment: Wayland"
else
    DEPS="$DEPS $X11_DEPS"
    echo "🖥️  Environment: X11"
fi

if [ -n "$DEPS" ]; then
    MISSING=""
    for pkg in $DEPS; do if ! $CHECK_CMD "$pkg" &>/dev/null; then MISSING="$MISSING $pkg"; fi; done
    if [ -n "$MISSING" ]; then
        echo "📦 Installing missing dependencies:$MISSING"
        $INSTALL_CMD $MISSING
    else
        echo "✅ All dependencies satisfied."
    fi
fi

# 3. Install Files
echo "📂 Copying files to $TARGET_DIR..."
mkdir -p "$TARGET_DIR"

# Clean up existing files to avoid "same file" errors (especially if they were symlinks)
if [ -d "$TARGET_DIR" ] && [ "$(ls -A "$TARGET_DIR" 2>/dev/null)" ]; then
    echo "🧹 Cleaning previous installation..."
    find "$TARGET_DIR" -maxdepth 1 -type f -delete 2>/dev/null
fi

# Copy core files
cp -f "$PROJECT_DIR"/*.py "$TARGET_DIR/" 2>/dev/null
cp -f "$PROJECT_DIR/applet.js" "$TARGET_DIR/" 2>/dev/null
cp -f "$PROJECT_DIR/metadata.json" "$TARGET_DIR/" 2>/dev/null
cp -f "$PROJECT_DIR/settings-schema.json" "$TARGET_DIR/" 2>/dev/null
cp -f "$PROJECT_DIR/icon.png" "$TARGET_DIR/" 2>/dev/null
cp -rf "$PROJECT_DIR/assets" "$TARGET_DIR/" 2>/dev/null

# 4. Compile Translations
echo "🌐 Compiling translations..."
mkdir -p "$TARGET_DIR/locale"
for po_file in "$PROJECT_DIR/po"/*.po; do
    if [ -f "$po_file" ]; then
        lang=$(basename "$po_file" .po)
        mkdir -p "$TARGET_DIR/locale/$lang/LC_MESSAGES"
        msgfmt "$po_file" -o "$TARGET_DIR/locale/$lang/LC_MESSAGES/$UUID.mo"
    fi
done

chmod +x "$TARGET_DIR/main.py"

# 5. Handle Desktop Entry
echo "🖥️  Configuring Desktop Menu Entry..."
if [ "$INSTALL_TYPE" == "applet" ]; then
    # Keep it inside the applet folder to stay Spices-compliant
    DESKTOP_FILE="$TARGET_DIR/mint-screenshot.desktop"
    echo "📌 Keeping .desktop file inside applet folder (Spices-compliant)"
else
    # Install globally for standalone usage
    DESKTOP_FILE="$HOME/.local/share/applications/mint-screenshot.desktop"
fi

# Process template and save to the determined location
sed "s|PROJECT_PATH|$TARGET_DIR|g" "$PROJECT_DIR/assets/mint-screenshot.desktop" > "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE"

# Update desktop database only if installed to the global applications folder
if [ "$INSTALL_TYPE" == "standalone" ] && command -v update-desktop-database &>/dev/null; then
    update-desktop-database ~/.local/share/applications/
fi

if [ "$INSTALL_TYPE" == "standalone" ]; then
    echo "✅ Standalone installation complete!"
    echo "You can now find 'Mint Screenshot' in your application menu."
else
    echo "✅ Applet installation complete!"
    echo "1. Right-click Cinnamon panel -> Applets"
    echo "2. Add 'Mint Screenshot'"
    echo "3. (Optional) You can also find it in your application menu."
fi
