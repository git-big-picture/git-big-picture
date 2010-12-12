#! /usr/bin/env bash
# Copyright (C) 2010 Sebastian Pipping <sebastian@pipping.org>
# Copyright (C) 2010 Julius Plenz <julius@plenz.com>
# Copyright (C) 2010 Valentin Haenel <valentin.haenel@gmx.de>
# Licensed under GPL v3 or later

die() {
	echo "FAIL: $@"
	exit 1
}

SELFDIR=$(dirname $(which $0))
cd "${SELFDIR}"

../git-big-picture >/dev/null || die 'git-big-picture failed'

echo 'PASSED.'
