# -*- coding: utf-8 -*-
#
# This file is part of git-big-picture
#
# Copyright (C) 2010    Sebastian Pipping <sebastian@pipping.org>
# Copyright (C) 2010    Julius Plenz <julius@plenz.com>
# Copyright (C) 2010-12 Valentin Haenel <valentin.haenel@gmx.de>
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

from __future__ import print_function

VERSION = '0.9.0-dev'

__docformat__ = "restructuredtext"


class CommitGraph(object):
    def __init__(self, parent_map, branch_dict, tag_dict):
        self.parents = parent_map
        self.branches = branch_dict
        self.tags = tag_dict
        self.dotdot = set()

        self.children = {}
        self._calculate_child_mapping()
        self._verify_child_mapping()

    def _has_label(self, sha_one):
        """ Check if a sha1 is pointed to by a ref.

        Parameters
        ----------
        sha_one : string
        """

        return sha_one in self.branches \
            or sha_one in self.tags

    def _calculate_child_mapping(self):
        """ Populate the self.children dict, using self.parents. """
        for sha_one, parent_sha_ones in self.parents.items():
            for p in parent_sha_ones:
                if p not in self.children:
                    self.children[p] = set()
                self.children[p].add(sha_one)
            if sha_one not in self.children:
                self.children[sha_one] = set()

    def _verify_child_mapping(self):
        """ Ensure that self.parents and self.children represent the same DAG.
        """
        for sha_one, pars in self.parents.items():
            for p in pars:
                for c in self.children[p]:
                    assert(p in self.parents[c])
        for sha_one, chs in self.children.items():
            for c in chs:
                for p in self.parents[c]:
                    assert(c in self.children[p])

    def _remove_non_labels(self):
        """ Generate the subgraph of the Git commit graph that contains only
        tags and branches.

        Remove, or 'filter' the unwanted commits from the DAG. This will modify
        self.parents and when done re-calculate self.children.

        Generate a reachability graph for labels This will generate a graph of
        all labels, with edges pointing to all reachable parents. Unfortunately
        this may possibly include edges from labels to parents that are also
        parents of the label's parents. These edges are redundant and must be
        removed.

        """

        reachable_labeled_parents = dict()
        # for everything that we are interested in
        for label in self.branches.keys() + self.tags.keys():
            # Handle tags pointing to non-commits
            if label in self.parents:
                to_visit = list(self.parents[label])
            else:
                to_visit = list()
            # create the set of seen commits
            seen = set()
            # initialise the parents for this label
            reachable_labeled_parents[label] = set()
            # iterate through to_visit list
            for commit in to_visit:
                # we have already been here
                if commit in seen:
                    continue
                else:
                    seen.add(commit)
                    if self._has_label(commit):
                        # has label and is reachable from current label
                        reachable_labeled_parents[label].add(commit)
                    else:
                        # no label, continue searching
                        to_visit.extend(self.parents[commit])

        # reset the parents of this graph
        self.parents = reachable_labeled_parents
        # update the child_mapping
        self._calculate_child_mapping()

    def _minimal_sha_one_digits(self):
        """ Calculate the minimal number of sha1 digits required to represent
        all commits unambiguously. """
        key_count = len(self.parents)
        for digit_count in xrange(7, 40):
            if len(set(e[0:digit_count] for e in self.parents.keys())) == key_count:
                return digit_count
        return 40

    def _generate_dot_file(self, sha_ones_on_labels, sha_one_digits=None):
        """ Generate graphviz input.

        Parameters
        ----------
        sha_ones_on_labels : boolean
            if True show sha1 (or minimal) on labels in addition to ref names
        sha_one_digits : int
            number of digits to use for showing sha1

        Returns
        -------
        dot_file_lines : list of strings
            lines of the graphviz input
        """

        def format_sha_one(sha_one):
            """ Shorten sha1 if required. """
            if (sha_one_digits is None) or (sha_one_digits == 40):
                return sha_one
            else:
                return sha_one[0:sha_one_digits]

        def label_gen():
            keys = set(self.branches.keys()).union(set(self.tags.keys()))
            for k in keys:
                labels = []
                case = 0
                if k in self.tags:
                    case = case + 1
                    map(labels.append, sorted(self.tags[k]))
                if k in self.branches:
                    case = case + 2
                    map(labels.append, sorted(self.branches[k]))
                # http://www.graphviz.org/doc/info/colors.html
                color = "/pastel13/%d" % case
                yield (k, labels, color)

        dot_file_lines = ['digraph {']
        for sha_one, labels, color in label_gen():
            dot_file_lines.append('\t"%(ref)s"[label="%(label)s", color="%(color)s", style=filled];' % {
                'ref':sha_one,
                'label':'\\n'.join(labels \
                    + (sha_ones_on_labels and [format_sha_one(sha_one),] or list())),
                'color':color})
        for sha_one in self.dotdot:
            dot_file_lines.append('\t"%(ref)s"[label="..."];' % {'ref':sha_one})
        if (sha_one_digits is not None) and (sha_one_digits != 40):
            for sha_one in (e for e in self.parents.keys() if not (self._has_label(e) or e in self.dotdot)):
                dot_file_lines.append('\t"%(ref)s"[label="%(label)s"];' % {
                    'ref':sha_one,
                    'label':format_sha_one(sha_one)})
        for child, self.parents in self.parents.items():
            for p in self.parents:
                dot_file_lines.append('\t"%(source)s" -> "%(target)s";' % {'source':child, 'target':p})
        dot_file_lines.append('}')
        return dot_file_lines
