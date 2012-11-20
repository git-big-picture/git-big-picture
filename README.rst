git-big-picture
===============

``git-big-picture`` is a visualization tool for Git repositories. You can think
of it as a filter that removes uninteresting commits from a DAG modelling a Git
repository and thereby exposes the big picture: for example the hierarchy of
tags and branches. ``git-big-picture`` supports conveniece output options and
can filter different classes of commits. It uses the Graphviz utility to render
images that are pleasing to the eye.

A Small Example
---------------

Imagine the following Graph:

.. code::

             0.1.1   0.1.2
               |       |
    0.0    G---H---I---J---K---L---M maint
     |    /
     A---B---C---D---E---F master
         |    \         /
        0.1    N---O---P topic


Where the following commits have Branches and Tags:

.. code::

    A -> 0.0
    B -> 0.1
    F -> master
    H -> 0.1.1
    J -> 0.1.2
    M -> maint
    P -> topic

The *reduced* graph of *interesting* commits would be:

.. code::

          H---J---M
         /
    A---B---F
         \ /
          P

But since the commits would be labeled with their refs, it would look more like
(within the limits of ascii art):

.. code::

          0.1.1---0.1.2---maint
         /
    0.0---0.1---master
            \     /
             topic

Screenshots
-----------

Courtesy of Graphviz, ``git-big-picture`` can output nice images.

Here is the original repository from the example above:

.. image:: https://raw.github.com/esc/git-big-picture/master/screenshots/before.png
    :height: 280px
    :width:  456px

And here is the reduced version:

.. image:: https://raw.github.com/esc/git-big-picture/master/screenshots/after.png
    :height: 280px
    :width:  456px

We also have a real world examples from:

* `cython <http://imgdump.zetatech.org/cython-big-picture.png>`_
* `PyMVPA <http://imgdump.zetatech.org/pymvpa-big-picture.png>`_
* `bloscpack <http://imgdump.zetatech.org/bloscpack-big-picture.png>`_

Dependencies
------------

* Python 2.6 or 2.7 (2.5 will not work, if you try it with 3.3 let us know)
* Git (1.7.1 works)
* Graphviz utility
* Nosetest and Cram (only for running tests)

Installation
------------

Just run it straight from a clone or download:

.. code:: shell

    $ git clone git://github.com/esc/git-big-picture.git
    $ cd git-big-picture
    $ ./git-big-picture --help

    $ wget https://raw.github.com/esc/git-big-picture/master/git-big-picture
    $ ./git-big-picture -h

Alternatively, use the standard ``setup.py`` script to install it system wide
or just for the user.

.. code:: shell

    $ ./setup.py install
    (may need root privileges)
    $ ./setup.py install --user

Git Integration
---------------

You can easily integrate this script as a regular Git command, by making the
script ``git-big-picture`` available on the ``$PATH``. For instance: using
``./setup.py install`` method, as described above should do the trick.
Alternatively symlink or copy ``git-big-picture`` into a directory listed in
your ``$PATH``, for example ``$HOME/bin``.

You may then use ``git big-picture`` (w/o the first dash) as you would any other Git command:

.. code:: shell

    $ git big-picture -h

Or create an alias:

.. code:: shell

    $ git config --global alias.bp big-picture
    $ git bp -h

Internals
---------

The graph operations are written in Python and output the graph-data in the
easy-to-write Graphviz syntax. This is converted into an image using the
Graphviz ``dot`` utility. Graphviz supports a multitude of image formats, e.g. SVG
and PDF. Check that Graphviz is installed by invoking: ``dot -V``.

Usage
-----

.. code:: shell

    $ git-big-picture --help
    Usage: git-big-picture OPTIONS [<repo-directory>]

    Options:
    --version             show program's version number and exit
    -h, --help            show this help message and exit
    --pstats=FILE         run cProfile profiler writing pstats output to FILE
    -d, --debug           activate debug output

    Output Options:
        Options to control output and format

        -f FMT, --format=FMT
                            set output format [svg, png, ps, pdf, ...]
        -g, --graphviz      output lines suitable as input for dot/graphviz
        -G, --no-graphviz   disable dot/graphviz output
        -p, --processed     output the dot processed, binary data
        -P, --no-processed  disable binary output
        -v CMD, --viewer=CMD
                            write image to tempfile and start specified viewer
        -V, --no-viewer     disable starting viewer
        -o FILE, --outfile=FILE
                            write image to specified file
        -O, --no-outfile    disable writing image to file

    Filter Options:
        Options to control commit/ref selection

        -a, --all           include all commits
        -b, --branches      show commits pointed to by branches
        -B, --no-branches   do not show commits pointed to by branches
        -t, --tags          show commits pointed to by tags
        -T, --no-tags       do not show commits pointed to by tags
        -r, --roots         show root commits
        -R, --no-roots      do not show root commits
        -m, --merges        include merge commits
        -M, --no-merges     do not include merge commits
        -i, --bifurcations  include bifurcation commits
        -I, --no-bifurcations
                            do not include bifurcation commits

Usage Examples
--------------

There are two releated groups of options, the output and the filter options.
Output options govern the output and format produced by the tool. Filter
options govern which commits to include when calculating the reduced graph.

Using Output Options
....................

Output Graphviz syntax:

.. code:: shell

    $ git-big-picture -g

Output raw Graphviz output (i.e. the image)

.. code:: shell

    $ git-big-picture -p

Generate PNG version of current Git repository and save to ``our-project.png``:

.. code:: shell

    $ git-big-picture -o our-project.png

If you specify the format and a filename with extension, the filename extension will
be used:

.. code:: shell

    $ git-big-picture -f svg -o our-project.png
    $ ls
    our-project.png

If you don't have an extension, you could still specify a format:

.. code:: shell

    $ git-big-picture -f pdf -o our-project
    warning: Filename had no suffix, using format: pdf

Otherwise the default format SVG is used:

.. code:: shell

    git-big-picture -o our-project
    warning: Filename had no suffix, using default format: svg

Generate SVG (default format) graph of the repository in ``~/git-repo`` and view the
result in firefox:

.. code:: shell

    $ git-big-picture -v firefox ~/git-repo/

If you would like to use an alternative viewer, specify viewer and its format:

.. code:: shell

    $ git-big-picture -f pdf -v xpdf

You can also open the viewer automatically on the output file:

.. code:: shell

    $ git-big-picture -v xpdf -o our-project.pdf

Manually pipe the Graphviz commands to the ``dot`` utility:

.. code:: shell

    $ git-big-picture --graphviz ~/git-repo | dot -Tpng -o graph.png

Using Filter Options
....................

The three options ``--branches`` ``--tags`` and ``--roots`` are active by
default. You can use the negation switches to turn them off. These use the
uppercase equivalent of the short option and the prefix ``no-`` for the long
option. For example: ``-B | --no-branches`` to deactivate showing branches.

Show all interesting commits, by showing also merges and bifurcations:

.. code:: shell

    $ git-big-picture -i -m

Show only roots (deactivate branches and tags):

.. code:: shell

    $ git-big-picture -B -T

Show merges and branches only (deactivate tags):

.. code:: shell

    $ git-big-picture -m -T

Show all commits:

.. code:: shell

    $ git-big-picture -a

Configuration
-------------

The standard ``git config`` infrastructre can be used to configure
``git-big-picture``. Most of the command line arguments can be configured in a
``big-picture`` section. For example to configure ``firefox`` as a viewer

.. code:: shell

    $ git config --global big-picture.viewer firefox

Will create the following section and entry in your ``~/.gitconfig``:

.. code:: ini

    [big-picture]
        viewer = firefox


The command line negation arguments can be used to disable a setting configured
via the command line. For example, if you have configured the ``viewer`` above
and try to use the ``-g | --graphviz`` switch, you will get the following
error:

.. code:: shell

    $ git-big-picture -g
    fatal: Options '-g | --graphviz' and '-p | --processed' are incompatible with other output options.

... since you already have a viewer configured. In this case, use the negation
option ``-V | --no-viewer`` to disable the ``viewer`` setting from the config
file:

.. code:: shell

    $ git-big-picture -g -V


Testing
-------

The Python code is tested with `nose <https://nose.readthedocs.org/en/latest/>`_

.. code:: shell

    $ ./test.py

The command line interface is tested with `cram <https://bitheap.org/cram/>`_:

.. code:: shell

    $ ./test.cram

Debugging
---------

You can use the ``[-d | --debug]`` switch to debug:

.. code:: shell

    $ git-big-picture -d -v firefox


Profiling
---------

There are two ways to profile git-big-picture, using the built-in ``--pstats``
option or using the Python module ``cProfile``:

Using ``--pstats``:

.. code:: shell

    $ git-big-picture --pstats=profile-stats -o graph.svg

Profile the script with ``cProfile``

.. code:: shell

    $ python -m cProfile -o profile-stats git-big-picture -o graph.svg

In either case, you can then use the excellent visualisation tool ``gprof2dot``
which, incidentally, outputs Graphviz syntax too:

.. code:: shell

    $ gprof2dot -f pstats profile-stats | dot -Tsvg -o profile_stats.svg

TODO
----

* Sanitize the test suite
* --abbrev switch

Changelog
---------

* v0.9.0 - XXXX-XX-XX

  * rstify readme
  * Fix long standing bug in graph search algorithm
  * Fix long standing conversion from tabbed to 4-spaces
  * Overhaul and refactor the test-suite
  * Remove old ``--some`` crufy code and option
  * Add ability to find root-, merge- and bifurcation-commits
  * Overhaul command line interface with new options
  * Add command line interface tests using Cram

* v0.8.0 - 2012-11-05

  * Snapshot of all developments Mar 2010 - Now
  * Extended command line options for viewing and formatting
  * Option to filter on all, some or decorated commits
  * Simple test suite for python module and command line

License
-------

Licensed under GPL v3 or later, see file COPYING for details.

Authors/Contributors
--------------------

* Sebastian Pipping  <sebastian@pipping.org>
* Julius Plenz       <julius@plenz.com>
* Valentin Haenel    <valentin.haenel@gmx.de>
* Yaroslav Halchenko <debian@onerussian.com>

