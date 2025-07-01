# window.py
from gi.repository import Adw, Gtk, GLib
import os
import pwd
import urllib.request
import threading
import subprocess


# Función independiente para obtener el nombre de usuario
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

    # Añade estas declaraciones para las vistas
    home_view = Gtk.Template.Child()
    host_view = Gtk.Template.Child()

    # Añade estos nuevos elementos
    switch_facebook = Gtk.Template.Child()
    switch_steven = Gtk.Template.Child()
    button_apply = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Conectar señales
        self.show_sidebar_button.connect("toggled", self.on_sidebar_toggle)
        self.home_button.connect("toggled", self.on_navigation_toggled)
        self.host_button.connect("toggled", self.on_navigation_toggled)
        # Conectar Boton Apply
        self.button_apply.connect("clicked", self.on_apply_clicked)

        # Configurar nombres de las vistas en el stack
        self.main_stack.add_named(self.home_view, "home_view")
        self.main_stack.add_named(self.host_view, "host_view")

        # Establecer vista inicial
        self.main_stack.set_visible_child_name("home_view")
        # Inicializar estado de progreso
        self.progress_bar.set_visible(False)

        # Obtener y establecer el nombre de usuario CORREGIDO
        user = get_username()  # Llamada correcta a la función
        self.nombre.set_label(f"Usuario: {user}")  # f-string corregido

    def on_sidebar_toggle(self, button):
        """Alternar visibilidad de la barra lateral"""
        self.split_view.set_show_sidebar(button.get_active())

    def on_navigation_toggled(self, button):
        """Cambiar de vista según el botón seleccionado"""
        if button.get_active():
            if button == self.home_button:
                self.main_stack.set_visible_child_name("home_view")
            elif button == self.host_button:
                self.main_stack.set_visible_child_name("host_view")

    def on_apply_clicked(self, button):
        """Manejador para el botón Apply"""
        # Verificar si ambos switches están activados
        if self.switch_steven.get_active():
            # Deshabilitar botón durante la descarga
            self.button_apply.set_sensitive(False)
            self.progress_bar.set_visible(True)
            self.progress_bar.set_fraction(0.0)

            # Ejecutar descarga en segundo plano
            threading.Thread(
                target=self.download_hosts_file,
                daemon=True
            ).start()
        else:
            # Mostrar mensaje si no están ambos activados
            print("No es Steve")
            self.show_message("Debes activar Steven para descargar")

    def download_hosts_file(self):
        """Descarga el archivo en segundo plano"""
        url = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
        destino = os.path.join(os.path.expanduser("~"), "hosts")

        try:
            # Función para actualizar progreso
            def update_progress(count, block_size, total_size):
                if total_size > 0:
                    progress = min(1.0, count * block_size / total_size)
                    GLib.idle_add(self.progress_bar.set_fraction, progress)

            # Descargar archivo
            urllib.request.urlretrieve(
                url,
                destino,
                reporthook=update_progress
            )

            # Completado con éxito
            GLib.idle_add(self.on_download_complete, destino)

        except Exception as e:
            GLib.idle_add(self.on_download_error, str(e))

    def on_download_complete(self, destino):
        """Acciones al completar la descarga"""
        self.progress_bar.set_fraction(1.0)
        self.show_message(f"Archivo descargado en: {destino}")
        self.button_apply.set_sensitive(True)

        # Ocultar progreso después de 2 segundos
        GLib.timeout_add_seconds(2, self.hide_progress)

    def on_download_error(self, error):
        """Manejo de errores de descarga"""
        self.show_message(f"Error: {error}")
        self.progress_bar.set_visible(False)
        self.button_apply.set_sensitive(True)

    def hide_progress(self):
        """Oculta la barra de progreso"""
        self.progress_bar.set_visible(False)
        return False  # Para detener el timeout

    def show_message(self, message):
        """Muestra un mensaje toast al usuario"""
        toast = Adw.Toast.new(message)
        overlay = self.get_content()  # Obtener el contenedor AdwToastOverlay
        overlay.add_toast(toast)
    
