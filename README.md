# 📸 Mint Screenshot

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Mint Screenshot** is a feature-rich screenshot and annotation tool. While it was initially born as a dedicated applet for the **Cinnamon Desktop**, it has evolved into a versatile, distribution-agnostic tool that works flawlessly on GNOME, KDE, XFCE, and more.

![Application Preview](screenshot.png)

---

## 🛠 How it Works

The tool provides a streamlined pipeline from the moment you decide to capture until the moment you share.

```mermaid
graph TD
    A[Launch App] --> B{Choose Mode}
    B -- Fullscreen --> C[Capture Screen]
    B -- Select Area --> D[Interactive Region Picker]
    B -- Timed --> E[Countdown Timer]
    
    D --> C
    E --> C
    
    C --> F[Annotation Editor]
    
    F --> G{Tools}
    G -- Draw --> H[Pencil/Highlight]
    G -- Shapes --> I[Arrow/Rect/Ellipse]
    G -- Text --> J[Labeling]
    
    H & I & J --> K[Refine/Undo]
    K --> F
    
    F --> L[Finalize]
    L -- Save --> M[File Saved to Folder]
    L -- Copy --> N[Stored in Clipboard]
    
    M & N --> O[System Notification]
```

### 🏗 System Architecture

The application is built on a modular architecture that adapts to your system's display server.

```mermaid
graph LR
    subgraph UI ["User Interface"]
        Launcher[Desktop Launcher]
        Applet[Cinnamon Applet]
    end

    subgraph Core ["Python Core (GTK 3)"]
        Main[Main Entry]
        Editor[Annotation Engine]
        Capture[Capture Logic]
    end

    subgraph System ["Display Server Layers"]
        direction TB
        X11[X11 Session]
        Wayland[Wayland Session]
        Portal[xdg-desktop-portal]
        DBus[D-Bus Interface]
    end

    subgraph Graphics ["Rendering & Assets"]
        Cairo[Cairo Graphics]
        Pillow[Pillow Icon Engine]
    end

    Launcher & Applet --> Main
    Main --> Capture
    Capture -- "X11 Mode" --> X11
    Capture -- "Wayland Mode" --> DBus
    DBus --> Portal
    Portal --> Wayland
    
    Capture --> Editor
    Editor --> Cairo
    Cairo --> Graphics
```


---

## 🌟 Key Features

- **Cross-Platform Compatibility**: Fully supports both **X11** and **Wayland** (via `xdg-desktop-portal`).
- **Multiple Capture Modes**: Fullscreen, interactive region selection, and custom timed captures.
- **Rich Annotation Suite**:
  - **Precision Shapes**: Rectangles, Ellipses, and Arrows with adjustable thickness.
  - **Creative Tools**: Freehand drawing and highlighting.
  - **Text Tool**: Add labels and comments with ease.
- **Modern UI/UX**:
  - **Undo/Redo**: Full history support for all annotations.
  - **High-Res Support**: Includes a premium 512px icon for high-DPI displays.
  - **Material Design**: A sleek, intuitive toolbar that stays out of your way.
- **Global Localization**: Full support for internationalization.

---

## 🚀 Installation

The `install.sh` script is smart—it automatically detects your environment and sets everything up.

### Option 1: Automatic Detection (Recommended)
Simply run the installer, and it will decide whether to install as a Cinnamon Applet or a Standalone application based on your session.
```bash
git clone https://github.com/khumnath/mint-screenshot.git
cd mint-screenshot
./install.sh
```

### Option 2: Force Standalone Mode
To install the menu shortcut and standalone launcher regardless of your desktop environment:
```bash
./install.sh --standalone
```

### Option 3: Force Cinnamon Applet
To install specifically as a Cinnamon applet:
```bash
./install.sh --applet
```

---

## 📦 Dependencies

The tool relies on standard GTK libraries. The installer will attempt to detect and install these for you:
- **Python 3** (GObject, Cairo)
- **libwnck-3** (For X11 window management)
- **xdg-desktop-portal** (For Wayland support)
- **Pillow** (For high-quality icon processing)

---

## 📝 License & Authorship

- **Author**: [Khumnath CG](https://khumnath.com.np)
- **License**: This project is licensed under the **GPL-3.0 License**.

---
*Capture, annotate, and share with ease.*
