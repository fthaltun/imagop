#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 19:05:13 2022

@author: fatihaltun
"""

import locale
from locale import gettext as _
import os
import shutil
import subprocess

import gi

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GObject, GLib, GdkPixbuf

locale.bindtextdomain('image-optimizer', '/usr/share/locale')
locale.textdomain('image-optimizer')


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

        self.main_window.set_application(application)

        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.about_dialog.set_version(version)
        except:
            pass

        self.about_dialog.set_program_name(_("Image Optimizer"))

        self.iconview.set_pixbuf_column(0)
        self.iconview.set_text_column(1)
        self.output_dir = os.path.join(os.path.expanduser("~"), "image-optimizer-output")
        self.org_images = []
        self.p_queue = 0
        self.z_queue = 0

        self.main_window.show_all()

    def define_components(self):
        self.main_window = self.GtkBuilder.get_object("ui_main_window")
        self.about_dialog = self.GtkBuilder.get_object("ui_about_dialog")
        self.filechooser_dialog = self.GtkBuilder.get_object("ui_filechooser_dialog")
        self.filechooser_button = self.GtkBuilder.get_object("ui_filechooser_button")
        self.iconview = self.GtkBuilder.get_object("ui_iconview")
        self.liststore = self.GtkBuilder.get_object("ui_liststore")
        self.main_stack = self.GtkBuilder.get_object("ui_main_stack")
        self.select_image = self.GtkBuilder.get_object("ui_selectimage")
        self.done_info = self.GtkBuilder.get_object("ui_done_info")

    def on_ui_about_button_clicked(self, button):
        self.about_dialog.run()
        self.about_dialog.hide()

    def on_ui_selectimage_button_clicked(self, button):
        self.image_to_ui()

    def on_ui_filechooser_dialog_file_activated(self, widget):
        self.image_to_ui()

    def on_ui_selectcancel_button_clicked(self, button):
        self.filechooser_dialog.hide()

    def on_ui_selectimage_clicked(self, button):
        self.filechooser_dialog.run()
        self.filechooser_dialog.hide()

    def image_to_ui(self):
        for image in self.filechooser_dialog.get_filenames():
            name = "{}".format(image)
            # currently only png is supported
            if name.lower().endswith(".png"):
                if name not in self.org_images:
                    try:
                        icon = GdkPixbuf.Pixbuf.new_from_file_at_size(image, 100, 100)
                        self.liststore.append([icon, os.path.basename(name)])
                        self.org_images.append(name)
                    except gi.repository.GLib.Error:
                        print("{} is not an image so skipped".format(name))
        self.filechooser_dialog.hide()

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
                    size = "{:.2f} MB".format(float(size / 1024))
                else:
                    size = "{:.2f} KB".format(float(size))
            return size
        return size

    def on_ui_optimize_button_clicked(self, button):
        if self.control_output_directory() and self.org_images:
            self.p_queue = len(self.org_images)
            self.z_queue = self.p_queue
            self.main_stack.set_visible_child_name("splash")
            self.select_image.set_visible(False)
            for org_image in self.org_images:
                command = ["/usr/bin/pngquant", "--quality=80-98", "--skip-if-larger", "--force", "--strip", "--speed",
                           "1",
                           "--output", os.path.join(self.output_dir,
                                                    os.path.basename(os.path.splitext(org_image)[0]) + "-pngquant.png"),
                           org_image]

                self.start_p_process(command)

    def on_ui_open_output_button_clicked(self, button):
        try:
            subprocess.check_call(["open", self.output_dir])
            return True
        except subprocess.CalledProcessError:
            print("error opening " + self.output_dir)
            return False

    def on_ui_optimize_new_button_clicked(self, button):
        self.main_stack.set_visible_child_name("select")
        self.select_image.set_visible(True)
        self.z_queue = 0
        self.p_queue = 0
        self.org_images = []
        self.liststore.clear()
        start, end = self.done_info.get_buffer().get_bounds()
        self.done_info.get_buffer().delete(start, end)

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
            for org_image in self.org_images:
                pngquanted = os.path.join(self.output_dir,
                                          os.path.basename(os.path.splitext(org_image)[0]) + "-pngquant.png")
                zopflipnged = os.path.join(self.output_dir,
                                           os.path.basename(os.path.splitext(org_image)[0]) + "-optimized.png")

                # if pngquanted file is bigger than org file then we use org file
                if not os.path.isfile(pngquanted):
                    shutil.copy2(org_image, pngquanted)
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

            for org_image in self.org_images:

                optimized = os.path.join(self.output_dir,
                                         os.path.basename(os.path.splitext(org_image)[0]) + "-optimized.png")

                self.done_info.get_buffer().insert(self.done_info.get_buffer().get_end_iter(),
                                                   "{} => old size: {} | new size: {}\n".format(
                                                       os.path.basename(optimized), self.get_size(org_image),
                                                       self.get_size(optimized)))

                pngquanted = os.path.join(self.output_dir,
                                          os.path.basename(os.path.splitext(org_image)[0]) + "-pngquant.png")
                if os.path.isfile(pngquanted):
                    os.remove(pngquanted)
