const Applet = imports.ui.applet;
const Main = imports.ui.main;
const Util = imports.misc.util;
const GLib = imports.gi.GLib;
const Gettext = imports.gettext;

function _(str) {
    return Gettext.dgettext("mint-screenshot", str);
}

class MintScreenshotApplet extends Applet.IconApplet {
    constructor(metadata, orientation, panel_height, instance_id) {
        super(orientation, panel_height, instance_id);
        this.set_applet_icon_symbolic_name("camera-photo-symbolic");
        this.set_applet_tooltip(_("Take a screenshot"));
        global.log("Mint Screenshot: Applet initialized");
    }

    _takeScreenshot() {
        global.log("Mint Screenshot: Triggering capture...");
        let pythonScript = GLib.get_home_dir() + "/projects/mint-screenshot/main.py";
        // Use full path to python3 and redirect output to a log file for debugging
        let command = `python3 "${pythonScript}" > /tmp/mint-screenshot.log 2>&1`;
        Util.spawnCommandLine(command);
    }

    on_applet_clicked(event) {
        this._takeScreenshot();
    }
}

function main(metadata, orientation, panel_height, instance_id) {
    return new MintScreenshotApplet(metadata, orientation, panel_height, instance_id);
}
