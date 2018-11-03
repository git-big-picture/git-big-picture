#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of git-big-picture
#
# Copyright (C) 2010    Sebastian Pipping <sebastian@pipping.org>
# Copyright (C) 2010    Julius Plenz <julius@plenz.com>
# Copyright (C) 2010-18 Valentin Haenel <valentin.haenel@gmx.de>
#
# git-big-picture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# git-big-piture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with git-big-picture.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup
from git_big_picture import __version__ as VERSION

with open('README.rst') as f:
    long_description = f.read()

setup(name = 'git-big-picture',
    version = VERSION,
    author = 'Sebastian Pipping, Julius Plenz, and Valentin Haenel',
    description = 'Git -- the big picture',
    long_description=long_description,
    url = 'https://github.com/esc/git-big-picture',
    license = 'GPL v3 or later',
    scripts = ['git-big-picture'],
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
