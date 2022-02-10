#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 19:05:13 2022

@author: fatihaltun
"""

import gi

from MainWindow import MainWindow

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.github.fthaltun.imagop",
                         flags=Gio.ApplicationFlags(0), **kwargs)
        self.window = None

    def do_activate(self):
        self.window = MainWindow(self)


if __name__ == "__main__":
    app = Application()
    app.run()
