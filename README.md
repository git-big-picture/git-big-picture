Program Description
===================

Git-big-picture is a visualization for Git repositories. You can think of it as
a filter that removes uninteresting commits from a DAG modelling a Git
repository and thereby exposes the big picture: the hierarchy of tags and
branches.

A Small Example
---------------

Imagine the follwing Graph:

                 0.1.1   0.1.2
                   |       |
    0.0    G---H---I---J---K---L---M maint
     |    /
     A---B---C---D---E---F master
         |    \         /
        0.1    N---O---P topic


Where the following commits have Branches and Tags:

    A -> 0.0
    B -> 0.1
    F -> master
    I -> 0.1.1
    K -> 0.1.2
    M -> maint
    P -> topic

The *reduced* graph of *interesting* commits would be:

          I---K---M
         /
    A---B---F
         \ /
          L

But since the commits would be labeled with their refs, it would look more like
(within the lmits of ascii art):

          0.1.1---0.1.2---maint
         /
    0.0---0.1---master
            \     /
             topic

Dependencies
============

* Python 2.6 (2.5 will not work, 2.7 may work)
* Git (1.7.1 works)
* Graphviz utility
* Nosetest (only for running tests)

Installation
============

Just run it straight from a clone or download:

    $ git clone git://git.goodpoint.de/git-big-picture.git
    $ cd git-big-picture
    $ ./git-big-picture --help

Alternatively, use the standard `setup.py` script to install it system wide.

    $ ./setup.py install
    (may need root privileges)

Internals
=========

The graph operations are written in Python and output the graph-data in the
easy-to-write Graphviz syntax. This is converted into an image using the
Graphviz `dot` utility. Graphviz supports a multitude of image formats, e.g. SVG
and PDF. Check that Graphviz is installed by invoking: `dot -V`.

Usage
=====

    $ ./git-big-picture --help
    Usage: git-big-picture -p | [-f <format>] [-v <viewer>] [-o <outfile>] [<repo-directory>]

    Options:
    --version             show program's version number and exit
    -h, --help            show this help message and exit
    -a, --all             include all commits (not just tags and branch heads)
    --some                include all commits but linear runs
    -p, --plain           output lines suitable as input for dot
    -f FMT, --format=FMT  set output format [svg, png, ps, pdf, ...]
    -v CMD, --viewer=CMD  write image to tempfile and start specified viewer
    -o FILE, --out=FILE   write image to specified file
    --pstats=FILE         run cProfile profiler writing pstats output to FILE


Usage Examples
==============

Output Graphviz synatx:

    $ ./git-big-picture -p

Output raw Graphviz output (i.e. the image)

    $ ./git-big-picture -f svg

Generate PNG version of current Git repository and save to `our-project.png`:

    $ ./git-big-picture -o our-project.png

If you specify the format and a filename with extension, the filename extension will
be used:

    $ ./git-big-picture -f svg -o our-project.png
    warning: Format mismatch: 'svg'(-f|--format)vs. 'png'(filename), will use: 'png'

If you don't have an extension, you could still specify a format:

    $ ./git-big-picture -f pdf -o our-project
    warning: Filename had no suffix, using format: pdf

Otherwise the default format SVG is used:

    ./git-big-picture -o our-project
    warning: Filename had no suffix, using default format: svg

Generate SVG (default format) graph of the repository in `~/git-repo` and view the
result in firefox:

    $ ./git-big-picture -v firefox ~/git-repo/

If you would like to use an alternative viewer, specify viewer and its format:

    $ ./git-big-picture -f pdf -v xpdf

You can also open the viewer automatically on the output file:

    $ ./git-big-picture -v xpdf -o our-project.pdf

Manually pipe the Graphviz commands to the `dot` utility:

    $ ./git-big-picture --plain ~/git-repo | dot -Tpng -o graph.png

Without any output options, the script will print its usage and exit.


Git Integration
===============

You can easily integrate this script as a regular Git command, by making the
script `git-big-picture` available on the `$PATH`. For instance: using
`./setup.py install` method as described above should do the trick. Alternatively symlink
`git-big-picture` into a directory listed in your `$PATH`, for example `$HOME/bin`.

You may then use `git big-picture` (w/o the first dash) as you would any other Git command:

    $ git big-picture -f pdf -v xpdf -o visualization.pdf

This will present you with a PDF viewer displaying your project's
graph, and stores this PDF in a file called `visualization.pdf`.

Testing
=======

Run the Python based test-suite with:

    $ ./setup.py test

Or alternatively use `nosetest` directly:

    $ nosetest

Also there are some basic calls to the cli. There are not checked against
predefined out though.

    $ ./test-cli.sh

Profiling
=========

There are two ways to profile git-big-picture, using the built-in `--pstats`
option or using the Python module `cProfile`:

Using `--pstats`:

    $ ./git-big-picture --pstats=profile-stats -o graph.svg

Profile the script with `cProfile`

    $ python -m cProfile -o profile-stats git-big-picture -o graph.svg

In either case, you can then use the excellent visualisation tool `gprof2dot`
which, incidentally, outputs Graphviz syntax too:

    $ gprof2dot -f pstats profile-stats | dot -Tsvg -o profile_stats.svg

License
=======

Licensed under GPL v3 or later, see file COPYING for details.

Authors/Contributors
====================

* Sebastian Pipping  <sebastian@pipping.org>
* Julius Plenz       <julius@plenz.com>
* Valentin Haenel    <valentin.haenel@gmx.de>
* Yaroslav Halchenko <debian@onerussian.com>

