#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 19:05:13 2022

@author: fatihaltun
"""

import locale
import os
import shutil
import subprocess
import threading
import urllib.parse
from locale import gettext as _

import gi
from PIL import Image

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GObject, GLib, GdkPixbuf, Gdk, Notify

from UserSettings import  UserSettings

locale.bindtextdomain('imagop', '/usr/share/locale')
locale.textdomain('imagop')


class MainWindow(object):
    def __init__(self, application):
        self.Application = application

        self.main_window_ui_filename = os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        try:
            self.GtkBuilder = Gtk.Builder.new_from_file(self.main_window_ui_filename)
            self.GtkBuilder.connect_signals(self)
        except GObject.GError:
            print("Error reading GUI file: " + self.main_window_ui_filename)
            raise

        self.define_components()
        self.user_settings()

        self.main_window.set_application(application)

        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.about_dialog.set_version(version)
        except:
            pass

        self.iconview.set_pixbuf_column(0)
        self.iconview.set_text_column(1)
        self.UserSettings.config_save_path = self.UserSettings.config_save_path
        self.org_images = []
        self.png_images = []
        self.jpg_images = []
        self.p_queue = 0
        self.z_queue = 0
        self.settings_counter = 0
        self.old_page = "select"

        self.main_window.show_all()

    def define_components(self):
        self.main_window = self.GtkBuilder.get_object("ui_main_window")
        self.about_dialog = self.GtkBuilder.get_object("ui_about_dialog")
        self.iconview = self.GtkBuilder.get_object("ui_iconview")
        self.liststore = self.GtkBuilder.get_object("ui_liststore")
        self.main_stack = self.GtkBuilder.get_object("ui_main_stack")
        self.select_image = self.GtkBuilder.get_object("ui_select_image")
        self.done_info = self.GtkBuilder.get_object("ui_done_info")
        self.done_listbox = self.GtkBuilder.get_object("ui_done_listbox")
        self.dd_info_label = self.GtkBuilder.get_object("ui_dd_info_label")
        self.settings_button = self.GtkBuilder.get_object("ui_settings_button")
        self.defaults_button = self.GtkBuilder.get_object("ui_defaults_button")
        self.settings_button_image = self.GtkBuilder.get_object("ui_settings_button_image")
        self.jpeg_adjusment = self.GtkBuilder.get_object("ui_jpeg_adjusment")
        self.save_path_button = self.GtkBuilder.get_object("ui_save_path_button")
        self.overwrite_switch = self.GtkBuilder.get_object("ui_overwrite_switch")
        self.save_path_box = self.GtkBuilder.get_object("ui_save_path_box")

        self.iconview.enable_model_drag_dest([Gtk.TargetEntry.new('text/uri-list', 0, 0)],
                                             Gdk.DragAction.DEFAULT | Gdk.DragAction.COPY)
        self.iconview.connect("drag-data-received", self.drag_data_received)

        self.menu = Gtk.Menu()
        self.menu_item1 = Gtk.ImageMenuItem(label=_("Remove from list"))
        self.menu_item1.set_image(Gtk.Image.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON))
        self.menu_item1.connect("activate", self.on_iconview_rcmenu_del_activated, self.iconview)
        self.menu.append(self.menu_item1)
        self.menu.show_all()

    def on_ui_iconview_button_press_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            path = self.iconview.get_path_at_pos(event.x, event.y)
            if path != None:
                if event.button == 3:
                    self.iconview.select_path(path)
                    self.right_index = path
                    self.menu.popup(None, None, None,None, event.button, event.time)

    def on_iconview_rcmenu_del_activated(self, item, widget):
        treeiter = self.liststore.get_iter(self.right_index)
        self.liststore.remove(treeiter)
        del self.org_images[self.right_index.get_indices()[0]]

        for s in self.iconview.get_selected_items():
            self.liststore.remove(self.liststore.get_iter(s))
            del self.org_images[s.get_indices()[0]]

    def on_ui_iconview_key_press_event(self, widget, event):

        if event.keyval == Gdk.KEY_Delete:
            for s in self.iconview.get_selected_items():
                self.liststore.remove(self.liststore.get_iter(s))
                del self.org_images[s.get_indices()[0]]

    def user_settings(self):
        self.UserSettings = UserSettings()
        self.UserSettings.createDefaultConfig()
        self.UserSettings.readConfig()

    def drag_data_received(self, treeview, context, posx, posy, selection, info, timestamp):
        if self.dd_info_label.get_visible():
            self.dd_info_label.set_visible(False)
        for image in selection.get_uris():
            try:
                name = "{}".format(urllib.parse.unquote(image.split("file://")[1]))
            except Exception as e:
                print("{}".format(e))
                continue
            try:
                img = Image.open(name)
            except IsADirectoryError:
                print("{} is a directory, so skipping for now.".format(name))
                continue
            except Exception as e:
                print("{}".format(e))
                continue

            if (img.format == "JPEG" or img.format == "PNG") and name not in self.org_images:

                try:
                    icon = GdkPixbuf.Pixbuf.new_from_file_at_size(name, 100, 100)
                    self.liststore.append([icon, os.path.basename(name)])
                    self.org_images.append(name)
                except gi.repository.GLib.Error:
                    print("{} is not an image so skipped.".format(name))

    def on_ui_iconview_item_activated(self, icon_view, path):
        self.liststore.remove(self.liststore.get_iter(path))
        del self.org_images[path.get_indices()[0]]

    def on_ui_about_button_clicked(self, button):
        self.about_dialog.run()
        self.about_dialog.hide()

    def on_ui_selectimage_clicked(self, button):
        file_chooser = Gtk.FileChooserDialog(title=_("Select Image(s)"), parent=self.main_window,
                                             action=Gtk.FileChooserAction.OPEN)
        file_chooser.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        file_chooser.add_button(_("Open"), Gtk.ResponseType.ACCEPT).get_style_context().add_class("suggested-action")
        file_chooser.set_select_multiple(True)

        filter_all = Gtk.FileFilter()
        filter_all.set_name(_("All supported files"))
        filter_all.add_mime_type("image/png")
        filter_all.add_mime_type("image/jpg")
        filter_all.add_mime_type("image/jpeg")

        filter_png = Gtk.FileFilter()
        filter_png.set_name(_("PNG files"))
        filter_png.add_mime_type("image/png")

        filter_jpg = Gtk.FileFilter()
        filter_jpg.set_name(_("JPG/JPEG files"))
        filter_jpg.add_mime_type("image/jpg")
        filter_jpg.add_mime_type("image/jpeg")

        file_chooser.add_filter(filter_all)
        file_chooser.add_filter(filter_png)
        file_chooser.add_filter(filter_jpg)
        file_chooser.set_filter(filter_all)

        response = file_chooser.run()
        if response == Gtk.ResponseType.ACCEPT:
            self.image_to_ui(file_chooser.get_filenames())
        file_chooser.destroy()

        if self.dd_info_label.get_visible():
            self.dd_info_label.set_visible(False)

        if self.main_stack.get_visible_child_name() == "settings":
            self.main_stack.set_visible_child_name("select")
            self.settings_counter +=1
            self.settings_button_image.set_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)

    def image_to_ui(self, filenames):
        for image in filenames:
            name = "{}".format(image)

            try:
                img = Image.open(name)
            except IsADirectoryError:
                print("{} is a directory, so skipping for now.".format(name))
                continue
            except Exception as e:
                print("{}".format(e))
                continue

            if (img.format == "JPEG" or img.format == "PNG") and name not in self.org_images:
                if name not in self.org_images:
                    try:
                        icon = GdkPixbuf.Pixbuf.new_from_file_at_size(name, 100, 100)
                        self.liststore.append([icon, os.path.basename(name)])
                        self.org_images.append(name)
                    except gi.repository.GLib.Error:
                        print("{} is not an image so skipped".format(name))

    def control_output_directory(self):
        try:
            if not os.path.isdir(self.UserSettings.config_save_path):
                os.makedirs(self.UserSettings.config_save_path)
        except Exception as e:
            print("{}".format(e))
            return False
        return True

    def get_size(self, filepath):
        size = 0
        if os.path.isfile(filepath):
            size = os.stat(filepath).st_size
            if type(size) is int:
                size = size / 1024
                if size > 1024:
                    size = "{:.2f} MiB".format(float(size / 1024))
                else:
                    size = "{:.2f} KiB".format(float(size))
            return size
        return size

    def on_ui_optimize_button_clicked(self, button):
        if self.control_output_directory() and self.org_images:

            for org_image in self.org_images:
                if Image.open(org_image).format == "PNG":
                    self.png_images.append({"name": org_image, "size": self.get_size(org_image)})
                elif Image.open(org_image).format == "JPEG":
                    self.jpg_images.append({"name": org_image, "size": self.get_size(org_image)})

            self.p_queue = len(self.png_images)
            self.z_queue = self.p_queue
            self.jpg_queue = len(self.jpg_images)

            self.main_stack.set_visible_child_name("splash")
            self.select_image.set_sensitive(False)
            self.settings_button.set_sensitive(False)

            for png_image in self.png_images:
                if self.UserSettings.config_overwrite:
                    save_path = png_image["name"]
                else:
                    save_path = os.path.join(self.UserSettings.config_save_path,
                                                    os.path.basename(os.path.splitext(png_image["name"])[0]) + "-optimized.png")

                command = ["/usr/bin/pngquant", "--quality=80-98", "--skip-if-larger", "--force", "--strip", "--speed",
                           "1", "--output", save_path, png_image["name"]]

                self.start_p_process(command)

            for jpg_image in self.jpg_images:
                self.jp = threading.Thread(target=self.optimize_jpg, args=(jpg_image,))
                self.jp.daemon = True
                self.jp.start()

    def optimize_jpg(self, jpg_image):
        foo = Image.open(jpg_image["name"])
        foo = foo.resize(foo.size, Image.ANTIALIAS)
        if self.UserSettings.config_overwrite:
            save_name = jpg_image["name"]
        else:
            save_name = os.path.join(self.UserSettings.config_save_path,
                              os.path.basename(os.path.splitext(jpg_image["name"])[0]) + "-optimized.jpg")

        foo.save(save_name, optimize=True, quality=self.UserSettings.config_jpeg_quality)

        self.jpg_queue -= 1

        if self.z_queue <= 0 and self.jpg_queue <= 0:
            GLib.idle_add(self.main_stack.set_visible_child_name, "complete")
            GLib.idle_add(self.settings_button.set_sensitive, True)
            self.notify()
            for jpg_img in self.jpg_images:
                if self.UserSettings.config_overwrite:
                    optimized = jpg_img["name"]
                else:
                    optimized = os.path.join(self.UserSettings.config_save_path,
                                             os.path.basename(os.path.splitext(jpg_img["name"])[0]) + "-optimized.jpg")

                thumb = Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(optimized, 100, 100))
                info_label = Gtk.Label.new()
                info_label.set_text("{} | {} => {}".format(os.path.basename(optimized), jpg_img["size"], self.get_size(optimized)))
                info_label.props.valign = Gtk.Align.CENTER
                info_label.props.halign = Gtk.Align.CENTER
                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                box.set_margin_start(5)
                box.set_margin_end(5)
                box.pack_start(thumb, False, True, 0)
                box.pack_start(info_label, False, True, 0)
                self.done_listbox.add(box)
            self.done_listbox.show_all()

    def on_ui_open_output_button_clicked(self, button):
        if self.UserSettings.config_overwrite:
            folders = []
            folder = ""
            for jpg_image in self.jpg_images:
                if os.path.dirname(jpg_image["name"]) not in folders:
                    folders.append(os.path.dirname(jpg_image["name"]))
            for png_image in self.png_images:
                if os.path.dirname(png_image["name"]) not in folders:
                    folders.append(os.path.dirname(png_image["name"]))
            try:
                for folder in folders:
                    subprocess.check_call(["xdg-open", folder])
            except subprocess.CalledProcessError:
                print("error opening " + folder)
        else:
            try:
                subprocess.check_call(["xdg-open", self.UserSettings.config_save_path])
                return True
            except subprocess.CalledProcessError:
                print("error opening " + self.UserSettings.config_save_path)
                return False

    def on_ui_optimize_new_button_clicked(self, button):
        self.main_stack.set_visible_child_name("select")
        self.select_image.set_sensitive(True)
        self.settings_button.set_sensitive(True)
        self.z_queue = 0
        self.p_queue = 0
        self.org_images = []
        self.png_images = []
        self.jpg_images = []
        self.liststore.clear()
        for row in self.done_listbox:
            self.done_listbox.remove(row)

    def on_ui_settings_button_clicked(self, button):
        self.settings_counter += 1
        if self.settings_counter % 2 == 1:
            self.old_page = self.main_stack.get_visible_child_name()
            self.main_stack.set_visible_child_name("settings")
            self.settings_button_image.set_from_icon_name("user-home-symbolic", Gtk.IconSize.BUTTON)
            self.jpeg_adjusment.set_value(self.UserSettings.config_jpeg_quality)
            self.save_path_button.set_uri(self.UserSettings.config_save_path)
            self.overwrite_switch.set_state(self.UserSettings.config_overwrite)
            if self.UserSettings.config_overwrite:
                self.save_path_box.set_visible(False)
            else:
                self.save_path_box.set_visible(True)
            if self.UserSettings.config_jpeg_quality != self.UserSettings.default_jpeg_quality or \
                    self.UserSettings.config_save_path != self.UserSettings.default_save_path or \
                    self.UserSettings.default_overwrite != self.UserSettings.config_overwrite:
                self.defaults_button.set_sensitive(True)
            else:
                self.defaults_button.set_sensitive(False)
        else:
            self.main_stack.set_visible_child_name(self.old_page)
            self.settings_button_image.set_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)

    def on_ui_jpeg_adjusment_value_changed(self, adjusment):
        user_jpeg_quality = self.UserSettings.config_jpeg_quality
        if int(adjusment.get_value()) != user_jpeg_quality:
            self.UserSettings.writeConfig(int(adjusment.get_value()), self.UserSettings.config_save_path,
                                          self.UserSettings.config_overwrite)
            self.user_settings()
        if self.UserSettings.config_jpeg_quality != self.UserSettings.default_jpeg_quality or \
                self.UserSettings.config_save_path != self.UserSettings.default_save_path or \
                self.UserSettings.default_overwrite != self.UserSettings.config_overwrite:
            self.defaults_button.set_sensitive(True)
        else:
            self.defaults_button.set_sensitive(False)

    def on_ui_save_path_button_file_set(self, button):
        path = "{}".format(urllib.parse.unquote(button.get_uri().split("file://")[1]))
        print(path)
        user_save_path = self.UserSettings.config_save_path

        if path != user_save_path:
            self.UserSettings.writeConfig(self.UserSettings.config_jpeg_quality, path, self.UserSettings.config_overwrite)
            self.user_settings()
        if self.UserSettings.config_jpeg_quality != self.UserSettings.default_jpeg_quality or \
                self.UserSettings.config_save_path != self.UserSettings.default_save_path or \
                self.UserSettings.default_overwrite != self.UserSettings.config_overwrite:
            self.defaults_button.set_sensitive(True)
        else:
            self.defaults_button.set_sensitive(False)

    def on_ui_overwrite_switch_state_set(self, switch, state):
        user_overwrite = self.UserSettings.config_overwrite

        if state != user_overwrite:
            self.UserSettings.writeConfig(self.UserSettings.config_jpeg_quality, self.UserSettings.config_save_path,
                                          state)
            self.user_settings()
            if state:
                self.save_path_box.set_visible(False)
            else:
                self.save_path_box.set_visible(True)
        if self.UserSettings.config_jpeg_quality != self.UserSettings.default_jpeg_quality or \
                self.UserSettings.config_save_path != self.UserSettings.default_save_path or \
                self.UserSettings.default_overwrite != self.UserSettings.config_overwrite:
            self.defaults_button.set_sensitive(True)
        else:
            self.defaults_button.set_sensitive(False)

    def on_ui_defaults_button_clicked(self, button):
        self.UserSettings.createDefaultConfig(force=True)
        self.user_settings()
        self.jpeg_adjusment.set_value(self.UserSettings.config_jpeg_quality)
        self.save_path_button.set_uri(self.UserSettings.config_save_path)
        self.overwrite_switch.set_state(self.UserSettings.config_overwrite)
        self.save_path_box.set_visible(True)
        self.defaults_button.set_sensitive(False)

    def start_p_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_p_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_p_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_p_process_exit)

        return pid

    def on_p_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def on_p_process_stderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def on_p_process_exit(self, pid, status):
        self.p_queue -= 1
        if self.p_queue <= 0:
            print("pngquant processes done, starting zopflipng processes")
            for png_image in self.png_images:

                if self.UserSettings.config_overwrite:
                    save_name = png_image["name"]
                else:
                    save_name = os.path.join(self.UserSettings.config_save_path,
                                             os.path.basename(os.path.splitext(png_image["name"])[0]) + "-optimized.png")
                command = ["/usr/bin/zopflipng", "-y", "--lossy_transparent", save_name, save_name]
                self.start_z_process(command)

    def start_z_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_z_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_z_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_z_process_exit)

        return pid

    def on_z_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def on_z_process_stderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def on_z_process_exit(self, pid, status):
        self.z_queue -= 1
        if self.z_queue <= 0:
            self.main_stack.set_visible_child_name("complete")
            self.settings_button.set_sensitive(True)
            self.notify()
            for png_image in self.png_images:

                if self.UserSettings.config_overwrite:
                    optimized = png_image["name"]
                else:
                    optimized = os.path.join(self.UserSettings.config_save_path,
                                             os.path.basename(os.path.splitext(png_image["name"])[0]) + "-optimized.png")

                thumb = Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(optimized, 100, 100))
                info_label = Gtk.Label.new()
                info_label.set_text("{} | {} => {}".format(os.path.basename(optimized), png_image["size"],
                                                           self.get_size(optimized)))
                info_label.props.valign = Gtk.Align.CENTER
                info_label.props.halign = Gtk.Align.CENTER
                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                box.set_margin_start(5)
                box.set_margin_end(5)
                box.pack_start(thumb, False, True, 0)
                box.pack_start(info_label, False, True, 0)
                self.done_listbox.add(box)

            self.done_listbox.show_all()

            for jpg_image in self.jpg_images:

                if self.UserSettings.config_overwrite:
                    optimized = jpg_image["name"]
                else:
                    optimized = os.path.join(self.UserSettings.config_save_path,
                                             os.path.basename(os.path.splitext(jpg_image["name"])[0]) + "-optimized.jpg")

                thumb = Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(optimized, 100, 100))
                info_label = Gtk.Label.new()
                info_label.set_text("{} | {} => {}".format(os.path.basename(optimized), jpg_image["size"], self.get_size(optimized)))

                info_label.props.valign = Gtk.Align.CENTER
                info_label.props.halign = Gtk.Align.CENTER
                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                box.set_margin_start(5)
                box.set_margin_end(5)
                box.pack_start(thumb, False, True, 0)
                box.pack_start(info_label, False, True, 0)
                self.done_listbox.add(box)
            self.done_listbox.show_all()

    def notify(self):
        if Notify.is_initted():
            Notify.uninit()

        message = _("Image optimization completed.")

        Notify.init("imagop")
        notification = Notify.Notification.new(summary="ImagOP", body=message, icon="imagop")
        notification.show()
