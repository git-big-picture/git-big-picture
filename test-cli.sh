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

set -x

outfile='file.svg'
viewer='firefox'
stats_file='stats'

echo --- run without options
./git-big-picture

echo --- run plain
./git-big-picture -p | sed '10q'

echo --- mix plain and others
./git-big-picture -p -f svg
./git-big-picture -p -v $viewer
./git-big-picture -p -o $outfile

echo --- try wrong format
./git-big-picture -f foo

echo --- mismatch format
./git-big-picture -f pdf -o $outfile

echo --- try just filename
./git-big-picture -o $outfile

echo --- try no such viewer
./git-big-picture -f svg -v foo

echo -- format but no extension
./git-big-picture -f svg -o file

echo --- provide no format
./git-big-picture -v $viewer

echo --- try profiling
./git-big-picture --pstats=$stats_file -o $outfile

rm $outfile
rm $stats_file
