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

from __future__ import print_function

import subprocess
import git_tools as gt

VERSION = '0.8'

__docformat__ = "restructuredtext"

def loop(l):
	"""Generator looping over a potentially changing
		iteratable input, e.g. a set. """

	while l:
		res = list(l)
		for r in res:
			if r not in l:
				continue
			yield r

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

	def _remove_linear_runs(self):
		todo_list = self.parents.keys()
		black_list = set()
		for sha_one in todo_list:
			if sha_one in black_list:
				continue
			for p in self.parents[sha_one]:
				# Run into the past while history
				# keeps linear locally
				path = [sha_one, p, ]
				last = p

				if len(self.children[last]) != 1 \
						or self._has_label(last):
					pass
				else:
					while len(self.parents[last]) == 1:
						last = list(self.parents[last])[0]
						path.append(last)
						if len(self.children[last]) != 1 \
								or self._has_label(last):
							break

				if len(path) < 3:
					continue

				# path == [sha_one, edge_child/p, (..,) edge_parent]
				edge_child = path[1]
				edge_parent = path[-1]
				commits_to_delete = path[2:-1]

				self.dotdot.add(edge_child)
				black_list.add(edge_child)

				self.parents[edge_child].remove(path[2])
				self.parents[edge_child].add(edge_parent)
				self.children[edge_parent].remove(path[-2])
				self.children[edge_parent].add(edge_child)

				for i in commits_to_delete:
					black_list.add(i)
					del self.parents[i]
					del self.children[i]

		self.dotdot = set(self.parents.keys()) & self.dotdot

	def _optimize_merge_branch_fits_away(self):
		todo_list = self.parents.keys()
		black_list = set()
		for sha_one in todo_list:
			if sha_one in black_list:
				continue

			# 1/3 Run up the DAG as far as we can
			up_runners = set([sha_one, ])
			_children = dict()
			_parents = dict()
			_sources = set()
			for run_start in loop(up_runners):
				current = run_start
				while True:
					if current not in _parents:
						_parents[current] = set()
					if current not in _children:
						_children[current] = set()

					if self._has_label(current) \
							and current != sha_one:
						up_runners.remove(run_start)
						_sources.add(current)
						break
					if not self.parents[current]:
						up_runners.remove(run_start)
						_sources.add(current)
						break
					if current != sha_one \
							and len(_children[current]) \
							< len(self.children[current]):
						up_runners.remove(run_start)
						_sources.add(current)
						break

					parent_list = list(self.parents[current])
					for p in parent_list:
						if p not in _children:
							_children[p] = set()
						_children[p].add(current)
						_parents[current].add(p)

					next, other_parents = parent_list[0], parent_list[1:]
					for p in other_parents:
						up_runners.add(p)
					current = next

			# Remove complete branch points from sources
			# as we completeness allowed us running further up the DAG
			for s in list(_sources):
				if len(_children[s]) == len(self.children[s]):
					_sources.remove(s)

			# 2/3 Run down the temp DAG cutting edges where a merge
			# cannot be complete all from this sources
			_cut_points = set()
			for s in _sources:
				down_runners = set([s,])
				_up_pass_parents = dict()
				for run_start in loop(down_runners):
					current = run_start
					while True:
						if not _children.get(current, []):
							down_runners.remove(run_start)
							break

						child_list = list(_children[current])
						for ch in child_list:
							if ch not in _up_pass_parents:
								_up_pass_parents[ch] = set()
							_up_pass_parents[ch].add(current)

						next, other_children = child_list[0], child_list[1:]
						for p in other_children:
							down_runners.add(p)
						current = next

				for k, v in _up_pass_parents.items():
					diff = _parents[k] - _up_pass_parents[k]
					if diff:
						_cut_points.add(k)

			## # One source, one sink
			source_sink_pairs = set()
			for k, v in _parents.items():
				if k not in _cut_points and v:
					# Not a source
					continue

				# Find sink
				current = k
				while True:
					child_list = list(_children[current])
					if not child_list or (current in _cut_points and k != current):
						# Sink found
						if k != current:
							source_sink_pairs.add((k, current))
						break
					current = child_list[0]
			sources = set(e[0] for e in source_sink_pairs)
			sinks = set(e[1] for e in source_sink_pairs)
			to_delete = set(_parents.keys()) - sources.union(sinks)
			map(black_list.add, to_delete)

			for d in to_delete:
				assert(not self._has_label(d))

				for p in self.parents[d]:
					self.children[p].remove(d)
					for ch in self.children[d]:
						self.children[p].add(ch)
						self.parents[ch].add(p)
				for ch in self.children[d]:
					self.parents[ch].remove(d)
					for p in self.parents[d]:
						self.parents[ch].add(p)
						self.children[p].add(ch)
				del self.parents[d]
				del self.children[d]

		self._verify_child_mapping()

	def _optimize_non_labels(self):
		todo_list = self.parents.keys()
		black_list = set()
		for sha_one in todo_list:
			if sha_one in black_list:
				continue

			# 1/3 Run up the DAG as far as we can
			up_runners = set([sha_one, ])
			_children = dict()
			_parents = dict()
			_sources = set()
			for run_start in loop(up_runners):
				current = run_start
				while True:
					if current not in _parents:
						_parents[current] = set()
					if current not in _children:
						_children[current] = set()

					if self._has_label(current) \
							and current != sha_one:
						up_runners.remove(run_start)
						_sources.add(current)
						break
					if not self.parents[current]:
						up_runners.remove(run_start)
						_sources.add(current)
						break
					if current != sha_one \
							and len(_children[current]) \
							< len(self.children[current]):
						up_runners.remove(run_start)
						_sources.add(current)
						break

					parent_list = list(self.parents[current])
					for p in parent_list:
						if p not in _children:
							_children[p] = set()
						_children[p].add(current)
						_parents[current].add(p)

					next, other_parents = parent_list[0], parent_list[1:]
					for p in other_parents:
						up_runners.add(p)
					current = next		

			# Remove complete branch points from sources
			# as we completeness allowed us running further up the DAG
			for s in list(_sources):
				if self._has_label(s) or not self.parents[s]:
					continue
				if len(_children[s]) == len(self.children[s]):
					_sources.remove(s)

			
			to_delete = (set(_parents.keys()) - _sources) - set([sha_one, ])

			if not self._has_label(sha_one):
				to_delete.add(sha_one)

			for d in to_delete:
				assert(not self._has_label(d))

				for p in self.parents[d]:
					self.children[p].remove(d)
					for ch in self.children[d]:
						self.children[p].add(ch)
						self.parents[ch].add(p)
				for ch in self.children[d]:
					self.parents[ch].remove(d)
					for p in self.parents[d]:
						self.parents[ch].add(p)
						self.children[p].add(ch)
				del self.parents[d]
				del self.children[d]
				
				black_list.add(d)

		# Cut transitive redundant edges
		for sha_one in self.parents.keys():
			multi_child_parents = set(e for e in self.parents[sha_one] if len(self.children[e]) > 1)
			if len(self.parents[sha_one]) < 2:
				continue
			for p in multi_child_parents:
				other_parents = self.parents[sha_one] - set([p, ])
				down_runners = set([p, ])
				for run_start in loop(down_runners):
					current = run_start
					while True:
						if current == sha_one:
							down_runners.remove(run_start)
							break
						elif current in other_parents:
							self.parents[sha_one].remove(p)
							self.children[p].remove(sha_one)
							down_runners.clear()
							break

						child_list = list(self.children[current])
						l = len(child_list)
						if l > 1:
							next, other_children = child_list[0], child_list[1:]
						elif l == 1:
							next, other_children = child_list[0], list()
						else:
							down_runners.remove(run_start)
							break

						for c in other_children:
							down_runners.add(c)
						current = next

		self._verify_child_mapping()

	def _remove_non_labels(self):
		""" Generate the subgraph of the Git commit graph that contains only
		tags and branches.

		Remove, or 'filter' the unwanted commits from the DAG. This will modify
		self.parents and when done re-calculate self.children.

		The algorithm has three steps:

			1. Generate a reachability graph for labels
				This will generate a graph of all labels, with edges pointing to
				all reachable parents. Unfortunately this may possibly include
				edges from labels to parents that are also parents of the
				label's parents. These edges are redundant and must be removed.

			2. Generate a full parent graph for labels
				This will use the information from step 1. to generate a graph
				of labels, with edges pointing to all parents, where in this
				case the parent of a parent of a label is also that label's
				parent.

			3. Generate the reduced commit graph containing tags and branches
				This will use the information from step 2. to prune the edges of
				the full parent graph and produce the final output graph
		"""
		def recurse(commit, in_labeled_parents, out_seen_commits):
			""" Recursive call used in step 2.

			Parameters
			----------
			commit : string
				sha1 of the commit to start at.
			in_labeled_parents : dict mapping strings to strings
				mapping from labeled commits to reachable labels
			out_seen_commits : dict
				mapping from labeled commits to all their labeled parents
			"""

			all_parents = set()
			if commit in out_seen_commits.keys():
				# we have already explored the parents
				all_parents = out_seen_commits[commit].copy()
			elif len(in_labeled_parents[commit]) == 0:
				# there are no parents
				out_seen_commits[commit] = all_parents.copy()
			else:
				# explore the commits before this one
				for p in in_labeled_parents[commit]:
					all_parents = all_parents.union(
						recurse(p, in_labeled_parents, out_seen_commits))
				# record what we have seen
				out_seen_commits[commit] = all_parents.copy()
			# add the current commit to the list of parents
			# and return from recursive step
			all_parents.add(commit)
			return all_parents

		# 1. Generate a reachability graph for labels
		reachable_labeled_parents = dict()
		for label in self.branches.keys() + self.tags.keys():
			# Handle tags pointing to non-commits
			if label in self.parents:
				to_visit = list(self.parents[label])
			else:
				to_visit = list()
			seen = set()
			reachable_labeled_parents[label] = set()
			for commit in to_visit:
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

		# 2. Generate a full parent graph for labels
		seen_commits = dict()
		for label in self.branches.keys() + self.tags.keys():
			recurse(label, reachable_labeled_parents, seen_commits)

		# 3. Generate the reduced commit graph containing tags and branches
		for label in seen_commits.keys():
			# get the parents of the parents of label, and if these are also
			# parents of label, remove them from label's parent list
			for parent in seen_commits[label].copy():
				for p_parent in seen_commits[parent]:
					if p_parent in seen_commits[label]:
						seen_commits[label].remove(p_parent)

		self.parents = seen_commits
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


def _process_dot_output(dot_file_lines, format = None, viewer = None, outfile = None):
	""" Run 'dot' utility to generate graphical output.

	If viewer and outfile are None, the raw output is printed to stdout.
	Otherwise it is either displyed in the requested viewer program, or
	written to file, or both.

	Parameters
	----------
	dot_file_lines : list of strings
		graphviz input lines
	format : string
		format of output [svg, png, ps, pdf, ...]
	viewer : string
		name of program to disply output with
	oufile : string
		file to store output in
	"""

	import tempfile, os, sys
	if not format:
		if outfile:
			format = outfile.split('.')[-1]
			sys.stderr.write('guessing format: %s.\n' % format)
		else: # output plain text
			for line in dot_file_lines:
				print(line)
			return 0
	# output in specified format
	try:
		p = subprocess.Popen(['dot', '-T'+format], stdin=subprocess.PIPE,
			stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	except OSError, e:
		if e.errno == 2:
			sys.stderr.write('Fatal: `dot\' not found! Please install the Graphviz utility.\n')
		else:
			sys.stderr.write('Fatal: A problem occured calling `dot -T' + format + '\'!\n')
		sys.exit(2)
	if p.poll():
		sys.stderr.write('`dot\' terminated prematurely with error code %d;\n'
			'probably you specified an invalid format, see "man dot"\n' % p.poll())
		sys.exit(3)
	# send dot input, automatically receive and store output
	dot_output = p.communicate(input='\n'.join(dot_file_lines))[0]
	if viewer or outfile:
		if outfile:
			try:
				f = open(outfile, 'w+b')
			except IOError, e:
				sys.stderr.write('Fatal: could not open file %s (errno: %d)!\n' % (outfile, e.errno))
				sys.exit(4)
		elif viewer:
			f = tempfile.NamedTemporaryFile(prefix='git-big-picture')
		f.write(dot_output)
		f.flush()
		os.fsync(f.fileno())
		if viewer:
			try:
				subprocess.call([viewer, f.name])
			except OSError, e:
				sys.stderr.write('Error calling `' + viewer + '\'!')
				sys.exit(5)
		f.close() # tmpfile is automatically deleted
	else: # print raw SVG, PDF, ...
		print(dot_output)


def main(opts, git_dir):
	gt.git_env = git_dir
	(lb, rb, ab), (tags, ctags, nctags) = gt.get_mappings()
	graph = CommitGraph(gt.get_parent_map(), ab, tags)
	# graph._optimize_linear_runs_away()
	# graph._optimize_merge_branch_fits_away()
	# graph._optimize_non_labels()
	if opts.all_commits:
		sha_one_digits = graph._minimal_sha_one_digits()
	elif opts.some_commits:
		sha_one_digits = graph._minimal_sha_one_digits()
		graph._remove_linear_runs()
	else:
		sha_one_digits = None
		graph._remove_non_labels()

	dot_file_lines = graph._generate_dot_file(sha_ones_on_labels=opts.all_commits, sha_one_digits=sha_one_digits)
	_process_dot_output(dot_file_lines, format=opts.format, viewer=opts.viewer, outfile=opts.outfile)
	

# vim: set noexpandtab:
