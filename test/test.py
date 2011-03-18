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

import os
import tempfile as tf
import shutil as sh
import unittest as ut
import git_big_picture as gbp
import git_big_picture.git_tools as gt

def dispatch(command_string):
	return gt.get_command_output(command_string.split(' '))

def get_head_sha():
	return dispatch('git rev-parse HEAD').rstrip()

def empty_commit(mess):
	dispatch('git commit --allow-empty -m %s' % mess)
	return get_head_sha()

class TestGitTools(ut.TestCase):

	def setUp(self):
		""" Setup testing environment.

		Create temporary directory, initialise git repo, and set some options.

		"""
		self.testing_dir = tf.mkdtemp(prefix='gbp-testing-', dir="/tmp")
		gbp.git_tools.git_env = {'GIT_DIR' : "%s/.git" % self.testing_dir }
		gt.get_command_output(['git', 'init', self.testing_dir])
		self.oldpwd = os.getcwd()
		os.chdir(self.testing_dir)

		dispatch('/usr/bin/git init')
		dispatch('git config user.name git-big-picture')
		dispatch('git config user.email git-big-picture@example.org')

	def tearDown(self):
		""" Remove testing environment """
		sh.rmtree(self.testing_dir)
		os.chdir(self.oldpwd)

	def test_get_parent_map(self):
		""" Check get_parent_map() works:

				 4 <- other
				 |\
				 | \
	   master -> 2  3
				 | /
				 |/
				 1

		"""
		sha_1 = empty_commit('1')
		sha_2 = empty_commit('2')
		dispatch('git checkout -b other HEAD^')
		sha_3 = empty_commit('3')
		dispatch('git merge --no-ff master')
		sha_4 = get_head_sha()

		expected_parents = {
			sha_1:set(),
			sha_2:set((sha_1,)),
			sha_3:set((sha_1,)),
			sha_4:set((sha_2, sha_3)),
		}

		actual_parents = gt.get_parent_map()
		self.assertEqual(actual_parents, expected_parents)


	def test_remove_non_labels_one(self):
		""" Remove a single commit from between two commits.
			3 <-- master
			2
			1 <-- one

		No ref pointing to B, thus it should be removed.

		"""
		one = empty_commit('1')
		dispatch('git branch one')
		two = empty_commit('2')
		three = empty_commit('3')
		(lb, rb, ab), (tags, ctags, nctags) = gt.get_mappings()
		graph = gbp.CommitGraph(gt.get_parent_map(), ab, tags)
		graph._remove_non_labels()
		expected_reduced_parents = {
			one:set(),
			three:set((one,)),
		}
		self.assertEqual(expected_reduced_parents, graph.parents)

# vim: set noexpandtab:
