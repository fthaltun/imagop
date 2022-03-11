#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 16 14:53:13 2022

@author: fatih
"""

from pathlib import Path
from configparser import ConfigParser


class UserSettings(object):
    def __init__(self):
        userhome = str(Path.home())

        self.default_jpeg_quality = 80
        self.default_save_path = userhome + "/imagop-output"
        self.default_overwrite = False

        self.configdir = userhome + "/.config/imagop/"
        self.configfile = "settings.ini"
        self.config = ConfigParser(strict=False)
        self.config_jpeg_quality = self.default_jpeg_quality
        self.config_save_path = self.default_save_path
        self.config_overwrite = self.default_overwrite

    def createDefaultConfig(self, force=False):
        self.config['ImagOP'] = {'JpegQuality': self.default_jpeg_quality, 'SavePath': self.default_save_path,
                                 'Overwrite': self.default_overwrite}

        if not Path.is_file(Path(self.configdir + self.configfile)) or force:
            if self.createDir(self.configdir):
                with open(self.configdir + self.configfile, "w") as cf:
                    self.config.write(cf)

    def readConfig(self):
        try:
            self.config.read(self.configdir + self.configfile)
            self.config_jpeg_quality = self.config.getint('ImagOP', 'JpegQuality')
            self.config_save_path = self.config.get('ImagOP', 'SavePath')
            self.config_overwrite = self.config.getboolean('ImagOP', 'Overwrite')
        except Exception as e:
            print("{}".format(e))
            print("user config read error ! Trying create defaults")
            # if not read; try to create defaults
            self.config_jpeg_quality = self.default_jpeg_quality
            self.config_save_path = self.default_save_path
            self.config_overwrite = self.default_overwrite
            try:
                self.createDefaultConfig(force=True)
            except Exception as e:
                print("self.createDefaultConfig(force=True) : {}".format(e))

    def writeConfig(self, jpegquality, savepath, overwrite):
        self.config['ImagOP'] = {'JpegQuality': jpegquality, 'SavePath': savepath, 'Overwrite': overwrite}
        if self.createDir(self.configdir):
            with open(self.configdir + self.configfile, "w") as cf:
                self.config.write(cf)
                return True
        return False

    def createDir(self, dir):
        try:
            Path(dir).mkdir(parents=True, exist_ok=True)
            return True
        except:
            print("{} : {}".format("mkdir error", dir))
            return False
