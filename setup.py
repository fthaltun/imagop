#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages, os

changelog = "debian/changelog"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
        version = ""
    f = open("src/__version__", "w")
    f.write(version)
    f.close()

data_files = [
    ("/usr/bin", ["imagop"]),
    ("/usr/share/applications", ["com.github.fthaltun.imagop.desktop"]),
    ("/usr/share/imagop/ui", ["ui/MainWindow.glade"]),
    ("/usr/share/imagop/src", ["src/main.py", "src/MainWindow.py", "src/__version__"]),
    ("/usr/share/locale/tr/LC_MESSAGES", ["po/tr/LC_MESSAGES/imagop.mo"]),
    ("/usr/share/icons/hicolor/scalable/apps/", ["ui/imagop.svg"])
]

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
