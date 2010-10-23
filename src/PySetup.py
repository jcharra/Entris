#! /usr/bin/env python

# Some of this script is from Pete Shinners pygame2exe script.
# (data copying and pygame icon code)

# import modules
from distutils.core import setup
import sys, os, shutil, pygame
import py2exe

#########################
### Variables to edit ###
#########################

script = "entris.py"   # Starting .py or .pyw script
dest_file = "Entris"  # Final name of .exe file
dest_folder = "win"   # Final folder to contain the executable, data files, etc.
icon_file = ""       # Icon file. Leave blank for the pygame icon.
extra_data = []              # Extra data to copy to the final folder
extra_modules = []           # Extra modules to be included in the .exe (leave empty if no extra modules)
dll_excludes = []            # excluded dlls ["w9xpopen.exe", "msvcr71.dll"]

#Libraries to exclude from the EXE (use to cut down the final EXE filesize.)
lib_excludes = ["Tkinter", "tcl", "OpenGL", "Numeric", "numpy", "wxPython", "pyglet"]

# Stuff to show who made it, etc.
copyright = "Copyright (C) 2010"
author = "Johannes Charra"
company = None
version = "1.04"

###################################################################
### Do not edit below here, unless you just want to experiment. ###
###################################################################

# Run the script if no commands are supplied 
if len(sys.argv) == 1:
    sys.argv.append("py2exe")
    sys.argv.append("-q")

# Use the pygame icon if there's no icon designated
if icon_file is '':
    path = os.path.split(pygame.__file__)[0]
    icon_file = '' + os.path.join(path, 'pygame.ico') 

# Copy extra data files
def installfile(name):
    dst = os.path.join(dest_folder)
    print 'copying', name, '->', dst
    if os.path.isdir(name):
        dst = os.path.join(dst, name)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(name, dst)
    elif os.path.isfile(name):
        shutil.copy(name, dst)
    else:
        print 'Warning, %s not found' % name

##############################
### Distutils setup script ###
##############################

# Set some variables for the exe
class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.version = version
        self.company_name = company
        self.author = author
        self.copyright = copyright
        self.name = dest_file

# Set some more variables for the exe
target = Target(
    script = script,
    icon_resources = [(1, icon_file)],
    dest_base = dest_file,
    extra_modules = extra_modules
    )

# Run the setup script!
setup(
    options = {"py2exe": {"compressed": 1,
                          "optimize": 2,
                          "bundle_files": 1,
                          "dll_excludes": dll_excludes,
                          "dist_dir": dest_folder,
                          "excludes": lib_excludes}},
    zipfile = None,
    windows = [target],
    )

# install extra data files
print '\n' # Just a space to make it look nicer :)
for d in extra_data:
    installfile(d)

# If everything went okay, this should come up.
raw_input('\n\n\nConversion successful! Press enter to exit')
