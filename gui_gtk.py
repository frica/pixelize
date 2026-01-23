#!/usr/bin/env python3
"""
GTK-based GUI for Pixelize - uses native GTK widgets for proper system integration
"""

try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import Gtk, GdkPixbuf, GLib
except ModuleNotFoundError:
    raise SystemExit(
        "GTK bindings not found. Install system packages or run with system Python.\n"
        "Ubuntu/Debian: sudo apt install python3-gi gir1.2-gtk-3.0\n"
        "Then run: /usr/bin/python3 gui_gtk.py"
    )

from pathlib import Path
import threading

from PIL import Image

from main import pixelate

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}


class PixelizeGTKApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Pixelize - Image Pixelation Tool")
        self.set_default_size(780, 800)
        self.set_border_width(10)

        # State
        self.input_dir = "images"
        self.output_dir = "output"
        self.sizes_str = "16, 32, 64"
        self.image_files = []
        self.current_preview_file = None
        self.current_preview_size = 32
        self.processing = False

        # Build UI
        self.create_ui()

        # Initial scan
        self.scan_input_directory()

    def create_ui(self):
        # Main vertical box
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_vbox)

        # Input Directory Section
        input_label = Gtk.Label(xalign=0)
        input_label.set_markup("<b>Input Directory:</b>")
        main_vbox.pack_start(input_label, False, False, 0)

        input_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_vbox.pack_start(input_hbox, False, False, 0)

        self.input_entry = Gtk.Entry()
        self.input_entry.set_text(self.input_dir)
        self.input_entry.connect("changed", self.on_input_changed)
        input_hbox.pack_start(self.input_entry, True, True, 0)

        input_browse_btn = Gtk.Button(label="Browse")
        input_browse_btn.connect("clicked", self.on_browse_input)
        input_hbox.pack_start(input_browse_btn, False, False, 0)

        # Output Directory Section
        output_label = Gtk.Label(xalign=0)
        output_label.set_markup("<b>Output Directory:</b>")
        main_vbox.pack_start(output_label, False, False, 0)

        output_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_vbox.pack_start(output_hbox, False, False, 0)

        self.output_entry = Gtk.Entry()
        self.output_entry.set_text(self.output_dir)
        self.output_entry.connect("changed", self.on_output_changed)
        output_hbox.pack_start(self.output_entry, True, True, 0)

        output_browse_btn = Gtk.Button(label="Browse")
        output_browse_btn.connect("clicked", self.on_browse_output)
        output_hbox.pack_start(output_browse_btn, False, False, 0)

        # Pixelation Sizes Section
        sizes_label = Gtk.Label(xalign=0)
        sizes_label.set_markup("<b>Pixelation Sizes:</b>")
        main_vbox.pack_start(sizes_label, False, False, 0)

        self.sizes_entry = Gtk.Entry()
        self.sizes_entry.set_text(self.sizes_str)
        self.sizes_entry.connect("changed", self.on_sizes_changed)
        main_vbox.pack_start(self.sizes_entry, False, False, 0)

        sizes_hint = Gtk.Label(xalign=0)
        sizes_hint.set_markup(
            '<span foreground="gray">'
            '(Comma-separated values, e.g., "16, 32, 64, 128")'
            "</span>"
        )
        main_vbox.pack_start(sizes_hint, False, False, 0)

        # Preview Section
        preview_frame = Gtk.Frame(label="Preview")
        preview_frame.set_label_align(0.02, 0.5)
        preview_frame.set_margin_top(10)
        preview_frame.set_margin_bottom(10)
        main_vbox.pack_start(preview_frame, True, True, 0)

        preview_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        preview_vbox.set_margin_start(10)
        preview_vbox.set_margin_end(10)
        preview_vbox.set_margin_top(10)
        preview_vbox.set_margin_bottom(10)
        preview_frame.add(preview_vbox)

        # Preview controls
        preview_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        preview_vbox.pack_start(preview_controls, False, False, 0)

        preview_controls.pack_start(Gtk.Label(label="File:"), False, False, 0)

        self.file_combo = Gtk.ComboBoxText()
        self.file_combo.connect("changed", self.on_preview_file_changed)
        preview_controls.pack_start(self.file_combo, True, True, 0)

        preview_controls.pack_start(Gtk.Label(label="Preview Size:"), False, False, 0)

        self.size_combo = Gtk.ComboBoxText()
        self.size_combo.connect("changed", self.on_preview_size_changed)
        preview_controls.pack_start(self.size_combo, False, False, 0)

        # Preview images
        preview_images_hbox = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=20, homogeneous=False
        )
        preview_vbox.pack_start(preview_images_hbox, True, True, 0)

        # Original image
        original_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        original_vbox.set_hexpand(True)
        original_vbox.set_vexpand(True)
        preview_images_hbox.pack_start(original_vbox, True, True, 0)

        original_label = Gtk.Label()
        original_label.set_markup("<b>Original</b>")
        original_label.set_margin_bottom(2)
        original_vbox.pack_start(original_label, False, False, 0)

        self.original_image = Gtk.Image()
        self.original_image.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
        self.original_image.set_halign(Gtk.Align.START)
        self.original_image.set_valign(Gtk.Align.START)
        original_scrolled = Gtk.ScrolledWindow()
        original_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        original_scrolled.set_hexpand(True)
        original_scrolled.set_vexpand(True)
        original_scrolled.set_halign(Gtk.Align.FILL)
        original_scrolled.set_valign(Gtk.Align.START)
        original_scrolled.set_min_content_width(350)
        original_scrolled.set_min_content_height(260)
        original_scrolled.add(self.original_image)
        original_vbox.pack_start(original_scrolled, True, True, 0)

        # Arrow
        arrow_label = Gtk.Label(label="→")
        arrow_label.set_markup('<span font="24">→</span>')
        preview_images_hbox.pack_start(arrow_label, False, False, 0)

        # Pixelated image
        pixelated_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        pixelated_vbox.set_hexpand(True)
        pixelated_vbox.set_vexpand(True)
        preview_images_hbox.pack_start(pixelated_vbox, True, True, 0)

        pixelated_label = Gtk.Label()
        pixelated_label.set_markup("<b>Pixelated</b>")
        pixelated_label.set_margin_bottom(2)
        pixelated_vbox.pack_start(pixelated_label, False, False, 0)

        self.pixelated_image = Gtk.Image()
        self.pixelated_image.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
        self.pixelated_image.set_halign(Gtk.Align.START)
        self.pixelated_image.set_valign(Gtk.Align.START)
        pixelated_scrolled = Gtk.ScrolledWindow()
        pixelated_scrolled.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC
        )
        pixelated_scrolled.set_hexpand(True)
        pixelated_scrolled.set_vexpand(True)
        pixelated_scrolled.set_halign(Gtk.Align.FILL)
        pixelated_scrolled.set_valign(Gtk.Align.START)
        pixelated_scrolled.set_min_content_width(350)
        pixelated_scrolled.set_min_content_height(260)
        pixelated_scrolled.add(self.pixelated_image)
        pixelated_vbox.pack_start(pixelated_scrolled, True, True, 0)

        # Control Section
        control_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_vbox.pack_start(control_hbox, False, False, 0)

        self.images_label = Gtk.Label(label="Images Found: 0", xalign=0)
        control_hbox.pack_start(self.images_label, True, True, 0)

        self.process_button = Gtk.Button(label="Process All Images")
        self.process_button.connect("clicked", self.on_process_clicked)
        control_hbox.pack_start(self.process_button, False, False, 0)

        # Progress Section
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        main_vbox.pack_start(self.progress_bar, False, False, 0)

        self.progress_label = Gtk.Label(label="Ready", xalign=0)
        main_vbox.pack_start(self.progress_label, False, False, 0)

        self.progress_label.set_text("Ready to process images...")

    def on_input_changed(self, entry):
        self.input_dir = entry.get_text()
        self.scan_input_directory()

    def on_output_changed(self, entry):
        self.output_dir = entry.get_text()

    def on_sizes_changed(self, entry):
        self.sizes_str = entry.get_text()
        self.update_size_combo()

    def on_browse_input(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Select Input Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        dialog.set_current_folder(self.input_dir)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.input_dir = dialog.get_filename()
            self.input_entry.set_text(self.input_dir)
            self.scan_input_directory()
        dialog.destroy()

    def on_browse_output(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Select Output Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        dialog.set_current_folder(self.output_dir)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.output_dir = dialog.get_filename()
            self.output_entry.set_text(self.output_dir)
        dialog.destroy()

    def on_preview_file_changed(self, combo):
        active = combo.get_active_text()
        if active:
            self.current_preview_file = active
            self.update_preview()

    def on_preview_size_changed(self, combo):
        active = combo.get_active_text()
        if active:
            try:
                self.current_preview_size = int(active)
                self.update_preview()
            except ValueError:
                pass

    def scan_input_directory(self):
        input_path = Path(self.input_dir)

        if input_path.exists() and input_path.is_dir():
            self.image_files = [
                f
                for f in input_path.iterdir()
                if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
            ]
            count = len(self.image_files)
            self.images_label.set_text(f"Images Found: {count}")

            # Update file combo
            self.file_combo.remove_all()
            for img_file in self.image_files:
                self.file_combo.append_text(img_file.name)

            if self.image_files:
                self.file_combo.set_active(0)

            # Update size combo
            self.update_size_combo()
        else:
            self.images_label.set_text("Images Found: 0")
            self.file_combo.remove_all()
            self.image_files = []

    def update_size_combo(self):
        sizes = self.parse_sizes()
        self.size_combo.remove_all()
        if sizes:
            for size in sizes:
                self.size_combo.append_text(str(size))
            self.size_combo.set_active(0)

    def parse_sizes(self):
        try:
            sizes = [int(s.strip()) for s in self.sizes_str.split(",") if s.strip()]
            if all(s > 0 for s in sizes):
                return sizes
            return None
        except ValueError:
            return None

    def update_preview(self):
        if not self.current_preview_file or not self.image_files:
            return

        # Find the file
        file_path = None
        for f in self.image_files:
            if f.name == self.current_preview_file:
                file_path = f
                break

        if not file_path or not file_path.exists():
            return

        try:
            # Load and display original
            pixbuf_original = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(file_path), 350, 350, True
            )
            self.original_image.set_from_pixbuf(pixbuf_original)

            # Generate pixelated version
            with Image.open(file_path) as img:
                size = self.current_preview_size
                if size and size > 0:
                    width, height = img.size
                    aspect_ratio = width / height

                    if width > height:
                        new_width = size
                        new_height = int(size / aspect_ratio)
                    else:
                        new_height = size
                        new_width = int(size * aspect_ratio)

                    new_width = max(1, new_width)
                    new_height = max(1, new_height)

                    # Resize down then up
                    img_small = img.resize(
                        (new_width, new_height), resample=Image.Resampling.BILINEAR
                    )
                    img_pixelated = img_small.resize(img.size, Image.Resampling.NEAREST)

                    # Save to temp file and load as pixbuf
                    temp_path = "/tmp/pixelize_preview.png"
                    img_pixelated.save(temp_path)

                    pixbuf_pixelated = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        temp_path, 350, 350, True
                    )
                    self.pixelated_image.set_from_pixbuf(pixbuf_pixelated)
        except Exception as e:
            self.progress_label.set_text(f"Preview error: {e}")

    def on_process_clicked(self, button):
        if self.processing:
            return

        # Validate inputs
        input_path = Path(self.input_dir)
        if not input_path.exists():
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=f"Input directory '{input_path}' does not exist.",
            )
            dialog.run()
            dialog.destroy()
            return

        sizes = self.parse_sizes()
        if not sizes:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Invalid pixelation sizes. Please enter comma-separated positive integers.",
            )
            dialog.run()
            dialog.destroy()
            return

        if not self.image_files:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No image files found in the input directory.",
            )
            dialog.run()
            dialog.destroy()
            return

        # Start processing
        self.processing = True
        self.process_button.set_sensitive(False)
        self.progress_label.set_text("Starting batch processing...")

        # Start processing thread
        thread = threading.Thread(
            target=self.process_images_thread,
            args=(input_path, Path(self.output_dir), sizes),
        )
        thread.daemon = True
        thread.start()

    def process_images_thread(self, input_dir, output_dir, sizes):
        try:
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            total = len(self.image_files)
            for idx, file_path in enumerate(self.image_files):
                GLib.idle_add(
                    self.update_progress, idx / total, f"Processing {idx}/{total}"
                )

                # Use the pixelate function from main.py
                try:
                    pixelate(file_path, output_dir, sizes)
                except Exception as e:
                    GLib.idle_add(self.progress_label.set_text, f"Error: {e}")

                GLib.idle_add(
                    self.update_progress,
                    (idx + 1) / total,
                    f"Processed {idx + 1}/{total} images",
                )

            GLib.idle_add(
                self.progress_label.set_text,
                f"Processing complete! Processed {total} images.",
            )
            GLib.idle_add(self.processing_done)
        except Exception as e:
            GLib.idle_add(self.progress_label.set_text, f"Error: {e}")
            GLib.idle_add(self.processing_done)

    def update_progress(self, fraction, text):
        self.progress_bar.set_fraction(fraction)
        self.progress_label.set_text(text)
        return False

    def processing_done(self):
        self.processing = False
        self.process_button.set_sensitive(True)
        self.progress_label.set_text("Complete")
        return False


def main():
    app = PixelizeGTKApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
