# -*- coding: utf-8 -*-
""" torpydo - Bittorrent metafile handling for Python.

    Copyright (c) 2015 The PyroScope Project <pyroscope.project@gmail.com>

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
from __future__ import with_statement

import os
import re
import sys
import webbrowser

from setuptools import find_packages

from paver.easy import *
from paver.setuputils import setup
from pyrobase.paver.easy import *


#
# Project Metadata
#

changelog = path("debian/changelog")

name, version = open(changelog).readline().split(" (", 1)
version, _ = version.split(")", 1)

project = dict(
    # egg
    name = "torpydo",
    version = version,
    package_dir = {"": "src"},
    packages = find_packages("src", exclude = ["tests"]),
    include_package_data = True,
    zip_safe = True,
    data_files = [
        ("EGG-INFO", [
            "README.md", "LICENSE", "debian/changelog",
        ]),
    ],

    # dependencies
    install_requires = [
        "pyrobase",
    ],
    setup_requires = [
        "Paver",
        "pyrobase",
    ],

    # tests
    test_suite = "nose.collector",

    # cheeseshop
    author = "The PyroScope Project",
    author_email = "pyroscope.project@gmail.com",
    description = __doc__.split('.', 1)[0].strip(),
    long_description = __doc__.split('.', 1)[1].strip(),
    license = [line.strip() for line in __doc__.splitlines()
        if line.strip().startswith("Copyright")][0],
    url = "https://github.com/pyroscope/torpydo",
    keywords = "python utility library bittorrent",
    classifiers = [
        # see http://pypi.python.org/pypi?:action=list_classifiers
        #"Development Status :: 3 - Alpha",
        #"Development Status :: 4 - Beta",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache 2.0",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)


#
# Build
#
@task
@needs(["setuptools.command.egg_info"])
def bootstrap():
    "initialize project"


@task
@needs("docs")
def dist_docs():
    "create a documentation bundle"
    dist_dir = path("dist")
    docs_package = path("%s/%s-%s-docs.zip" % (dist_dir.abspath(), options.setup.name, options.setup.version))

    dist_dir.exists() or dist_dir.makedirs()
    docs_package.exists() and docs_package.remove()

    sh(r'cd build/apidocs && zip -qr9 %s .' % (docs_package,))

    print
    print "Upload @ http://pypi.python.org/pypi?:action=pkg_edit&name=%s" % ( options.setup.name,)
    print docs_package


#
# Testing
#

@task
@requires("nose>=1.0", "coverage>=3.4")
def test():
    "run unit tests"
    environment.call_task("nosetests")


@task
def coverage():
    "generate coverage report and show in browser"
    coverage_index = path("build/coverage/index.html")
    coverage_index.remove()
    sh("paver test")
    coverage_index.exists() and webbrowser.open(coverage_index)


@task
@needs("setuptools.command.build")
def functest():
    "functional test of the command line tools"
    from pyrobase.paver.support import vsh

    venv = path("build/venv")
    venv.exists() and venv.rmtree()
    sh("git clone --local '%s' '%s'" % (os.getcwd(), venv))
    with pushd(venv) as basedir:
        sh("virtualenv", "--no-site-packages", ".")
        vsh("easy_install", "-q", "-U", "setuptools")
        vsh("easy_install", "-q", "paver")
        vsh("paver", "bootstrap")


#
# Release Management
#
@task
@needs(["dist_clean", "minilib", "generate_setup", "sdist"])
def release():
    "check release before upload to PyPI"
    sh("paver bdist_egg")

    # Check that source distribution can be built and is complete
    print
    print "~" * 78
    print "TESTING SOURCE BUILD"
    sh(
        "{ cd dist/ && unzip -q %s-%s.zip && cd %s-%s/"
        "  && /usr/bin/python setup.py sdist >/dev/null"
        "  && if { unzip -ql ../%s-%s.zip; unzip -ql dist/%s-%s.zip; }"
        "        | cut -b26- | sort | uniq -c| egrep -v '^ +2 +' ; then"
        "       echo '^^^ Difference in file lists! ^^^'; false;"
        "    else true; fi; } 2>&1"
        % tuple([project["name"], version] * 4)
    )
    path("dist/%s-%s" % (project["name"], version)).rmtree()
    print "~" * 78

    print
    print "Created", " ".join([str(i) for i in path("dist").listdir()])
    print "Use 'paver sdist bdist_egg upload' to upload to PyPI"
    print "Use 'paver dist_docs' to prepare an API documentation upload"


#
# Main
#
setup(**project)
