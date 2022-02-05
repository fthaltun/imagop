#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 19:05:13 2022

@author: fatihaltun
"""

import locale
import os

import gi

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GObject

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

        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.aboutdialog.set_version(version)
        except:
            pass

        self.main_window = self.GtkBuilder.get_object("ui_main_window")
        self.main_window.set_application(application)

        self.main_window.show_all()
