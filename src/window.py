# window.py
from gi.repository import Adw, Gtk, GLib, Gio
import os
import pwd
import urllib.request
import threading
import tempfile

def get_username():
    try:
        return pwd.getpwuid(os.getuid()).pw_name
    except Exception:
        return "Usuario desconocido"

@Gtk.Template(resource_path='/org/gnome/BlockHost/window.ui')
class ProyectoInnovacionWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ProyectoInnovacionWindow'

    split_view = Gtk.Template.Child()
    show_sidebar_button = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    home_button = Gtk.Template.Child()
    host_button = Gtk.Template.Child()
    nombre = Gtk.Template.Child()
    home_view = Gtk.Template.Child()
    host_view = Gtk.Template.Child()
    switch_facebook = Gtk.Template.Child()
    switch_easylist = Gtk.Template.Child()
    switch_steven = Gtk.Template.Child()
    button_apply = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gio.Settings.new("org.gnome.BlockHost")

        self.host_sources = {
            "steven": {
                "switch": self.switch_steven,
                "url": "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
                "gsettings_key": "switch-steven-active"
            },
            "facebook": {
                "switch": self.switch_facebook,
                "url": "https://raw.githubusercontent.com/anudeepND/blacklist/master/facebook.txt",
                "gsettings_key": "switch-facebook-active"
            },
            "easylist": {
                "switch": self.switch_easylist,
                "url": "https://gist.githubusercontent.com/thelabcat/21301002ca0906759617970235693627/raw/4488fac71f14b4f4f4fedfbe52ebcc2a9ce88124/easylist_for_pihole_hosts.txt",
                "gsettings_key": "switch-easylist-active"
            }

        }

        for source in self.host_sources.values():
            self.settings.bind(
                source["gsettings_key"],
                source["switch"],
                "active",
                Gio.SettingsBindFlags.DEFAULT
            )

        self.show_sidebar_button.connect("toggled", self.on_sidebar_toggle)
        self.home_button.connect("toggled", self.on_navigation_toggled)
        self.host_button.connect("toggled", self.on_navigation_toggled)
        self.button_apply.connect("clicked", self.on_apply_clicked)

        self.main_stack.add_named(self.home_view, "home_view")
        self.main_stack.add_named(self.host_view, "host_view")
        self.main_stack.set_visible_child_name("home_view")
        self.progress_bar.set_visible(False)
        self.nombre.set_label(f"Usuario: {get_username()}")

    def on_sidebar_toggle(self, button):
        self.split_view.set_show_sidebar(button.get_active())

    def on_navigation_toggled(self, button):
        if button.get_active():
            if button == self.home_button:
                self.main_stack.set_visible_child_name("home_view")
            elif button == self.host_button:
                self.main_stack.set_visible_child_name("host_view")

    def on_apply_clicked(self, button):
        active_urls = [
            source["url"] for source in self.host_sources.values()
            if source["switch"].get_active()
        ]

        if not active_urls:
            self.show_message("Debes activar al menos un switch para descargar.")
            return

        self.button_apply.set_sensitive(False)
        self.progress_bar.set_visible(True)
        self.progress_bar.set_fraction(0.0)

        threading.Thread(
            target=self.download_and_combine_hosts,
            args=(active_urls,),
            daemon=True
        ).start()

    def download_and_combine_hosts(self, urls):
        temp_files = []
        total_progress = 0
        progress_per_url = 1.0 / len(urls)

        try:
            for i, url in enumerate(urls):
                with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                    temp_files.append(temp_file.name)

                    def update_progress(count, block_size, total_size):
                        if total_size > 0:
                            progress = (count * block_size / total_size) * progress_per_url
                            current_total = total_progress + progress
                            GLib.idle_add(self.progress_bar.set_fraction, current_total)

                    urllib.request.urlretrieve(url, temp_file.name, reporthook=update_progress)
                    total_progress += progress_per_url
                    GLib.idle_add(self.progress_bar.set_fraction, total_progress)

            destino = os.path.join(os.path.expanduser("~"), "mi_hosts")
            with open(destino, "w") as outfile:
                for temp_path in temp_files:
                    with open(temp_path, "r") as infile:
                        outfile.write(infile.read())
                    outfile.write("\n")

            GLib.idle_add(self.on_download_complete, destino)

        except Exception as e:
            GLib.idle_add(self.on_download_error, str(e))
        finally:
            for temp_path in temp_files:
                os.remove(temp_path)

    def on_download_complete(self, destino):
        self.progress_bar.set_fraction(1.0)
        self.show_message(f"Archivo de hosts actualizado en: {destino}")
        self.button_apply.set_sensitive(True)
        GLib.timeout_add_seconds(2, self.hide_progress)

    def on_download_error(self, error):
        self.show_message(f"Error: {error}")
        self.progress_bar.set_visible(False)
        self.button_apply.set_sensitive(True)

    def hide_progress(self):
        self.progress_bar.set_visible(False)
        return False

    def show_message(self, message):
        toast = Adw.Toast.new(message)
        overlay = self.get_content()
        overlay.add_toast(toast)
    
