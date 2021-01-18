#! /usr/bin/env bash
# This file is part of git-big-picture
#
# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
#
# git-big-picture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# git-big-picture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with git-big-picture.  If not, see <http://www.gnu.org/licenses/>.

set -e
set -o pipefail

tempfile="$(mktemp)"
remove_tempfile() {
    if [[ -e "${tempfile}" ]]; then
        rm -v "${tempfile}"
    fi
}
trap remove_tempfile EXIT

text_before_help_output() {
    awk '/usage:/ { hide = 1 } !hide { print }' "$1"
}

text_after_help_output() {
    awk '/Usage Examples/ { show = 1 } show { print }' "$1"
}

{
    text_before_help_output README.rst
    git-big-picture --help | sed '/./ s,^,    ,'
    echo
    text_after_help_output README.rst
} > "${tempfile}"

mv "${tempfile}" README.rst
