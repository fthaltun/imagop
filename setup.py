#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os, subprocess

def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs("{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True)
            mo_file = "{}/{}/LC_MESSAGES/{}".format(podir, po.split(".po")[0], "imagop.mo")
            msgfmt_cmd = 'msgfmt {} -o {}'.format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(("/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                       ["po/" + po.split(".po")[0] + "/LC_MESSAGES/imagop.mo"]))
    return mo


changelog = "debian/changelog"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
        version = "0.0.0"
    f = open("src/__version__", "w")
    f.write(version)
    f.close()

data_files = [
    ("/usr/bin", ["imagop"]),
    ("/usr/share/applications", ["com.github.fthaltun.imagop.desktop"]),
    ("/usr/share/imagop/ui", ["ui/MainWindow.glade"]),
    ("/usr/share/imagop/src", ["src/Main.py", "src/MainWindow.py", "src/UserSettings.py", "src/__version__"]),
    ("/usr/share/icons/hicolor/scalable/apps/", ["ui/imagop.svg"])
] + create_mo_files()

setup(
    name="ImagOP",
    version=version,
    packages=find_packages(),
    scripts=["imagop"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Fatih Altun",
    author_email="fatih.altun@pardus.org.tr",
    description="Optimizes the sizes of images",
    license="GPLv3",
    keywords="imagop, image, optimizer",
    url="https://github.com/fthaltun/imagop",
)
