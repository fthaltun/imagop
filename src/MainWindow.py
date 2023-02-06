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
import random
from datetime import datetime
from locale import gettext as _

import gi
from PIL import Image

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GObject, GLib, GdkPixbuf, Gdk, Notify, Pango

from UserSettings import UserSettings

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
        self.total_freed = 0

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
        self.optimize_button = self.GtkBuilder.get_object("ui_optimize_button")
        self.settings_button = self.GtkBuilder.get_object("ui_settings_button")
        self.defaults_button = self.GtkBuilder.get_object("ui_defaults_button")
        self.settings_button_image = self.GtkBuilder.get_object("ui_settings_button_image")
        self.jpeg_adjusment = self.GtkBuilder.get_object("ui_jpeg_adjusment")
        self.save_path_button = self.GtkBuilder.get_object("ui_save_path_button")
        self.output_combobox = self.GtkBuilder.get_object("ui_output_combobox")
        self.ext_name = self.GtkBuilder.get_object("ui_ext_name")
        self.save_path_box = self.GtkBuilder.get_object("ui_save_path_box")
        self.ext_name_box = self.GtkBuilder.get_object("ui_ext_name_box")
        self.info_revealer = self.GtkBuilder.get_object("ui_info_revealer")
        self.info_label = self.GtkBuilder.get_object("ui_info_label")
        self.settings_info_label = self.GtkBuilder.get_object("ui_settings_info_label")
        self.jpg_progress_box = self.GtkBuilder.get_object("ui_jpg_progress_box")
        self.png_progress_box = self.GtkBuilder.get_object("ui_png_progress_box")
        self.jpg_progress_label = self.GtkBuilder.get_object("ui_jpg_progress_label")
        self.png_progress_label = self.GtkBuilder.get_object("ui_png_progress_label")
        self.total_freed_label = self.GtkBuilder.get_object("ui_total_freed_label")

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
                    self.menu.popup(None, None, None, None, event.button, event.time)

    def on_iconview_rcmenu_del_activated(self, item, widget):
        treeiter = self.liststore.get_iter(self.right_index)
        self.liststore.remove(treeiter)
        del self.org_images[self.right_index.get_indices()[0]]

        for s in self.iconview.get_selected_items():
            self.liststore.remove(self.liststore.get_iter(s))
            del self.org_images[s.get_indices()[0]]

        self.optimize_button.set_sensitive(len(self.org_images) > 0)

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
                    self.optimize_button.set_sensitive(True)
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
            self.settings_counter += 1
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
                        self.optimize_button.set_sensitive(True)
                    except gi.repository.GLib.Error:
                        print("{} is not an image so skipped".format(name))

    def control_output_directory(self):
        try:
            if not os.path.isdir(self.UserSettings.config_save_path):
                os.makedirs(self.UserSettings.config_save_path)
        except Exception as e:
            print("{}".format(e))
            return False
        try:
            if self.UserSettings.config_output_method == 0:
                test_filename = os.path.join(self.UserSettings.config_save_path,
                                             ".imagop" + str(random.randint(0, 1000)))
                open(test_filename, "a").close()
                os.remove(test_filename)
            elif self.UserSettings.config_output_method == 1 or self.UserSettings.config_output_method == 2:
                folders = []
                for org_image in self.org_images:
                    if os.path.dirname(org_image) not in folders:
                        folders.append(os.path.dirname(org_image))
                for folder in folders:
                    test_filename = os.path.join(folder, ".imagop" + str(random.randint(0, 1000)))
                    open(test_filename, "a").close()
                    os.remove(test_filename)
        except PermissionError as e:
            self.info_revealer.set_reveal_child(True)
            print("{}".format(e))
            self.info_label.set_markup(
                "<small>{}</small>".format(_("You don't have write permissions to the image output folder.")))
            return False
        except Exception as e:
            print("{}".format(e))
            return False
        return True

    def get_size(self, filepath):
        size = 0
        if os.path.isfile(filepath):
            size = os.stat(filepath).st_size
        return size

    def beauty_size(self, byte):
        size = 0
        if isinstance(byte, int):
            size = byte / 1024
            if size > 1024:
                size = "{:.2f} MiB".format(float(size / 1024))
            else:
                size = "{:.2f} KiB".format(float(size))
        return size

    def add_to_done_listbox(self, images):
        for image in images:

            if self.UserSettings.config_output_method == 0:  # Save pictures to folder
                optimized = os.path.join(self.UserSettings.config_save_path,
                                         os.path.basename(os.path.splitext(image["name"])[0]) +
                                         ("-" if self.UserSettings.config_ext_name != "" else "") +
                                         self.UserSettings.config_ext_name + image["ext"])
            elif self.UserSettings.config_output_method == 1:  # Save each image in its own directory
                optimized = os.path.join(os.path.dirname(image["name"]),
                                         os.path.basename(os.path.splitext(image["name"])[0]) + "-" +
                                         (
                                             self.UserSettings.config_ext_name if self.UserSettings.config_ext_name != "" else self.UserSettings.default_ext_name)
                                         + image["ext"])
            elif self.UserSettings.config_output_method == 2:  # Overwrite existing image
                optimized = image["name"]
            else:
                optimized = image["name"]

            thumb = Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(optimized, 100, 100, False))

            img_name = Gtk.Label.new()
            img_name.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
            img_name.set_justify(Gtk.Justification.LEFT)
            img_name.set_xalign(0)
            img_name.set_text("{}".format(os.path.basename(optimized)))

            old_size = Gtk.Label.new()
            old_size.set_justify(Gtk.Justification.LEFT)
            old_size.set_markup("{}".format(self.beauty_size(image["size"])))

            new_size = Gtk.Label.new()
            new_size.set_justify(Gtk.Justification.LEFT)
            if self.get_size(optimized) < image["size"]:
                new_size.set_markup("<span color='green'>{}</span>".format(self.beauty_size(self.get_size(optimized))))
            else:
                new_size.set_markup("<span color='red'>{}</span>".format(self.beauty_size(self.get_size(optimized))))

            icon = Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.BUTTON)

            box_size = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
            box_size.set_spacing(8)
            box_size.pack_start(old_size, False, True, 0)
            box_size.pack_start(icon, False, True, 0)
            box_size.pack_start(new_size, False, True, 0)

            freed_label = Gtk.Label.new()
            freed_label.set_justify(Gtk.Justification.LEFT)
            freed_label.set_xalign(0)
            diff = image["size"] - self.get_size(optimized)
            if diff > 0:
                freed_label.set_markup("<span color='green'>{}</span> {}".format(self.beauty_size(diff), _("freed")))
            else:
                freed_label.set_markup(
                    "<span color='red'>{}</span> {}".format(self.beauty_size(abs(diff)), _("increased")))

            self.total_freed += diff

            box1 = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
            box1.props.valign = Gtk.Align.CENTER
            box1.set_spacing(8)
            box1.pack_start(img_name, False, True, 0)
            box1.pack_start(box_size, False, True, 0)
            box1.pack_start(freed_label, False, True, 0)

            box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
            box.name = image
            box.set_margin_top(5)
            box.set_margin_bottom(5)
            box.set_margin_start(5)
            box.set_margin_end(5)
            box.pack_start(thumb, False, True, 0)
            box.pack_start(box1, False, True, 13)

            GLib.idle_add(self.done_listbox.add, box)
            GLib.idle_add(self.done_listbox.add, Gtk.Separator.new(Gtk.Orientation.HORIZONTAL))
        GLib.idle_add(self.done_listbox.show_all)
        if self.total_freed > 0:
            GLib.idle_add(self.total_freed_label.set_markup,
                          "<b>{} <span color='green'>{}</span> {}</b>".format(_("Totally"),
                                                                              self.beauty_size(self.total_freed),
                                                                              _("freed")))
        else:
            GLib.idle_add(self.total_freed_label.set_markup,
                          "<b>{} <span color='red'>{}</span> {}</b>".format(_("Totally"),
                                                                            self.beauty_size(abs(self.total_freed)),
                                                                            _("increased")))

    def on_ui_optimize_button_clicked(self, button):
        self.total_freed = 0
        if self.org_images and self.control_output_directory():

            for org_image in self.org_images:
                if Image.open(org_image).format == "PNG":
                    self.png_images.append({"name": org_image, "size": self.get_size(org_image), "ext": ".png"})
                elif Image.open(org_image).format == "JPEG":
                    self.jpg_images.append({"name": org_image, "size": self.get_size(org_image), "ext": ".jpg"})

            self.p_queue = len(self.png_images)
            self.z_queue = self.p_queue
            self.jpg_queue = len(self.jpg_images)

            self.completed_jpg = 0
            self.completed_png = 0

            self.main_stack.set_visible_child_name("splash")
            self.select_image.set_sensitive(False)
            self.settings_button.set_sensitive(False)

            if self.jpg_images:
                GLib.idle_add(self.jpg_progress_box.set_visible, True)
            else:
                GLib.idle_add(self.jpg_progress_box.set_visible, False)
            if self.png_images:
                GLib.idle_add(self.png_progress_box.set_visible, True)
            else:
                GLib.idle_add(self.png_progress_box.set_visible, False)

            GLib.idle_add(self.jpg_progress_label.set_markup, "<b>{} / {}</b> {}".format(self.completed_jpg, len(self.jpg_images), _("completed.")))
            GLib.idle_add(self.png_progress_label.set_markup, "<b>{} / {}</b> {}".format(self.completed_png, len(self.png_images), _("completed.")))

            for png_image in self.png_images:

                if self.UserSettings.config_output_method == 0:  # Save pictures to folder
                    save_name = os.path.join(self.UserSettings.config_save_path,
                                             os.path.basename(os.path.splitext(png_image["name"])[0]) +
                                             ("-" if self.UserSettings.config_ext_name != "" else "") +
                                             self.UserSettings.config_ext_name + png_image["ext"])
                elif self.UserSettings.config_output_method == 1:  # Save each image in its own directory
                    save_name = os.path.join(os.path.dirname(png_image["name"]),
                                             os.path.basename(os.path.splitext(png_image["name"])[0]) + "-" +
                                             (self.UserSettings.config_ext_name if self.UserSettings.config_ext_name != "" else self.UserSettings.default_ext_name)
                                             + png_image["ext"])
                elif self.UserSettings.config_output_method == 2:  # Overwrite existing image
                    save_name = png_image["name"]
                else:
                    save_name = png_image["name"]

                if os.path.isfile(save_name):
                    self.backup_image(save_name)

                command = ["/usr/bin/pngquant", "--quality=80-98", "--skip-if-larger", "--force", "--strip", "--speed",
                           "1", "--output", save_name, png_image["name"]]

                self.start_p_process(command)

            for jpg_image in self.jpg_images:
                self.jp = threading.Thread(target=self.optimize_jpg, args=(jpg_image,))
                self.jp.daemon = True
                self.jp.start()

    def optimize_jpg(self, jpg_image):
        foo = Image.open(jpg_image["name"])
        foo = foo.resize(foo.size, Image.ANTIALIAS)
        if self.UserSettings.config_output_method == 0:  # Save pictures to folder
            save_name = os.path.join(self.UserSettings.config_save_path,
                                     os.path.basename(os.path.splitext(jpg_image["name"])[0]) +
                                     ("-" if self.UserSettings.config_ext_name != "" else "") +
                                     self.UserSettings.config_ext_name + jpg_image["ext"])
        elif self.UserSettings.config_output_method == 1:  # Save each image in its own directory
            save_name = os.path.join(os.path.dirname(jpg_image["name"]),
                                     os.path.basename(os.path.splitext(jpg_image["name"])[0]) + "-" +
                                     (self.UserSettings.config_ext_name if self.UserSettings.config_ext_name != "" else self.UserSettings.default_ext_name)
                                     + jpg_image["ext"])
        elif self.UserSettings.config_output_method == 2:  # Overwrite existing image
            save_name = jpg_image["name"]
        else:
            save_name = jpg_image["name"]

        if os.path.isfile(save_name):
            self.backup_image(save_name)

        foo.save(save_name, optimize=True, quality=self.UserSettings.config_jpeg_quality)

        self.jpg_queue -= 1

        self.completed_jpg += 1
        GLib.idle_add(self.jpg_progress_label.set_markup,
                      "<b>{} / {}</b> {}".format(self.completed_jpg, len(self.jpg_images), _("completed.")))

        if self.z_queue <= 0 and self.jpg_queue <= 0:
            GLib.idle_add(self.main_stack.set_visible_child_name, "complete")
            GLib.idle_add(self.settings_button.set_sensitive, True)
            self.notify()

            self.add_to_done_listbox(self.jpg_images)

    def on_ui_done_listbox_row_activated(self, listbox, row):
        row.set_can_focus(False)
        try:
            subprocess.check_call(["xdg-open", row.get_child().name["name"]])
            return True
        except subprocess.CalledProcessError:
            print("error opening " + row.get_child().name["name"])
            return False

    def backup_image(self, save_name):
        # a little check to prevent overwrite existing image if user didn't choose to overwrite existing image
        if self.UserSettings.config_output_method != 3:
            try:
                if not os.path.isdir(self.UserSettings.backup_folder):
                    os.makedirs(self.UserSettings.backup_folder)
                shutil.copy2(save_name, self.UserSettings.backup_folder + os.path.basename(save_name) + "-" +
                             datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            except Exception as e:
                print("{}".format(e))

    def on_ui_open_output_button_clicked(self, button):
        # Save pictures to folder
        if self.UserSettings.config_output_method == 0:
            try:
                subprocess.check_call(["xdg-open", self.UserSettings.config_save_path])
                return True
            except subprocess.CalledProcessError:
                print("error opening " + self.UserSettings.config_save_path)
                return False
        # Save each image in its own directory or Overwrite existing image
        elif self.UserSettings.config_output_method == 1 or self.UserSettings.config_output_method == 2:
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

    def on_ui_optimize_new_button_clicked(self, button):
        self.main_stack.set_visible_child_name("select")
        self.select_image.set_sensitive(True)
        self.settings_button.set_sensitive(True)
        self.optimize_button.set_sensitive(False)
        self.z_queue = 0
        self.p_queue = 0
        self.org_images = []
        self.png_images = []
        self.jpg_images = []
        self.completed_jpg = 0
        self.completed_png = 0
        self.jpg_progress_label.set_text("")
        self.png_progress_label.set_text("")
        self.liststore.clear()
        for row in self.done_listbox:
            self.done_listbox.remove(row)

    def on_ui_settings_button_clicked(self, button):
        self.settings_counter += 1
        if self.settings_counter % 2 == 1:
            self.settings_info_label.set_text("")
            self.old_page = self.main_stack.get_visible_child_name()
            self.main_stack.set_visible_child_name("settings")
            self.settings_button_image.set_from_icon_name("user-home-symbolic", Gtk.IconSize.BUTTON)
            self.jpeg_adjusment.set_value(self.UserSettings.config_jpeg_quality)
            self.save_path_button.set_uri(self.UserSettings.config_save_path)
            self.output_combobox.set_active(self.UserSettings.config_output_method)
            self.ext_name.set_text(self.UserSettings.config_ext_name)
            if self.UserSettings.config_output_method == 0:
                self.ext_name.set_placeholder_text("")
                self.save_path_box.set_visible(True)
                self.ext_name_box.set_visible(True)
            elif self.UserSettings.config_output_method == 1:
                self.ext_name.set_placeholder_text(self.UserSettings.default_ext_name)
                self.save_path_box.set_visible(False)
                self.ext_name_box.set_visible(True)
            elif self.UserSettings.config_output_method == 2:
                self.save_path_box.set_visible(False)
                self.ext_name_box.set_visible(False)
            self.control_defaults()
        else:
            self.main_stack.set_visible_child_name(self.old_page)
            self.settings_button_image.set_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)

    def on_ui_jpeg_adjusment_value_changed(self, adjusment):
        user_jpeg_quality = self.UserSettings.config_jpeg_quality
        if int(adjusment.get_value()) != user_jpeg_quality:
            self.UserSettings.writeConfig(int(adjusment.get_value()), self.UserSettings.config_output_method,
                                          self.UserSettings.config_save_path, self.UserSettings.config_ext_name)
            self.user_settings()
            self.settings_info_label.set_markup("<small><span weight='light'>{}</span></small>".format(
                _("Changes saved.")))
        self.control_defaults()

    def on_ui_output_combobox_changed(self, combo_box):
        user_output_method = self.UserSettings.config_output_method
        if combo_box.get_active() != user_output_method:
            self.UserSettings.writeConfig(self.UserSettings.config_jpeg_quality, combo_box.get_active(),
                                          self.UserSettings.config_save_path, self.UserSettings.config_ext_name)
            self.user_settings()
            self.settings_info_label.set_markup("<small><span weight='light'>{}</span></small>".format(
                _("Changes saved.")))
            if self.UserSettings.config_output_method == 0:
                self.ext_name.set_placeholder_text("")
                self.save_path_box.set_visible(True)
                self.ext_name_box.set_visible(True)
            elif self.UserSettings.config_output_method == 1:
                self.ext_name.set_placeholder_text(self.UserSettings.default_ext_name)
                self.save_path_box.set_visible(False)
                self.ext_name_box.set_visible(True)
            elif self.UserSettings.config_output_method == 2:
                self.save_path_box.set_visible(False)
                self.ext_name_box.set_visible(False)
        self.control_defaults()

    def on_ui_save_path_button_file_set(self, button):
        path = "{}".format(urllib.parse.unquote(button.get_uri().split("file://")[1]))
        user_save_path = self.UserSettings.config_save_path

        if path != user_save_path:
            self.UserSettings.writeConfig(self.UserSettings.config_jpeg_quality, self.UserSettings.config_output_method,
                                          path, self.UserSettings.config_ext_name)
            self.user_settings()
            self.settings_info_label.set_markup("<small><span weight='light'>{}</span></small>".format(
                _("Changes saved.")))
        self.control_defaults()

    def on_ui_ext_name_changed(self, editable):
        if self.UserSettings.config_output_method != 1:
            self.ext_name.set_placeholder_text("")

        user_ext_name = self.UserSettings.config_ext_name
        if self.ext_name.get_text() != user_ext_name:
            self.UserSettings.writeConfig(self.UserSettings.config_jpeg_quality, self.UserSettings.config_output_method,
                                          self.UserSettings.config_save_path, self.ext_name.get_text())
            self.user_settings()
            self.settings_info_label.set_markup("<small><span weight='light'>{}</span></small>".format(
                _("Changes saved.")))
        self.control_defaults()

    def control_defaults(self):
        if self.UserSettings.config_jpeg_quality != self.UserSettings.default_jpeg_quality or \
                self.UserSettings.config_save_path != self.UserSettings.default_save_path or \
                self.UserSettings.default_output_method != self.UserSettings.config_output_method or \
                self.UserSettings.default_ext_name != self.UserSettings.config_ext_name:
            self.defaults_button.set_sensitive(True)
        else:
            self.defaults_button.set_sensitive(False)

    def on_ui_defaults_button_clicked(self, button):
        self.UserSettings.createDefaultConfig(force=True)
        self.user_settings()
        self.jpeg_adjusment.set_value(self.UserSettings.config_jpeg_quality)
        self.output_combobox.set_active(self.UserSettings.config_output_method)
        self.save_path_button.set_uri(self.UserSettings.config_save_path)
        self.ext_name.set_text(self.UserSettings.config_ext_name)
        self.save_path_box.set_visible(True)
        self.ext_name_box.set_visible(True)
        self.defaults_button.set_sensitive(False)
        self.settings_info_label.set_markup("<small><span weight='light'>{}</span></small>".format(
            _("Changes saved.")))

    def on_ui_info_ok_button_clicked(self, button):
        self.info_revealer.set_reveal_child(False)

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

                if self.UserSettings.config_output_method == 0:  # Save pictures to folder
                    save_name = os.path.join(self.UserSettings.config_save_path,
                                             os.path.basename(os.path.splitext(png_image["name"])[0]) +
                                             ("-" if self.UserSettings.config_ext_name != "" else "") +
                                             self.UserSettings.config_ext_name + png_image["ext"])
                    if not os.path.isfile(save_name):
                        shutil.copy2(png_image["name"], save_name)
                elif self.UserSettings.config_output_method == 1:  # Save each image in its own directory
                    save_name = os.path.join(os.path.dirname(png_image["name"]),
                                             os.path.basename(os.path.splitext(png_image["name"])[0]) + "-" +
                                             (self.UserSettings.config_ext_name if self.UserSettings.config_ext_name != "" else self.UserSettings.default_ext_name)
                                             + png_image["ext"])
                    if not os.path.isfile(save_name):
                        shutil.copy2(png_image["name"], save_name)
                elif self.UserSettings.config_output_method == 2:  # Overwrite existing image
                    save_name = png_image["name"]
                else:
                    save_name = png_image["name"]

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
        self.completed_png += 1
        GLib.idle_add(self.png_progress_label.set_markup,
                      "<b>{} / {}</b> {}".format(self.completed_png, len(self.png_images), _("completed.")))

        if self.z_queue <= 0:
            GLib.idle_add(self.main_stack.set_visible_child_name, "complete")
            GLib.idle_add(self.settings_button.set_sensitive, True)
            self.notify()

            self.add_to_done_listbox(self.png_images)
            self.add_to_done_listbox(self.jpg_images)

    def notify(self):
        if Notify.is_initted():
            Notify.uninit()

        message = _("Image optimization completed.")

        Notify.init("imagop")
        notification = Notify.Notification.new(summary="ImagOP", body=message, icon="imagop")
        notification.show()
