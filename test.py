#!/usr/bin/env pytest
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
# git-big-picture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with git-big-picture.  If not, see <http://www.gnu.org/licenses/>.

import os
import shlex
import shutil as sh
import tempfile as tf
import unittest as ut

import git_big_picture._main as gbp

# The only reason these global commands work, is because we change the cwd of
# the test script... ugly.


def dispatch(command_string):
    return gbp.get_command_output(shlex.split(command_string))


def tag(sha1, tag_name):
    dispatch(f'git tag {tag_name} {sha1}')


def get_head_sha():
    return dispatch('git rev-parse HEAD').rstrip()


def empty_commit(mess):
    dispatch('git commit --allow-empty -m %s' % mess)
    return get_head_sha()


def print_dict(dict_):
    for (k, v) in dict_.items():
        print(k, v)


class TestGitTools(ut.TestCase):
    def setUp(self):
        """ Setup testing environment.

        Create temporary directory, initialise git repo, and set some options.

        """
        self.testing_dir = tf.mkdtemp(prefix='gbp-testing-', dir="/tmp")
        self.oldpwd = os.getcwd()
        os.chdir(self.testing_dir)

        dispatch('git init')
        dispatch('git config user.name git-big-picture')
        dispatch('git config user.email git-big-picture@example.org')

    def tearDown(self):
        """ Remove testing environment """
        sh.rmtree(self.testing_dir)
        os.chdir(self.oldpwd)

    @property
    def graph(self):
        return gbp.graph_factory(self.testing_dir)

    def test_find_roots(self):
        def create_root(branch_name):
            dispatch('git read-tree --empty')
            new_tree = dispatch('git write-tree').strip()
            new_commit = dispatch('git commit-tree %s -m empty' % new_tree).strip()
            dispatch(f'git branch {branch_name} {new_commit}')
            return new_commit

        a = empty_commit('a')
        empty_commit('b')
        graph = self.graph
        self.assertEqual(graph.roots, [a])
        c = create_root('C')
        graph = self.graph
        self.assertEqual(set(graph.roots), {a, c})
        d = create_root('D')
        graph = self.graph
        self.assertEqual(set(graph.roots), {a, c, d})
        e = create_root('E')
        graph = self.graph
        self.assertEqual(set(graph.roots), {a, c, d, e})

    def test_filter_roots(self):
        a = empty_commit('a')
        b = empty_commit('b')
        graph = self.graph
        filterd_graph = graph.filter(roots=True)
        expected_parents = {
            a: set(),
            b: {a},
        }
        self.assertEqual(expected_parents, filterd_graph.parents)

    def test_find_merges_bifurcations(self):
        r""" Check that finding merges and bifurcations works.

            master other
                |   |
            A---B---D
             \     /
              --C--
        """
        a = empty_commit('a')
        empty_commit('b')
        dispatch('git checkout -b other HEAD^')
        empty_commit('c')
        dispatch('git merge master')
        d = get_head_sha()

        graph = self.graph
        self.assertEqual(set(graph.merges), {d})
        self.assertEqual(set(graph.bifurcations), {a})

    def test_get_parent_map(self):
        r""" Check get_parent_map() works:

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
            a: set(),
            b: {a},
            c: {a},
            d: {c, b},
        }
        self.assertEqual(gbp.Git(self.testing_dir).get_parent_map(), expected_parents)

    def test_filter_one(self):
        """ Remove a single commit from between two commits.

            A---B---C
            |       |
           one    master

        No ref pointing to B, thus it should be removed.

        """
        a = empty_commit('A')
        dispatch('git branch one')
        empty_commit('B')
        c = empty_commit('C')
        graph = self.graph
        filterd_graph = graph.filter()
        expected_reduced_parents = {
            a: set(),
            c: {a},
        }
        self.assertEqual(expected_reduced_parents, filterd_graph.parents)

    def test_filter_with_tags(self):
        """ Remove three commits and root commit

            A---B---C---D---E---F
                |               |
               0.1            master

        """
        a = empty_commit('A')
        b = empty_commit('B')
        dispatch('git tag 0.1')
        empty_commit('C')
        empty_commit('D')
        empty_commit('E')
        f = empty_commit('F')
        graph = self.graph
        # use the defaults
        filterd_graph = graph.filter()
        expected_reduced_parents = {
            a: set(),
            b: {a},
            f: {b},
        }
        self.assertEqual(expected_reduced_parents, filterd_graph.parents)
        filterd_graph = graph.filter(roots=False)
        expected_reduced_parents = {
            b: set(),
            f: {b},
        }
        self.assertEqual(expected_reduced_parents, filterd_graph.parents)
        filterd_graph = graph.filter(tags=False)
        expected_reduced_parents = {
            a: set(),
            f: {a},
        }
        self.assertEqual(expected_reduced_parents, filterd_graph.parents)

    def test_no_commit_tags(self):
        """ Test for tree-tag and a blob-tag.
        """

        a = empty_commit('A')
        f = open('foo', 'w')
        f.writelines('bar')
        f.close()
        blob_hash = dispatch('git hash-object -w foo').rstrip()
        dispatch('git tag -m "blob-tag" blob-tag ' + blob_hash)
        os.mkdir('baz')
        f = open('baz/foo', 'w')
        f.writelines('bar')
        f.close()
        dispatch('git add baz/foo')
        tree_hash = dispatch('git write-tree --prefix=baz').rstrip()
        dispatch('git tag -m "tree-tag" tree-tag ' + tree_hash)
        dispatch('git reset')

        graph = self.graph
        filterd_graph = graph.filter()
        expected_reduced_parents = {
            blob_hash: set(),
            tree_hash: set(),
            a: set(),
        }
        self.assertEqual(expected_reduced_parents, filterd_graph.parents)

    def test_parent_of_parent_loop(self):
        r""" Test the case, where an alternative route may lead to a parents
        parent.

           0.1         0.2    master
            |           |       |
            A---B---C---D---E---F
                     \     /
                      --G--

           0.1 0.2 master
            |   |   |
            A---D---F
            \      /
             ------

        """
        a = empty_commit('A')
        tag(a, '0.1')
        empty_commit('B')
        c = empty_commit('C')
        d = empty_commit('D')
        tag(d, '0.2')
        empty_commit('E')

        dispatch('git checkout -b topic %s' % c)
        empty_commit('G')
        dispatch('git checkout master')
        dispatch('git merge topic')
        f = get_head_sha()
        dispatch('git branch -d topic')

        graph = self.graph
        filterd_graph = graph.filter()
        expected_reduced_parents = {
            d: {a},
            a: set(),
            f: {a, d},
        }
        self.assertEqual(expected_reduced_parents, filterd_graph.parents)

    def test_expose_multi_parent_bug(self):
        r""" Test for a peculiar bug that used to exist in pruning the graph.

        Before:

             A---B---C---D---E---F master
             |   |    \         /
            0.0 0.1    N---O---P topic

        After:

            0.0---0.1---master
                    \     /
                     topic

        """
        a = empty_commit('A')
        tag(a, '0.0')
        b = empty_commit('B')
        tag(b, '0.1')
        c = empty_commit('C')
        empty_commit('D')
        empty_commit('E')
        dispatch('git checkout -b topic %s' % c)
        empty_commit('N')
        empty_commit('O')
        p = empty_commit('P')
        dispatch('git checkout master')
        dispatch('git merge topic')
        f = get_head_sha()
        graph = self.graph
        filterd_graph = graph.filter()
        expected_reduced_parents = {
            b: {a},
            a: set(),
            f: {p, b},
            p: {b},
        }
        dispatch(f"git log --oneline {f}..{p}")
        self.assertEqual(expected_reduced_parents, filterd_graph.parents)

    def test_more_realistic(self):
        r""" Test a slightly larger DAG

        input:
                    0.1.1   0.1.2
                      |       |
            0.0   G---H---I---J---K---L---M maint
            |    /
            A---B---C---D---E---F master
                |    \         /
               0.1    N---O---P topic

        output:

                     0.1.1---0.1.2---maint
                    /
            0.0---0.1---master
                    \     /
                     topic
        """
        a = empty_commit('A')
        tag(a, '0.0')
        b = empty_commit('B')
        tag(b, '0.1')
        c = empty_commit('C')
        empty_commit('D')
        empty_commit('E')
        dispatch('git checkout -b maint %s' % b)
        empty_commit('G')
        h = empty_commit('H')
        tag(h, '0.1.1')
        empty_commit('I')
        j = empty_commit('J')
        tag(j, '0.1.2')
        empty_commit('K')
        empty_commit('L')
        m = empty_commit('M')
        dispatch('git checkout -b topic %s' % c)
        empty_commit('N')
        empty_commit('O')
        p = empty_commit('P')
        dispatch('git checkout master')
        dispatch('git merge topic')
        f = get_head_sha()
        graph = self.graph
        filterd_graph = graph.filter()
        expected_reduced_parents = {
            m: {j},
            j: {h},
            h: {b},
            b: {a},
            a: set(),
            f: {p, b},
            p: {b},
        }
        print_dict(expected_reduced_parents)
        print_dict(graph.parents)
        self.assertEqual(expected_reduced_parents, filterd_graph.parents)
