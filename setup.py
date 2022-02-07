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
    ("/usr/bin", ["image-optimizer"]),
    ("/usr/share/applications", ["com.github.fthaltun.image-optimizer.desktop"]),
    ("/usr/share/image-optimizer/ui", ["ui/MainWindow.glade"]),
    ("/usr/share/image-optimizer/src", ["src/main.py", "src/MainWindow.py", "src/__version__"]),
    ("/usr/share/locale/tr/LC_MESSAGES", ["po/tr/LC_MESSAGES/image-optimizer.mo"]),
]

setup(
    name="Image Optimizer",
    version=version,
    packages=find_packages(),
    scripts=["image-optimizer"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Fatih Altun",
    author_email="fatih.altun@pardus.org.tr",
    description="Optimizes the sizes of images",
    license="GPLv3",
    keywords="image optimizer",
    url="https://github.com/fthaltun/image-optimizer",
)
