#!/bin/bash
#
# This file is part of git-big-picture
#
# Copyright (C) 2010    Sebastian Pipping <sebastian@pipping.org>
# Copyright (C) 2010    Julius Plenz <julius@plenz.com>
# Copyright (C) 2010-11 Valentin Haenel <valentin.haenel@gmx.de>
# Copyright (C) 2011    Yaroslav Halchenko <debian@onerussian.com>
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

# Just some rudimentary tests of the command line interface

outfile='file.svg'
viewer='firefox'

echo --- run without options
./git-big-picture

echo --- run plain
./git-big-picture -p | head

echo --- mix plain and others
./git-big-picture -p -f svg
./git-big-picture -p -v $viewer
./git-big-picture -p -o $outfile

echo --- try wrong format
./git-big-picture -f foo

echo --- mismatch format
./git-big-picture -f pdf -o $outfile

echo --- try no such viewer
./git-big-picture -f svg -v foo

echo --- provide no format
./git-big-picture -v $viewer

rm $outfile
