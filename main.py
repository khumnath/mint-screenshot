#!/usr/bin/env python3
import sys
import os
import math
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Wnck, GLib, Pango, PangoCairo
import cairo

class AppState:
    SELECTING = 1
    ANNOTATING = 2

class Annotation:
    def __init__(self, type, start, end, color=(1,0,0), width=2, text=""):
        self.type = type # 'rect', 'arrow', 'text', 'ellipse'
        self.start = start # (x, y)
        self.end = end # (x, y)
        self.color = color
        self.width = width
        self.text = text

class ScreenshotOverlay(Gtk.Window):
    def __init__(self, screenshot_path=None):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.screenshot_path = screenshot_path
        
        # Window setup
        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_keep_above(True)
        
        # Enable transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        # Monitor and Scale Detection
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geom = monitor.get_geometry()
        self.width = geom.width
        self.height = geom.height

        # BACKGROUND CAPTURE (Immediate)
        window = Gdk.get_default_root_window()
        # Capture RAW pixels (e.g. 2880x1800)
        self.full_pixbuf = Gdk.pixbuf_get_from_window(window, geom.x, geom.y, window.get_width(), window.get_height())
        self.scale = self.get_scale_factor()

        # Target the primary monitor
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.fullscreen_on_monitor(screen, 0)

        # State
        self.state = AppState.SELECTING
        self.selection_start = None
        self.selection_end = None
        self.rect = None # (x, y, w, h)
        
        # Window detection
        self.windows = self._get_windows()
        self.hovered_window = None

        # Annotation State
        self.annotations = []
        self.current_ann = None
        self.current_tool = 'rect' # 'rect', 'arrow', 'text', 'ellipse'
        self.current_color = (1.0, 0.0, 0.0) # Red
        self.line_width = 3

        # Toolbar
        self.toolbar = None

        # Signals
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("key-press-event", self.on_key_press)
        
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.KEY_PRESS_MASK)

        self.show_all()

    def _get_windows(self):
        screen = Wnck.Screen.get_default()
        screen.force_update()
        windows = []
        for window in screen.get_windows():
            if window.get_window_type() == Wnck.WindowType.NORMAL:
                x, y, w, h = window.get_geometry()
                x = max(0, x); y = max(0, y)
                w = min(self.width - x, w); h = min(self.height - y, h)
                if w > 0 and h > 0:
                    windows.append({'rect': (x, y, w, h)})
        return windows

    def on_draw(self, widget, cr):
        allocation = widget.get_allocation()
        
        # Always draw the frozen background
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        
        if self.full_pixbuf:
            # Create a HiDPI-aware surface from the raw pixbuf
            # We scale the image by the monitor's scale factor
            surface = Gdk.cairo_surface_create_from_pixbuf(self.full_pixbuf, self.scale, self.get_window())
            cr.set_source_surface(surface, 0, 0)
            cr.paint()

        if self.state == AppState.SELECTING:
            # Dim the whole screen
            cr.set_source_rgba(0, 0, 0, 0.4)
            cr.paint()

            # Instructions
            cr.set_source_rgba(0, 0, 0, 0.8)
            cr.rectangle(0, 0, allocation.width, 40)
            cr.fill()
            cr.set_source_rgb(1, 1, 1)
            layout = self.create_pango_layout("Drag to select area | Click to select window | ESC to cancel")
            cr.move_to(20, 10)
            PangoCairo.show_layout(cr, layout)

            target_rect = None
            if self.selection_start and self.selection_end:
                target_rect = self._get_rect(self.selection_start, self.selection_end)
            elif self.hovered_window:
                target_rect = self.hovered_window['rect']
                
            if target_rect:
                x, y, w, h = target_rect
                # Reveal area
                cr.save()
                cr.set_operator(cairo.Operator.CLEAR)
                cr.rectangle(x, y, w, h)
                cr.fill()
                cr.restore()
                
                # Redraw area from background surface
                cr.save()
                cr.rectangle(x, y, w, h)
                cr.clip()
                cr.set_source_surface(surface, 0, 0)
                cr.paint()
                cr.restore()
                
                # Highlight Border
                cr.set_source_rgb(0, 0.6, 1.0)
                cr.set_line_width(2)
                cr.rectangle(x, y, w, h)
                cr.stroke()
        
        elif self.state == AppState.ANNOTATING:
            x, y, w, h = self.rect
            # Dim outside
            cr.save()
            cr.set_fill_rule(cairo.FillRule.EVEN_ODD)
            cr.set_source_rgba(0, 0, 0, 0.4)
            cr.rectangle(0, 0, allocation.width, allocation.height)
            cr.rectangle(x, y, w, h)
            cr.fill()
            cr.restore()
            
            # Border
            cr.set_source_rgb(0, 0.6, 1.0)
            cr.set_line_width(1)
            cr.rectangle(x, y, w, h)
            cr.stroke()

            # Draw existing annotations
            for ann in self.annotations:
                self._draw_annotation(cr, ann)
            
            # Draw current annotation
            if self.current_ann:
                self._draw_annotation(cr, self.current_ann)

    def _get_rect(self, start, end):
        x1, y1 = start; x2, y2 = end
        return min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2)

    def _draw_selection_area(self, cr, x, y, w, h):
        cr.save()
        # Create a "hole" in the current drawing (which is already dimmed)
        cr.set_operator(cairo.Operator.CLEAR)
        cr.rectangle(x, y, w, h)
        cr.fill()
        cr.restore()
        
        cr.save()
        # Clip to selection area
        cr.rectangle(x, y, w, h)
        cr.clip()
        
        # Pixbuf is now 1:1 logical size
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
        cr.paint()
        cr.restore()

        # Border
        cr.set_source_rgb(0, 0.6, 1.0)
        cr.set_line_width(2)
        cr.rectangle(x, y, w, h)
        cr.stroke()

    def _draw_annotation(self, cr, ann):
        cr.set_source_rgb(*ann.color)
        cr.set_line_width(ann.width)
        x1, y1 = ann.start; x2, y2 = ann.end
        
        if ann.type == 'rect':
            cr.rectangle(min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))
            cr.stroke()
        elif ann.type == 'arrow':
            self._draw_arrow(cr, x1, y1, x2, y2)
        elif ann.type == 'ellipse':
            cr.save()
            cr.translate(min(x1, x2) + abs(x1-x2)/2, min(y1, y2) + abs(y1-y2)/2)
            cr.scale(abs(x1-x2)/2, abs(y1-y2)/2)
            cr.arc(0, 0, 1, 0, 2*3.14159)
            cr.restore()
            cr.stroke()

    def _draw_arrow(self, cr, x1, y1, x2, y2):
        import math
        angle = math.atan2(y2 - y1, x2 - x1)
        length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        arrow_size = 15
        
        cr.move_to(x1, y1)
        cr.line_to(x2, y2)
        cr.stroke()
        
        cr.save()
        cr.translate(x2, y2)
        cr.rotate(angle)
        cr.move_to(0, 0)
        cr.line_to(-arrow_size, arrow_size/2)
        cr.line_to(-arrow_size, -arrow_size/2)
        cr.close_path()
        cr.fill()
        cr.restore()

    def on_button_press(self, widget, event):
        if event.button == 1:
            if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
                self.rect = (0, 0, self.width, self.height)
                self.state = AppState.ANNOTATING
                self._show_toolbar()
                self.queue_draw()
                return
            
            if self.state == AppState.SELECTING:
                self.selection_start = (event.x, event.y)
            elif self.state == AppState.ANNOTATING:
                self.current_ann = Annotation(self.current_tool, (event.x, event.y), (event.x, event.y), self.current_color, self.line_width)

    def on_button_release(self, widget, event):
        if event.button == 1:
            if self.state == AppState.SELECTING:
                if self.selection_start:
                    x, y, w, h = self._get_rect(self.selection_start, (event.x, event.y))
                    if w < 5 and h < 5 and self.hovered_window:
                        self.rect = self.hovered_window['rect']
                    else:
                        self.rect = (x, y, w, h)
                
                if self.rect and self.rect[2] > 5 and self.rect[3] > 5:
                    self.state = AppState.ANNOTATING
                    self._show_toolbar()
                self.selection_start = None
                self.queue_draw()
            elif self.state == AppState.ANNOTATING:
                if self.current_ann:
                    self.annotations.append(self.current_ann)
                    self.current_ann = None
                    self.queue_draw()

    def on_motion_notify(self, widget, event):
        if self.state == AppState.SELECTING:
            if self.selection_start:
                self.selection_end = (event.x, event.y)
            else:
                self.hovered_window = None
                for win in reversed(self.windows):
                    x, y, w, h = win['rect']
                    if x <= event.x <= x + w and y <= event.y <= y + h:
                        self.hovered_window = win
                        break
        elif self.state == AppState.ANNOTATING:
            if self.current_ann:
                self.current_ann.end = (event.x, event.y)
        self.queue_draw()

    def _show_toolbar(self):
        if self.toolbar: self.toolbar.destroy()
        self.toolbar = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.toolbar.set_keep_above(True)
        
        # Apply CSS for premium look
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(b"""
            #toolbar { 
                background: rgba(40, 40, 40, 0.9); 
                border-radius: 8px; 
                padding: 4px;
                border: 1px solid rgba(255,255,255,0.1);
            }
            button { background: transparent; border: none; padding: 8px; color: white; }
            button:hover { background: rgba(255,255,255,0.1); border-radius: 4px; }
        """)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.set_name("toolbar")
        
        tools = [('rect', 'draw-rectangle-symbolic', 'Rectangle'), 
                 ('ellipse', 'draw-ellipse-symbolic', 'Ellipse'), 
                 ('arrow', 'draw-arrow-forward-symbolic', 'Arrow')]
        
        for tool, icon, label in tools:
            btn = Gtk.Button.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
            btn.set_tooltip_text(label)
            btn.connect("clicked", lambda b, t=tool: self._set_tool(t))
            box.add(btn)
        
        # Save button
        save_btn = Gtk.Button.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)
        save_btn.set_tooltip_text("Save and Copy (Enter)")
        save_btn.connect("clicked", lambda b: self._save_screenshot())
        box.add(save_btn)
        
        # Close button
        close_btn = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON)
        close_btn.connect("clicked", lambda b: Gtk.main_quit())
        box.add(close_btn)

        self.toolbar.add(box)
        
        # Position toolbar at the top of the screen, centered
        toolbar_y = 10
        toolbar_x = (self.width / 2) - 100
        toolbar_x = max(10, min(self.width - 210, toolbar_x))
        
        self.toolbar.move(int(toolbar_x), int(toolbar_y))
        self.toolbar.show_all()

    def _set_tool(self, tool):
        self.current_tool = tool

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
        elif event.keyval == Gdk.KEY_z and (event.state & Gdk.ModifierType.CONTROL_MASK):
            if self.annotations:
                self.annotations.pop()
                self.queue_draw()

    def _save_screenshot(self):
        x, y, w, h = self.rect
        # Save at device pixel resolution is not needed here as full_pixbuf is already logical size
        # Or should we use raw?
        # Let's keep it consistent with full_pixbuf.
        
        surface = cairo.ImageSurface(cairo.Format.ARGB32, int(w), int(h))
        cr = cairo.Context(surface)
        
        # Draw background from frozen pixbuf
        Gdk.cairo_set_source_pixbuf(cr, self.full_pixbuf, -x, -y)
        cr.paint()
        
        # Draw annotations
        for ann in self.annotations:
            self._draw_annotation(cr, ann)
            
        path = os.path.expanduser("~/Pictures/Screenshot-" + GLib.DateTime.new_now_local().format("%Y%m%d-%H%M%S") + ".png")
        surface.write_to_png(path)
        
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        final_pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        clipboard.set_image(final_pixbuf)
        clipboard.store()
        
        Gtk.main_quit()

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    overlay = ScreenshotOverlay(path)
    Gtk.main()
