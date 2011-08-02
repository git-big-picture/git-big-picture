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
import shlex


def dispatch(command_string):
	return gt.get_command_output(shlex.split(command_string))

def tag(sha1, tag_name):
	dispatch('git tag %s %s' % (tag_name, sha1))

def get_head_sha():
	return dispatch('git rev-parse HEAD').rstrip()

def empty_commit(mess):
	dispatch('git commit --allow-empty -m %s' % mess)
	return get_head_sha()

def print_dict(dict_):
	for (k,v) in dict_.iteritems():
		print k,v

class TestGitTools(ut.TestCase):

	def setUp(self):
		""" Setup testing environment.

		Create temporary directory, initialise git repo, and set some options.

		"""
		self.testing_dir = tf.mkdtemp(prefix='gbp-testing-', dir="/tmp")
		gbp.git_tools.git_env = {'GIT_DIR' : "%s/.git" % self.testing_dir }
		self.oldpwd = os.getcwd()
		os.chdir(self.testing_dir)

		dispatch('git init')
		dispatch('git config user.name git-big-picture')
		dispatch('git config user.email git-big-picture@example.org')

	def tearDown(self):
		""" Remove testing environment """
		sh.rmtree(self.testing_dir)
		os.chdir(self.oldpwd)

	def test_get_parent_map(self):
		""" Check get_parent_map() works:

		    master other
				|   |
			A---B---D
			 \     /
			  --C--
		"""
		a = empty_commit('a')
		b = empty_commit('b')
		dispatch('git checkout -b other HEAD^')
		c = empty_commit('c')
		dispatch('git merge --no-ff master')
		d = get_head_sha()

		expected_parents = {
			a:set(),
			b:set((a,)),
			c:set((a,)),
			d:set((c, b)),
		}

		actual_parents = gt.get_parent_map()
		self.assertEqual(actual_parents, expected_parents)


	def test_remove_non_labels_one(self):
		""" Remove a single commit from between two commits.

			A---B---C
			|       |
		   one    master

		No ref pointing to B, thus it should be removed.

		"""
		a = empty_commit('A')
		dispatch('git branch one')
		b = empty_commit('B')
		c = empty_commit('C')
		(lb, rb, ab), (tags, ctags, nctags) = gt.get_mappings()
		graph = gbp.CommitGraph(gt.get_parent_map(), ab, tags)
		graph._remove_non_labels()
		expected_reduced_parents = {
			a:set(),
			c:set((a,)),
		}
		self.assertEqual(expected_reduced_parents, graph.parents)
	
	def test_remove_non_labels_with_tags(self):
		""" Remove three commits and root commmit

            A---B---C---D---E---F
                |               |
               0.1            master

		"""
		a = empty_commit('A')
		b = empty_commit('B')
		dispatch('git tag 0.1')
		c = empty_commit('C')
		d = empty_commit('D')
		e = empty_commit('E')
		f = empty_commit('F')
		(lb, rb, ab), (tags, ctags, nctags) = gt.get_mappings()
		graph = gbp.CommitGraph(gt.get_parent_map(), ab, tags)
		graph._remove_non_labels()
		expected_reduced_parents = {
			b:set(),
			f:set((b,)),
		}
		self.assertEqual(expected_reduced_parents, graph.parents)

	def test_no_commit_tags(self):
		""" Test for tree-tag and a blob-tag.
		"""

		a = empty_commit('A')
		f = open('foo','w')
		f.writelines('bar')
		f.close()
		blob_hash = dispatch('git hash-object -w foo').rstrip()
		dispatch('git tag -m "blob-tag" blob-tag '+blob_hash)
		os.mkdir('baz')
		f = open('baz/foo','w')
		f.writelines('bar')
		f.close()
		dispatch('git add baz/foo')
		tree_hash = dispatch('git write-tree --prefix=baz').rstrip()
		dispatch('git tag -m "tree-tag" tree-tag '+tree_hash)
		dispatch('git reset')

		(lb, rb, ab), (tags, ctags, nctags) = gt.get_mappings()
		graph = gbp.CommitGraph(gt.get_parent_map(), ab, tags)
		graph._remove_non_labels()
		expected_reduced_parents = {
			blob_hash:set(),
			tree_hash:set(),
			a:set(),
		}
		self.assertEqual(expected_reduced_parents, graph.parents)
# vim: set noexpandtab:
