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
        self.userhome = str(Path.home())
        self.backup_folder = self.userhome + "/imagop-backup/"

        self.default_jpeg_quality = 80
        self.default_output_method = 0
        self.default_save_path = self.userhome + "/imagop-output"
        self.default_ext_name = "imagop"

        self.configdir = self.userhome + "/.config/imagop/"
        self.configfile = "settings.ini"
        self.config = ConfigParser(strict=False)
        self.config_jpeg_quality = self.default_jpeg_quality
        self.config_output_method = self.default_output_method
        self.config_save_path = self.default_save_path
        self.config_ext_name = self.default_ext_name

    def createDefaultConfig(self, force=False):
        self.config['ImagOP'] = {'JpegQuality': self.default_jpeg_quality, 'OutputMethod': self.default_output_method,
                                 'SavePath': self.default_save_path, 'ExtName': self.default_ext_name}

        if not Path.is_file(Path(self.configdir + self.configfile)) or force:
            if self.createDir(self.configdir):
                with open(self.configdir + self.configfile, "w") as cf:
                    self.config.write(cf)

    def readConfig(self):
        try:
            self.config.read(self.configdir + self.configfile)
            self.config_jpeg_quality = self.config.getint('ImagOP', 'JpegQuality')
            self.config_output_method = self.config.getint('ImagOP', 'OutputMethod')
            self.config_save_path = self.config.get('ImagOP', 'SavePath')
            self.config_ext_name = self.config.get('ImagOP', 'ExtName')
        except Exception as e:
            print("{}".format(e))
            print("user config read error ! Trying create defaults")
            # if not read; try to create defaults
            self.config_jpeg_quality = self.default_jpeg_quality
            self.config_output_method = self.default_output_method
            self.config_save_path = self.default_save_path
            self.config_ext_name = self.default_ext_name
            try:
                self.createDefaultConfig(force=True)
            except Exception as e:
                print("self.createDefaultConfig(force=True) : {}".format(e))

    def writeConfig(self, jpegquality, outputmethod, savepath, extname):
        self.config['ImagOP'] = {'JpegQuality': jpegquality, 'OutputMethod': outputmethod, 'SavePath': savepath,
                                 'ExtName': extname}
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
