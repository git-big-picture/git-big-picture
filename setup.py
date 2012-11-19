#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of git-big-picture
#
# Copyright (C) 2010    Sebastian Pipping <sebastian@pipping.org>
# Copyright (C) 2010    Julius Plenz <julius@plenz.com>
# Copyright (C) 2010-11 Valentin Haenel <valentin.haenel@gmx.de>
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


setup(name = 'git-big-picture',
    version = VERSION,
    author = 'Sebastian Pipping, Julius Plenz, and Valentin Haenel',
    description = 'Visualize git repositories.',
    url = 'http://git.goodpoint.de/?p=git-big-picture.git;a=summary',
    license = 'GPL v3 or later',
    modules = ['git_big_picture'],
    scripts = ['git-big-picture'],
)
