#!/usr/bin/env python
#
# This file is part of git-big-picture
#
# Copyright (C) 2010    Sebastian Pipping <sebastian@pipping.org>
# Copyright (C) 2010    Julius Plenz <julius@plenz.com>
# Copyright (C) 2011    Yaroslav Halchenko <debian@onerussian.com>
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

import argparse
import ast
import copy
import os
import re
import signal
import subprocess
import sys
import tempfile
import textwrap
import time

__version__ = '1.0.0'
__docformat__ = "restructuredtext"

# format settings
GRAPHVIZ = 'graphviz'
PROCESSED = 'processed'
FORMAT = 'format'
VIEWER = 'viewer'
OUT_FILE = 'outfile'
WAIT_SECONDS = 'wait'
OUTPUT_SETTINGS = [
    FORMAT,
    GRAPHVIZ,
    PROCESSED,
    VIEWER,
    OUT_FILE,
    WAIT_SECONDS,
]
OUTPUT_DEFAULTS = {
    FORMAT: 'svg',
    GRAPHVIZ: False,
    PROCESSED: False,
    VIEWER: False,
    OUT_FILE: False,
    WAIT_SECONDS: 2.0,
}

# filter settings
BRANCHES = 'branches'
TAGS = 'tags'
ROOTS = 'roots'
MERGES = 'merges'
BIFURCATIONS = 'bifurcations'
FILTER_SETTINGS = [
    BRANCHES,
    TAGS,
    ROOTS,
    MERGES,
    BIFURCATIONS,
]
FILTER_DEFAULTS = {
    BRANCHES: True,
    TAGS: True,
    ROOTS: True,
    MERGES: False,
    BIFURCATIONS: False,
}

# annotation settings
MESSAGES = 'messages'
ANNOTATION_SETTINGS = [
    MESSAGES,
]
ANNOTATION_DEFAULTS = {
    MESSAGES: False,
}

EXIT_CODES = {
    "too_many_args": 1,
    "dot_not_found": 2,
    "problem_with_dot": 3,
    "dot_terminated_early": 4,
    "not_write_to_file": 5,
    "no_such_viewer": 6,
    "graphviz_processed_others": 7,
    "no_options": 8,
    "no_git": 9,
    "no_git_repo": 10,
    "killed_by_sigint": 128 + signal.SIGINT,
}

sha1_pattern = re.compile('[0-9a-fA-F]{40}')

# https://graphviz.org/doc/info/attrs.html#k:rankdir
# NOTE: "left to right" to a human is "right to left" to Graphviz; same for top and bottom
RANKDIR_OF_HISTORY_DIRECTION = {
    'downwards': 'BT',
    'leftwards': 'LR',
    'rightwards': 'RL',
    'upwards': 'TB',
}

DEBUG = False

USAGE = "%(prog)s OPTIONS [REPOSITORY]"


def create_parser():
    parser = argparse.ArgumentParser(prog='git-big-picture',
                                     usage=USAGE,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    format_group = parser.add_argument_group("output options",
                                             "Options to control output and format")

    # output options
    format_group.add_argument('-f',
                              '--format',
                              dest=FORMAT,
                              metavar='FMT',
                              help='set output format [svg, png, ps, pdf, ...]')

    format_group.add_argument('--history-direction',
                              default=None,
                              choices=sorted(RANKDIR_OF_HISTORY_DIRECTION.keys()),
                              help='enforce a specific direction of history on Graphviz\n'
                              '(default: upwards)')

    format_group.add_argument('-g',
                              '--graphviz',
                              default=None,
                              action='store_true',
                              dest=GRAPHVIZ,
                              help='output lines suitable as input for dot/graphviz')
    format_group.add_argument('-G',
                              '--no-graphviz',
                              default=None,
                              action='store_false',
                              dest=GRAPHVIZ,
                              help='disable dot/graphviz output')

    format_group.add_argument('-p',
                              '--processed',
                              default=None,
                              action='store_true',
                              dest=PROCESSED,
                              help='output the dot processed, binary data')
    format_group.add_argument('-P',
                              '--no-processed',
                              default=None,
                              action='store_false',
                              dest=PROCESSED,
                              help='disable binary output')

    format_group.add_argument('-v',
                              '--viewer',
                              dest=VIEWER,
                              metavar='CMD',
                              help='write image to tempfile and start specified viewer')
    format_group.add_argument('-V',
                              '--no-viewer',
                              default=None,
                              action='store_false',
                              dest=VIEWER,
                              help='disable starting viewer')

    format_group.add_argument('-o',
                              '--outfile',
                              dest=OUT_FILE,
                              metavar='FILE',
                              help='write image to specified file')
    format_group.add_argument('-O',
                              '--no-outfile',
                              default=None,
                              action='store_false',
                              dest=OUT_FILE,
                              help='disable writing image to file')

    format_group.add_argument('-w',
                              '--wait',
                              type=float,
                              dest=WAIT_SECONDS,
                              metavar='SECONDS',
                              help='\n'.join(
                                  textwrap.wrap(
                                      'wait for SECONDS seconds before deleting the temporary file'
                                      ' that is opened using the viewer command'
                                      f' (default: {OUTPUT_DEFAULTS[WAIT_SECONDS]} seconds)'
                                      '; this helps e.g. with '
                                      'viewer commands that tell other running processes '
                                      'to open that file on their behalf'
                                      ', to then shut themselves down',
                                      width=57)))

    filter_group = parser.add_argument_group("filter options",
                                             "Options to control commit/ref selection")

    # commit/ref selection -- filtering options
    filter_group.add_argument('-a',
                              '--all',
                              default=None,
                              action='store_true',
                              dest='all_commits',
                              help='include all commits')

    filter_group.add_argument('-b',
                              '--branches',
                              default=None,
                              action='store_true',
                              dest=BRANCHES,
                              help='show commits pointed to by branches')
    filter_group.add_argument('-B',
                              '--no-branches',
                              default=None,
                              action='store_false',
                              dest=BRANCHES,
                              help='do not show commits pointed to by branches')

    filter_group.add_argument('-t',
                              '--tags',
                              default=None,
                              action='store_true',
                              dest=TAGS,
                              help='show commits pointed to by tags')
    filter_group.add_argument('-T',
                              '--no-tags',
                              default=None,
                              action='store_false',
                              dest=TAGS,
                              help='do not show commits pointed to by tags')

    filter_group.add_argument('-r',
                              '--roots',
                              default=None,
                              action='store_true',
                              dest=ROOTS,
                              help='show root commits')
    filter_group.add_argument('-R',
                              '--no-roots',
                              default=None,
                              action='store_false',
                              dest=ROOTS,
                              help='do not show root commits')

    filter_group.add_argument('-m',
                              '--merges',
                              default=None,
                              action='store_true',
                              dest=MERGES,
                              help='include merge commits')
    filter_group.add_argument('-M',
                              '--no-merges',
                              default=None,
                              action='store_false',
                              dest=MERGES,
                              help='do not include merge commits')

    filter_group.add_argument('-i',
                              '--bifurcations',
                              default=None,
                              action='store_true',
                              dest=BIFURCATIONS,
                              help='include bifurcation commits')
    filter_group.add_argument('-I',
                              '--no-bifurcations',
                              default=None,
                              action='store_false',
                              dest=BIFURCATIONS,
                              help='do not include bifurcation commits')

    filter_group.add_argument('-c',
                              '--commit-messages',
                              default=None,
                              action='store_true',
                              dest=MESSAGES,
                              help='include commit messages on labels')
    filter_group.add_argument('-C',
                              '--no-commit-messages',
                              default=None,
                              action='store_false',
                              dest=MESSAGES,
                              help='do not include commit messages on labels')

    # miscellaneous options
    parser.add_argument('--pstats',
                        dest='pstats_outfile',
                        metavar='FILE',
                        help='run cProfile profiler writing pstats output to FILE')

    parser.add_argument('-d',
                        '--debug',
                        action='store_true',
                        dest='debug',
                        help='activate debug output')

    # NOTE: This would have nargs='?' but we're using nargs='*'
    #       here so that we can provide a custom error message
    #       and exit code in function ``parse_variable_args``.
    parser.add_argument('repo_dirs',
                        metavar='REPOSITORY',
                        nargs='*',
                        help='path to the Git working directory'
                        '\n(default: current directory)')

    return parser


def barf(message, exit_code):
    """ Abort execution with error message and exit code.

    Parameters
    ----------
    message : string
        error message
    exit_code : int
        exit code for program

    """
    sys.stderr.write('fatal: %s\n' % message)
    sys.exit(exit_code)


def warn(message):
    """ Print a warning message.

    Parameters
    ----------
    message : string
        the warning

    """
    sys.stderr.write('warning: %s\n' % message)


def debug(message):
    """ Print a debug message.

    Parameters
    ----------
    message : string
        the debug message

    """
    if DEBUG:
        sys.stdout.write('debug:   %s\n' % message)


def parse_variable_args(args):
    """ Parse arguments and get repo_dir.

    Parameters
    ----------
    args : list
        arguments given on command line

    Returns
    -------
    repo_dir : path
        path to the repo_dir

    """
    if len(args) > 1:
        barf('Too many arguments: %s' % args, EXIT_CODES["too_many_args"])
    return args[0] if len(args) == 1 else os.getcwd()


def run_dot(output_format, dot_file_lines):
    """ Run the 'dot' utility.

    Parameters
    ----------
    output_format : string
        format of output [svg, png, ps, pdf, ...]
    dot_file_lines : list of strings
        graphviz input lines

    Returns
    -------
    Raw output from 'dot' utility

    """
    try:
        p = subprocess.Popen(['dot', '-T' + output_format],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    except OSError as e:
        if e.errno == 2:
            barf("'dot' not found! Please install the Graphviz utility.",
                 EXIT_CODES["dot_not_found"])
        else:
            barf("A problem occured calling 'dot -T%s'" % output_format,
                 EXIT_CODES["problem_with_dot"])

    # send dot input, automatically receive and store output and error
    out, err = p.communicate(input='\n'.join(dot_file_lines).encode('utf-8'))
    if p.returncode != 0:
        barf(
            "'dot' terminated prematurely with error code %d;\n"
            "probably you specified an invalid format, see 'man dot'.\n"
            "The error from 'dot' was:\n"
            ">>>%s" % (p.returncode, err.decode('utf-8')), EXIT_CODES["dot_terminated_early"])
    return out


def write_to_file(output_file, dot_output):
    """ Write the output from the 'dot' utility to file.

    Parameters
    ----------
    output_file : string
        filename of output file
    dot_output : list of strings
        raw output from the 'dot' utility

    """
    try:
        f = open(output_file, 'wb+')
    except OSError as e:
        barf(f"Could not open file '{output_file}':\n>>>{e}", EXIT_CODES["not_write_to_file"])
    f.write(dot_output)
    f.flush()
    os.fsync(f.fileno())
    f.close()


def show_in_viewer(output_file, viewer):
    """ Show the output of 'dot' utility in a viewer.

    If 'output' is a file, open viewer on that file, else assume its the raw
    output from the 'dot' utility, write that to a temporary file, and open
    viewer on that.

    Parameters
    ----------
    output_file : str
        name of the output file
    viewer : string
        name of the viewer to use

    """
    try:
        subprocess.call([viewer, output_file])
    except OSError as e:
        barf(f"Error calling viewer: '{viewer}':\n>>>{e}", EXIT_CODES["no_such_viewer"])


def guess_format_from_filename(output_file):
    """ Guess the output format from the filename.

    Parameters
    ----------
    output_file : string
        filename of the output file

    Returns
    -------
    has_suffix : boolean
        True if the filename had a suffix, False otherwise
    guess:
        the format guess if the filename has a suffix and None otherwise

    """
    if '.' in output_file:
        return True, output_file.split('.')[-1]
    else:
        return False, None


def parse_output_options(opts):
    cmdline_settings = {}
    for setting in OUTPUT_SETTINGS:
        if setting == FORMAT:
            continue
        cmdline_settings[setting] = getattr(opts, setting)
    val = getattr(opts, FORMAT)
    cmdline_settings[FORMAT] = val if val is not None else None
    return cmdline_settings


def parse_filter_options(opts, SETTINGS):
    """ Extract and check  options from the command line 'opts'.

    Checks that not both the option and it's negation were found. The return
    dict contains one entry for each setting. This entry can be True to signal
    the option was found, False to signal the negation was found and None to
    signal that neither was found.

    Parameters
    ----------
    opts : dict
        options dict from cmdline

    Returns
    -------
    cmdline_settings : dict
        the settings dict

    """
    cmdline_settings = {}
    for setting in SETTINGS:
        cmdline_settings[setting] = getattr(opts, setting)
    return cmdline_settings


def set_settings(settings, defaults, conf, cli):
    """ Extract the value for setting in order.

    If any of the 'containers' are None, it will be skipped.

    Parameters
    ----------
    setting : list of str
        the settings to look for
    defaults : dict
        defaults
    conf : dict
        configuration file
    cli : dict like
        command line settings

    Returns
    -------
    val : str
        an appropriate value for setting

    """
    order = [('defaults', defaults), ('conf file', conf), ('command line args', cli)]
    output = {}
    for setting in settings:
        prev, val, prev_val = None, None, None
        for desc, container in order:
            if container is None:
                continue
            if container[setting] is not None:
                prev_val, val = val, container[setting]
                if prev_val is not None:
                    debug("Value for '%s' found in '%s', overrides setting '%s' from '%s': '%s'" %
                          (setting, desc, prev_val, prev, val))
                else:
                    debug(f"Value for '{setting}' found in '{desc}': '{val}'")
            prev = desc
        if val is None:
            debug("No value for '%s' found anywhere" % setting)
        output[setting] = val
    return output


def get_command_output(command_list, cwd=None, git_env=None):
    """ Execute arbitrary commands.

    Parameters
    ----------
    command_list : list of strings
        the command and its arguments
    cwd : string
        current working directory to execute command in
    git_env : dict
        the git environment, if any

    Returns
    -------
    output : string
        the raw output of the command executed
    """
    p = subprocess.Popen(command_list,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         env=git_env,
                         cwd=cwd)
    load = p.stdout.read().decode('utf-8')
    p.stdout.close()
    p.stderr.close()
    p.wait()
    if p.returncode:
        err = p.stderr.read()
        err = '\n'.join(('> ' + e) for e in err.split('\n'))
        raise Exception('Stderr:\n%s\nReturn code %d from command "%s"' %
                        (err, p.returncode, ' '.join(command_list)))
    return load


class Git:
    def __init__(self, repo_dir):

        self.repo_dir = repo_dir
        # under the assumption that if git rev-parse fails
        # it really is not a git repo
        try:
            self(['git', 'rev-parse'])
        except Exception:
            barf("'%s' is probably not a Git repository" % self.repo_dir,
                 EXIT_CODES['no_git_repo'])

    def __call__(self, argv):
        return get_command_output(argv, cwd=self.repo_dir).splitlines()

    def config(self, settings):
        config_settings = {}
        for setting in settings:
            try:
                val = self(['git', 'config', f'big-picture.{setting}'])[0]
            except Exception:
                val = None

            # We need to keep the result of "git config big-picture.wait 1"
            # from ending up as boolean True a few lines below
            if setting == WAIT_SECONDS and val is not None:
                try:
                    config_settings[setting] = float(val)
                except ValueError:
                    debug(f"Could not convert {val!r} to float")
                    config_settings[setting] = None
                continue

            if val is None:
                config_settings[setting] = None
            elif val.lower() in ['1', 'yes', 'true', 'on']:
                config_settings[setting] = True
            elif val.lower() in ['0', 'no', 'false', 'off']:
                config_settings[setting] = False
            else:
                config_settings[setting] = val
        return config_settings

    def get_mappings(self):
        """ Get mappings for all refs.

        This is implemented using a single call to 'git for-each-ref'. Note
        that it can handle non commit tags too and returns these

        Returns
        -------
        (lbranches, rbranches, abranches), (tags, ctags, nctags)

        lbranches : dict mapping strings to sets of strings
            mapping of commit sha1s to local branch names
        rbranches : dict mapping strings to sets of strings
            mapping of commit sha1s to remote branch names
        abranches : dict mapping strings to sets of strings
            mapping of commit sha1s to all branch names
        tags : dict mapping strings to sets of strings
            mapping of object sha1s to tag names
        ctags : dict mapping sha1s to sets of strings
            mapping of commits sha1s to tag names
        nctags : dict mapping sha1s to sets of strings
            mapping of non-commit sha1s to sets of strings
        """

        ref_format = '[%(objectname), %(*objectname), %(objecttype), %(refname)]'
        output = self(['git', 'for-each-ref', f'--format={ref_format}', '--python'])
        lbranch_prefix = 'refs/heads/'
        rbranch_prefix = 'refs/remotes/'
        tag_prefix = 'refs/tags/'
        lbranches, rbranches, abranches = {}, {}, {}
        tags, ctags, nctags = {}, {}, {}

        def add_to_dict(dic, sha1, name):
            dic.setdefault(sha1, set()).add(name)

        for ref_info in output:
            sha1, tag_sha1, ref_type, name = ast.literal_eval(ref_info)
            if ref_type not in ['commit', 'tag']:
                continue
            elif name.startswith(lbranch_prefix):
                add_to_dict(lbranches, sha1, name.replace(lbranch_prefix, ''))
                add_to_dict(abranches, sha1, name.replace(lbranch_prefix, ''))
            elif name.startswith(rbranch_prefix):
                add_to_dict(rbranches, sha1, name.replace(rbranch_prefix, ''))
                add_to_dict(abranches, sha1, name.replace(rbranch_prefix, ''))
            elif name.startswith(tag_prefix):
                # recusively dereference until we find a non-tag object
                sha1 = self(['git', 'rev-parse', '%s^{}' % name])[0]
                # determine object type and to respective dict
                obj_type = self(['git', 'cat-file', '-t', sha1])[0]
                if obj_type in ['blob', 'tree']:
                    add_to_dict(nctags, sha1, name.replace(tag_prefix, ''))
                else:
                    add_to_dict(ctags, sha1, name.replace(tag_prefix, ''))
                add_to_dict(tags, sha1, name.replace(tag_prefix, ''))

        return (lbranches, rbranches, abranches), (tags, ctags, nctags)

    def get_parent_map(self):
        """ Get a mapping of children to parents.

        Returns
        -------
        parents : dict mapping strings to sets of strings
            mapping of children sha1s to parents sha1
        """

        parents = {}
        lines = self(['git', 'rev-list', '--all', '--parents'])
        for line in lines:
            sha_ones = [e.group(0) for e in re.finditer(sha1_pattern, line)]
            count = len(sha_ones)
            if count > 1:
                parents[sha_ones[0]] = set(sha_ones[1:])
            elif count == 1:
                parents[sha_ones[0]] = set()
        return parents


def graph_factory(repo_dir):
    """ Create a CommitGraph object from a git_dir. """
    git = Git(repo_dir)
    (lb, rb, ab), (tags, ctags, nctags) = git.get_mappings()
    return CommitGraph(git.get_parent_map(), ab, tags, git=git)


class CommitGraph:
    """ Directed Acyclic Graph (DAG) git repository.

    Parameters
    ----------
    parent_map : dict mapping SHA1s to list of SHA1s
        the parent map
    branch_dict : dict mapping SHA1s to list of strings
        the branches
    tag_dict : dict mapping SHA1s to list of strings
        the tags

    Properties
    ----------
    roots : list of SHA1s
        all root commits (the ones with no parents)
    merges : list of SHA1s
        all merge commits (the ones with multiple parents)
    bifurcations : list SHA1s
        all bifurcation commits (the ones with multiple children)

    Attributes
    ----------
    parents : dict mapping SHA1s to list of SHA1s
        the parent map
    children : dict mapping SHA1s to list of SHA1s
        the child map
    branches : dict mapping SHA1s to list of strings
        the branches
    tags : dict mapping SHA1s to list of strings
        tags
    git : Git
        interface to dispatch commands to this repo

    """
    def __init__(self, parent_map, branch_dict, tag_dict, git=None):
        self.parents = parent_map
        self.branches = branch_dict
        self.tags = tag_dict
        self.dotdot = set()
        self.git = git

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
                    assert (p in self.parents[c])
        for sha_one, chs in self.children.items():
            for c in chs:
                for p in self.parents[c]:
                    assert (c in self.children[p])

    @property
    def roots(self):
        """ Find all root commits. """
        return [sha for sha, parents in self.parents.items() if not parents]

    @property
    def merges(self):
        """ Find all merge commits. """
        return [sha for sha, parents in self.parents.items() if len(parents) > 1]

    @property
    def bifurcations(self):
        """ Find all bifurcations. """
        return [sha for sha, children in self.children.items() if len(children) > 1]

    def filter(self,
               branches=FILTER_DEFAULTS[BRANCHES],
               tags=FILTER_DEFAULTS[TAGS],
               roots=FILTER_DEFAULTS[ROOTS],
               merges=FILTER_DEFAULTS[MERGES],
               bifurcations=FILTER_DEFAULTS[BIFURCATIONS],
               additional=None):
        """ Filter the commit graph.

        Remove, or 'filter' the unwanted commits from the DAG. This will modify
        self.parents and when done re-calculate self.children. Keyword
        arguments can be used to specify 'interesting' commits

        Generate a reachability graph for 'interesting' commits. This will
        generate a graph of all interesting commits, with edges pointing to all
        reachable 'interesting' parents.

        Parameters
        ----------
        branches : bool
            include commits being pointed to by branches
        tags : bool
            include commits being pointed to by tags
        roots : bool
            include root commits
        merges : bool
            include merge commits
        bifurcations : bool
            include bifurcation commits
        additional : list of SHA1 sums
            any additional commits to include

        Returns
        -------
        commit_graph : CommitGraph
            the filtered graph

        """
        interesting = []
        if branches:
            interesting.extend(self.branches.keys())
        if tags:
            interesting.extend(self.tags.keys())
        if roots:
            interesting.extend(self.roots)
        if merges:
            interesting.extend(self.merges)
        if bifurcations:
            interesting.extend(self.bifurcations)
        if additional:
            interesting.extend(additional)

        reachable_interesting_parents = dict()
        # for everything that we are interested in
        for commit_i in interesting:
            # Handle tags pointing to non-commits
            if commit_i in self.parents:
                to_visit = list(self.parents[commit_i])
            else:
                to_visit = list()
            # create the set of seen commits
            seen = set()
            # initialise the parents for this commit_i
            reachable_interesting_parents[commit_i] = set()
            # iterate through to_visit list, i.e. go searching in the graph
            for commit_j in to_visit:
                # we have already been here
                if commit_j in seen:
                    continue
                else:
                    seen.add(commit_j)
                    if commit_j in interesting:
                        # is interesting, add and stop
                        reachable_interesting_parents[commit_i].add(commit_j)
                    else:
                        # is not interesting, keep searching
                        to_visit.extend(self.parents[commit_j])

        return CommitGraph(reachable_interesting_parents, copy.deepcopy(self.branches),
                           copy.deepcopy(self.tags), self.git)

    def _minimal_sha_one_digits(self):
        """ Calculate the minimal number of sha1 digits required to represent
        all commits unambiguously. """
        key_count = len(self.parents)
        for digit_count in range(7, 40):
            if len({e[0:digit_count] for e in self.parents.keys()}) == key_count:
                return digit_count
        return 40

    def _generate_dot_file(self,
                           sha_ones_on_labels,
                           with_commit_messages,
                           sha_one_digits=None,
                           history_direction=None):
        """ Generate graphviz input.

        Parameters
        ----------
        sha_ones_on_labels : boolean
            if True show sha1 (or minimal) on labels in addition to ref names
        with_commit_messages : boolean
            if True the commit messages are displyed too
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

        def format_label(sha_one):
            if with_commit_messages:
                output = self.git(['git', 'log', '-1', '--pretty=format:%s', sha_one])
                message = output[0].replace('"', '').replace('\'', '')
                return format_sha_one(sha_one) + '\n' + message
            else:
                return format_sha_one(sha_one)

        def label_gen():
            keys = set(self.branches.keys()).union(set(self.tags.keys()))
            for k in (k for k in keys if k in self.parents or k in self.children):
                labels = []
                case = 0
                if k in self.tags:
                    case = case + 1
                    labels.extend(sorted(self.tags[k]))
                if k in self.branches:
                    case = case + 2
                    labels.extend(sorted(self.branches[k]))
                # http://www.graphviz.org/doc/info/colors.html
                color = "/pastel13/%d" % case
                yield (k, labels, color)

        dot_file_lines = ['digraph {']
        if history_direction is not None:
            rankdir = RANKDIR_OF_HISTORY_DIRECTION[history_direction]
            dot_file_lines.append(f'\trankdir="{rankdir}";')
        for sha_one, labels, color in label_gen():
            label = '\\n'.join(labels + ((with_commit_messages or sha_ones_on_labels) and [
                format_label(sha_one),
            ] or list()))
            label = label.replace('"', '\\"')
            dot_file_lines.append(
                f'\t"{sha_one}"[label="{label}", color="{color}", style=filled];')
        for sha_one in self.dotdot:
            dot_file_lines.append(f'\t"{sha_one}"[label="..."];')
        if (sha_one_digits is not None) and (sha_one_digits != 40):
            for sha_one in (e for e in self.parents.keys()
                            if not (self._has_label(e) or e in self.dotdot)):
                sha_label = format_label(sha_one)
                dot_file_lines.append(f'\t"{sha_one}"[label="{sha_label}"];')
        for child, self.parents in self.parents.items():
            for p in self.parents:
                dot_file_lines.append(f'\t"{child}" -> "{p}";')
        dot_file_lines.append('}')
        return dot_file_lines


def innermost_main(opts):
    repo_dir = parse_variable_args(opts.repo_dirs)
    debug("The Git repository is at: '%s'" % repo_dir)
    graph = graph_factory(repo_dir)
    output_settings = set_settings(OUTPUT_SETTINGS, OUTPUT_DEFAULTS,
                                   graph.git.config(OUTPUT_SETTINGS), parse_output_options(opts))
    filter_settings = set_settings(FILTER_SETTINGS, FILTER_DEFAULTS,
                                   graph.git.config(FILTER_SETTINGS),
                                   parse_filter_options(opts, FILTER_SETTINGS))
    annotation_settings = set_settings(ANNOTATION_SETTINGS, ANNOTATION_DEFAULTS,
                                       graph.git.config(ANNOTATION_SETTINGS),
                                       parse_filter_options(opts, ANNOTATION_SETTINGS))
    if opts.all_commits:
        sha_one_digits = graph._minimal_sha_one_digits()
    else:
        sha_one_digits = None
        graph = graph.filter(**filter_settings)
        sha_one_digits = graph._minimal_sha_one_digits()

    dot_file_lines = graph._generate_dot_file(
        sha_ones_on_labels=opts.all_commits,
        with_commit_messages=annotation_settings['messages'],
        sha_one_digits=sha_one_digits,
        history_direction=opts.history_direction,
    )

    if (output_settings[GRAPHVIZ] and output_settings[PROCESSED]):
        barf("Options '-g | --graphviz' and '-p | --processed' " + "are mutually exclusive.",
             EXIT_CODES["graphviz_processed_others"])
    elif (output_settings[GRAPHVIZ] or output_settings[PROCESSED]) and (output_settings[VIEWER] or
                                                                        output_settings[OUT_FILE]):
        barf(
            "Options '-g | --graphviz' and '-p | --processed' "
            + "are incompatible with other output options.",
            EXIT_CODES["graphviz_processed_others"])
    elif not any([
            output_settings[GRAPHVIZ], output_settings[PROCESSED], output_settings[VIEWER],
            output_settings[OUT_FILE]
    ]):
        barf("Must provide an output option. Try '-h' for more information",
             EXIT_CODES["no_options"])
    # if plain just print dot input to stdout
    if output_settings[GRAPHVIZ]:
        debug('Will now print dot format')
        for line in dot_file_lines:
            print(line)
        return
    # check for format mismatch between -f and -o
    if output_settings[FORMAT] and output_settings[OUT_FILE]:
        (has_suffix, guess) = guess_format_from_filename(output_settings[OUT_FILE])
        if output_settings[FORMAT] != guess and guess is not None:
            debug("Format mismatch: '%s'(-f|--format or default)"
                  "vs. '%s'(filename), will use: "
                  "'%s'" % (output_settings[FORMAT], guess, guess))
            output_settings[FORMAT] = guess
        if guess is None:
            warn('Filename had no suffix, using format: %s' % output_settings[FORMAT])
            output_settings[OUT_FILE] += '.' + output_settings[FORMAT]
    # run the 'dot' utility
    dot_output = run_dot(output_settings[FORMAT], dot_file_lines)
    # create outfile and possibly view that or a temporary file in viewer
    if output_settings[VIEWER] or output_settings[OUT_FILE]:
        # no output file requested, create a temporary one
        temporary_file = None
        try:
            if not output_settings[OUT_FILE]:
                temporary_file = tempfile.NamedTemporaryFile(prefix='git-big-picture-',
                                                             suffix='.' + output_settings[FORMAT])
                output_settings[OUT_FILE] = temporary_file.name
                debug("Created temp file: '%s'" % output_settings[OUT_FILE])
            debug("Writing to file: '%s'" % output_settings[OUT_FILE])
            write_to_file(output_settings[OUT_FILE], dot_output)
            if output_settings[VIEWER]:
                debug("Will now open file in viewer: '%s'" % output_settings[VIEWER])
                if temporary_file is not None:
                    wait_until = time.time() + max(0, output_settings[WAIT_SECONDS])
                show_in_viewer(output_settings[OUT_FILE], output_settings[VIEWER])
                if temporary_file is not None:
                    # NOTE: The idea is to sleep for WAIT_SECONDS minus the process runtim
                    #       duration.  As a result, for a long-running process we don't wait
                    #       any more than necessary.
                    sleep_time = wait_until - time.time()
                    if sleep_time > 0:
                        debug("Now sleeping for %0.1f seconds" % sleep_time)
                        time.sleep(sleep_time)
        finally:
            if temporary_file is not None:
                debug(f"Removing temp file: {temporary_file.name!r}")
                temporary_file.close()  # also removes the file
    elif output_settings[PROCESSED]:
        debug("Will now print dot processed output in format: '%s'" % output_settings[FORMAT])
        print(dot_output)


def inner_main():
    opts = create_parser().parse_args()

    if opts.debug:
        global DEBUG
        DEBUG = True
        debug('Activate debug')

    try:
        get_command_output(['git', '--help'])
    except Exception as e:
        barf("git is either not installed or not on your $PATH:\n>>>%s" % e, EXIT_CODES["no_git"])

    if opts.pstats_outfile is not None:
        import cProfile
        debug("Running in profiler, output is: '%s'" % opts.pstats_outfile)
        cProfile.runctx('innermost_main(opts)', globals(), locals(), opts.pstats_outfile)
    else:
        innermost_main(opts)


def main():
    try:
        inner_main()
    except KeyboardInterrupt:
        sys.exit(EXIT_CODES['killed_by_sigint'])


if __name__ == '__main__':
    main()
