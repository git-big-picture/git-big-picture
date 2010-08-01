#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2010 Sebastian Pipping <sebastian@pipping.org>
# Copyright (C) 2010 Julius Plenz <julius@plenz.com>
# Copyright (C) 2010 Valentin Haenel <valentin.haenel@gmx.de>
# Licensed under GPL v3 or later

from distutils.core import setup, Extension
import git_big_picture as gbp

setup(name = 'git-big-picture',
	version = gbp.VERSION,
	author = 'Sebastian Pipping, Julius Plenz & Valentin Haenel',
	author_email = 'FIXME@foo.bar',
	description = 'Visualize git repositories.',
	url = 'http://git.goodpoint.de/?p=git-big-picture.git;a=summary',
	license = 'GPL v3 or later',
	scripts=['git-big-picture'])

# vim: set noexpandtab:
