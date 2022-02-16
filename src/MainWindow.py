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
        self.output_dir = os.path.join(os.path.expanduser("~"), "imagop-output")
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
        self.dd_info_label = self.GtkBuilder.get_object("ui_dd_info_label")
        self.settings_button = self.GtkBuilder.get_object("ui_settings_button")
        self.settings_button_image = self.GtkBuilder.get_object("ui_settings_button_image")
        self.jpeg_adjusment = self.GtkBuilder.get_object("ui_jpeg_adjusment")

        self.iconview.enable_model_drag_dest([Gtk.TargetEntry.new('text/uri-list', 0, 0)],
                                             Gdk.DragAction.DEFAULT | Gdk.DragAction.COPY)
        self.iconview.connect("drag-data-received", self.drag_data_received)

    def user_settings(self):
        self.UserSettings = UserSettings()
        self.UserSettings.createDefaultConfig()
        self.UserSettings.readConfig()

    def drag_data_received(self, treeview, context, posx, posy, selection, info, timestamp):
        if self.dd_info_label.get_visible():
            self.dd_info_label.set_visible(False)
        for image in selection.get_uris():
            name = "{}".format(urllib.parse.unquote(image.split("file://")[1]))
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
        treeiter = self.liststore.get_iter(path)
        self.liststore.remove(treeiter)
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
            if not os.path.isdir(self.output_dir):
                os.makedirs(self.output_dir)
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
                    self.png_images.append(org_image)
                elif Image.open(org_image).format == "JPEG":
                    self.jpg_images.append(org_image)

            self.p_queue = len(self.png_images)
            self.z_queue = self.p_queue
            self.jpg_queue = len(self.jpg_images)

            self.main_stack.set_visible_child_name("splash")
            self.select_image.set_sensitive(False)
            self.settings_button.set_sensitive(False)

            for png_image in self.png_images:
                command = ["/usr/bin/pngquant", "--quality=80-98", "--skip-if-larger", "--force", "--strip", "--speed",
                           "1",
                           "--output", os.path.join(self.output_dir,
                                                    os.path.basename(os.path.splitext(png_image)[0]) + "-pngquant.png"),
                           png_image]

                self.start_p_process(command)

            for jpg_image in self.jpg_images:
                self.jp = threading.Thread(target=self.optimize_jpg, args=(jpg_image,))
                self.jp.daemon = True
                self.jp.start()

    def optimize_jpg(self, jpg_image):
        foo = Image.open(jpg_image)
        foo = foo.resize(foo.size, Image.ANTIALIAS)
        foo.save(os.path.join(self.output_dir,
                              os.path.basename(os.path.splitext(jpg_image)[0]) + "-optimized.jpg"),
                 optimize=True, quality=self.UserSettings.config_jpeg_quality)

        self.jpg_queue -= 1

        if self.z_queue <= 0 and self.jpg_queue <= 0:
            self.main_stack.set_visible_child_name("complete")
            self.settings_button.set_sensitive(True)
            self.notify()
            for jpg_image in self.jpg_images:
                optimized = os.path.join(self.output_dir,
                                         os.path.basename(os.path.splitext(jpg_image)[0]) + "-optimized.jpg")
                self.done_info.get_buffer().insert(self.done_info.get_buffer().get_end_iter(),
                                                   "{} | {} => {}\n".format(
                                                       os.path.basename(optimized), self.get_size(jpg_image),
                                                       self.get_size(optimized)))

    def on_ui_open_output_button_clicked(self, button):
        try:
            subprocess.check_call(["xdg-open", self.output_dir])
            return True
        except subprocess.CalledProcessError:
            print("error opening " + self.output_dir)
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
        start, end = self.done_info.get_buffer().get_bounds()
        self.done_info.get_buffer().delete(start, end)

    def on_ui_settings_button_clicked(self, button):
        self.settings_counter += 1
        if self.settings_counter % 2 == 1:
            self.old_page = self.main_stack.get_visible_child_name()
            self.main_stack.set_visible_child_name("settings")
            self.settings_button_image.set_from_icon_name("user-home-symbolic", Gtk.IconSize.BUTTON)
            self.jpeg_adjusment.set_value(self.UserSettings.config_jpeg_quality)
        else:
            self.main_stack.set_visible_child_name(self.old_page)
            self.settings_button_image.set_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)

    def on_ui_jpeg_adjusment_value_changed(self, adjusment):
        user_jpeg_quality = self.UserSettings.config_jpeg_quality
        if int(adjusment.get_value()) != user_jpeg_quality:
            self.UserSettings.writeConfig(int(adjusment.get_value()))
            self.user_settings()

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
                pngquanted = os.path.join(self.output_dir,
                                          os.path.basename(os.path.splitext(png_image)[0]) + "-pngquant.png")
                zopflipnged = os.path.join(self.output_dir,
                                           os.path.basename(os.path.splitext(png_image)[0]) + "-optimized.png")

                # if pngquanted file is bigger than org file then we use org file
                if not os.path.isfile(pngquanted):
                    shutil.copy2(png_image, pngquanted)
                command = ["/usr/bin/zopflipng", "-y", "--lossy_transparent", pngquanted, zopflipnged]
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

                optimized = os.path.join(self.output_dir,
                                         os.path.basename(os.path.splitext(png_image)[0]) + "-optimized.png")

                self.done_info.get_buffer().insert(self.done_info.get_buffer().get_end_iter(),
                                                   "{} | {} => {}\n".format(
                                                       os.path.basename(optimized), self.get_size(png_image),
                                                       self.get_size(optimized)))

                pngquanted = os.path.join(self.output_dir,
                                          os.path.basename(os.path.splitext(png_image)[0]) + "-pngquant.png")
                if os.path.isfile(pngquanted):
                    os.remove(pngquanted)

            for jpg_image in self.jpg_images:
                optimized = os.path.join(self.output_dir,
                                         os.path.basename(os.path.splitext(jpg_image)[0]) + "-optimized.jpg")
                self.done_info.get_buffer().insert(self.done_info.get_buffer().get_end_iter(),
                                                   "{} | {} => {}\n".format(
                                                       os.path.basename(optimized), self.get_size(jpg_image),
                                                       self.get_size(optimized)))

    def notify(self):
        if Notify.is_initted():
            Notify.uninit()

        message = _("Image optimization completed.")

        Notify.init("imagop")
        notification = Notify.Notification.new(summary="ImagOP", body=message, icon="imagop")
        notification.show()
