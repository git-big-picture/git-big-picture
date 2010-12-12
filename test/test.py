#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2010 Sebastian Pipping <sebastian@pipping.org>
# Copyright (C) 2010 Julius Plenz <julius@plenz.com>
# Copyright (C) 2010 Valentin Haenel <valentin.haenel@gmx.de>
# Licensed under GPL v3 or later

import tempfile as tf
import shutil as sh
import unittest as ut
import git_big_picture as gbp
import git_big_picture.git_tools as gt

class TestGitTools(ut.TestCase):

	def setUp(self):
		self.testing_dir = tf.mkdtemp(prefix='gbp-testing-', dir="/tmp")
		gbp.git_tools.git_env = {'GIT_DIR' : "%s/.git" % self.testing_dir }
		gt.get_command_output(['git', 'init', self.testing_dir])

	def tearDown(self):
		#sh.rmtree(testing_dir)
		pass

	def test_get_parent_map(self):
		pass


#def test_tag():
#	tags_target = {'73dd0407d6c51c9759e694cc296ac4c2dbae18ba': set(['0'])}
#	nt.assert_equal(tags_target, gbp.get_tag_dict())
#
#def test_branch():
#	branch_target = {'73dd0407d6c51c9759e694cc296ac4c2dbae18ba' : set(['master',
#																	   'origin/master'])}
#	nt.assert_equal(branch_target, gbp.get_branch_dict())


# vim: set noexpandtab:
