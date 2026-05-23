[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Tests](https://github.com/git-big-picture/git-big-picture/actions/workflows/run-tests.yml/badge.svg)](https://github.com/git-big-picture/git-big-picture/actions/workflows/run-tests.yml)

> [!IMPORTANT]
> This project is in **maintenance mode**. That means that I will:
>
> - :white_check_mark: continue to apply dependency updates and bug fixes, but will
> - :no_entry_sign: not add any new features, and will
> - :no_entry_sign: not take time to review pull requests adding features
>   or making bigger changes.
>
> Thanks for your understanding! :pray:
>
> Sebastian Pipping — Berlin, 2026-05-17


# git-big-picture

`git-big-picture` is a visualization tool for Git repositories. You can
think of it as a filter that removes uninteresting commits from a DAG
modelling a Git repository and thereby exposes the big picture: for
example the hierarchy of tags and branches. `git-big-picture` supports
convenience output options and can filter different classes of commits.
It uses the Graphviz utility to render images that are pleasing to the
eye.


## A Small Example

Imagine the following Graph:

```
         0.1.1   0.1.2
           |       |
0.0    G---H---I---J---K---L---M maint
 |    /
 A---B---C---D---E---F master
     |    \         /
    0.1    N---O---P topic
```

Where the following commits have Branches and Tags:

```
A -> 0.0
B -> 0.1
F -> master
H -> 0.1.1
J -> 0.1.2
M -> maint
P -> topic
```

The *reduced* graph of *interesting* commits would be:

```
      H---J---M
     /
A---B---F
     \ /
      P
```

But since the commits would be labeled with their refs, it would look
more like (within the limits of ASCII art):

```
          0.1.1---0.1.2---maint
         /
0.0---0.1---master
         \     /
          topic
```


## Demo Video

Chuwei Lu has made a YouTube video showing how to use `git-big-picture`:

<https://www.youtube.com/watch?v=H7w7JWSy3oc>


## Screenshots

Courtesy of Graphviz, `git-big-picture` can output nice images.

Here is the original repository from the example above:

<img
src="https://raw.github.com/git-big-picture/git-big-picture/master/screenshots/before.png"
width="492" height="1043" alt="image" />

And here is the reduced version:

<img
src="https://raw.github.com/git-big-picture/git-big-picture/master/screenshots/after.png"
width="280" height="456" alt="image" />

We also have a real world examples from:

- [cython](https://raw.github.com/git-big-picture/git-big-picture/master/screenshots/cython-big-picture.png)
- [PyMVPA](https://raw.github.com/git-big-picture/git-big-picture/master/screenshots/pymvpa-big-picture.png)
- [bloscpack](https://raw.github.com/git-big-picture/git-big-picture/master/screenshots/bloscpack-big-picture.png)


## Dependencies

- Python \>=3.10
- Git (1.7.1 works)
- Graphviz utility
- pytest and Cram (only for running tests)


## Installation

As of `v0.10.1` you may install it from PyPI:

<https://pypi.org/project/git-big-picture/>

``` console
$ pip install git-big-picture
```

Alternatively, just run it straight from a Git clone:

``` console
$ git clone https://github.com/git-big-picture/git-big-picture.git
$ cd git-big-picture
$ python3 -m venv venv      # creates a virtualenv
$ source venv/bin/activate  # activates the virtualenv
$ pip install -e .          # installs to the virtualenv
$ git-big-picture --help
```

Alternatively, use pip to install it system wide or just for the user.

``` console
$ pip install .
(may need root privileges)
$ pip install --user .
```


## Git Integration

After installation using pip, you can easily integrate this script as a
regular Git command, by making sure that executable `git-big-picture` is
found during `${PATH}` lookup. E.g. you could append a line like
`export PATH="${HOME}/.local/bin:${PATH}"` to your `~/.bashrc` if you
are using Bash.

You may then use `git big-picture` (w/o the first dash) as you would any
other Git command:

``` console
$ git big-picture -h
```

Or create an alias:

``` console
$ git config --global alias.bp big-picture
$ git bp -h
```


## Internals

The graph operations are written in Python and output the graph-data in
the easy-to-write Graphviz syntax. This is converted into an image using
the Graphviz `dot` utility. Graphviz supports a multitude of image
formats, e.g. SVG and PDF. Check that Graphviz is installed by invoking:
`dot -V`.


## Usage

``` console
$ git-big-picture --help
usage: git-big-picture OPTIONS [REPOSITORY]

Visualize Git repositories

positional arguments:
  REPOSITORY            path to the Git working directory
                        (default: current directory)

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --pstats FILE         run cProfile profiler writing pstats output to FILE
  -d, --debug           activate debug output

output options:
  Options to control output and format

  -f, --format FMT      set output format [svg, png, ps, pdf, ...]
  --history-direction {downwards,leftwards,rightwards,upwards}
                        enforce a specific direction of history on Graphviz
                        (default: rightwards)
  --simplify            remove edges implied by transitivity using Graphviz
                        filter "tred" (default: do not remove implied edges)
  -g, --graphviz        output lines suitable as input for dot/graphviz
  -G, --no-graphviz     disable dot/graphviz output
  -p, --processed       output the dot processed, binary data
  -P, --no-processed    disable binary output
  -v, --viewer CMD      write image to tempfile and start specified viewer
  -V, --no-viewer       disable starting viewer
  -o, --outfile FILE    write image to specified file
  -O, --no-outfile      disable writing image to file
  -w, --wait SECONDS    wait for SECONDS seconds before deleting the temporary
                        file that is opened using the viewer command (default:
                        2.0 seconds); this helps e.g. with viewer commands that
                        tell other running processes to open that file on their
                        behalf, to then shut themselves down

filter options:
  Options to control commit/ref selection

  -a, --all             include all commits
  -b, --branches        show commits pointed to by branches
  -B, --no-branches     do not show commits pointed to by branches
  -t, --tags            show commits pointed to by tags
  -T, --no-tags         do not show commits pointed to by tags
  -r, --roots           show root commits
  -R, --no-roots        do not show root commits
  -m, --merges          include merge commits
  -M, --no-merges       do not include merge commits
  -i, --bifurcations    include bifurcation commits; a bifurcation commit is a
                        commit that is a parent to more than one other commits,
                        i.e. it marks the point where one or more new branches
                        came to life; bifurcation commits can also be thought of
                        as the counterpart of merge commits
  -I, --no-bifurcations
                        do not include bifurcation commits
  -c, --commit-messages
                        include commit messages on labels
  -C, --no-commit-messages
                        do not include commit messages on labels

git-big-picture is software libre, licensed under the GPL v3 or later license.
Please report bugs at https://github.com/git-big-picture/git-big-picture/issues — thank you!
```


## Usage Examples

There are two related groups of options, the output and the filter
options. Output options govern the output and format produced by the
tool. Filter options govern which commits to include when calculating
the reduced graph.


### Using Output Options

Generate PNG version of current Git repository and save to
`our-project.png`:

``` console
$ git-big-picture -o our-project.png
```

Generate SVG (default format) image of the repository in `~/git-repo`
and view the result in Firefox:

``` console
$ git-big-picture -v firefox ~/git-repo/
```

If you specify the format and a filename with extension, the filename
extension will be used:

``` console
$ git-big-picture -f svg -o our-project.png
$ file our-project.png
our-project.png: PNG image data, 216 x 325, 8-bit/color RGB, non-interlaced
```

If you don't have an extension, you could still specify a format:

``` console
$ git-big-picture -f pdf -o our-project
warning: Filename had no suffix, using format: pdf
```

Otherwise the default format SVG is used:

``` console
$ git-big-picture -o our-project
warning: Filename had no suffix, using default format: svg
```

If you would like to use an alternative viewer, specify viewer and its
format:

``` console
$ git-big-picture -f pdf -v xpdf
```

You can also open the viewer automatically on the output file:

``` console
$ git-big-picture -v xpdf -o our-project.pdf
```

Output raw Graphviz syntax:

``` console
$ git-big-picture -g
```

Output raw Graphviz output (i.e. the image):

``` console
$ git-big-picture -p
```

Note however, that the options in the two examples above are both
mutually exclusive and incompatible with other output options.

``` console
$ git-big-picture -g -p
fatal: Options '-g | --graphviz' and '-p | --processed' are mutually exclusive.
$ git-big-picture -g -v firefox
fatal: Options '-g | --graphviz' and '-p | --processed' are incompatible with other output options.
```

Manually pipe the Graphviz commands to the `dot` utility:

``` console
$ git-big-picture --graphviz ~/git-repo | dot -Tpng -o graph.png
```


### Using Filter Options

The three options `--branches` `--tags` and `--roots` are active by
default. You can use the negation switches to turn them off. These use
the uppercase equivalent of the short option and the prefix `no-` for
the long option. For example: `-B | --no-branches` to deactivate showing
branches.

Show all interesting commits, i.e. show also merges and bifurcations:

``` console
$ git-big-picture -i -m
```

Show only roots (deactivate branches and tags):

``` console
$ git-big-picture -B -T
```

Show merges and branches only (deactivate tags):

``` console
$ git-big-picture -m -T
```

Show all commits:

``` console
$ git-big-picture -a
```


## Configuration

The standard `git config` infrastructure can be used to configure
`git-big-picture`. Most of the command line arguments can be configured
in a `big-picture` section. For example, to configure `firefox` as a
viewer

``` console
$ git config --global big-picture.viewer firefox
```

Will create the following section and entry in your `~/.gitconfig`:

``` ini
[big-picture]
    viewer = firefox
```

The command line negation arguments can be used to disable a setting
configured via the command line. For example, if you have configured the
`viewer` above and try to use the `-g | --graphviz` switch, you will get
the following error:

``` console
$ git-big-picture -g
fatal: Options '-g | --graphviz' and '-p | --processed' are incompatible with other output options.
```

... since you already have a viewer configured. In this case, use the
negation option `-V | --no-viewer` to disable the `viewer` setting from
the config file:

``` console
$ git-big-picture -g -V
```


## Development

git-big-picture uses [pre-commit](https://pre-commit.com/), both locally
and in the CI. To activate the same local pre-commit Git hooks for
yourself, you could do:

``` console
$ pip install pre-commit
$ pre-commit install --install-hooks
```

When you do a commit after that, pre-commit will run the checks
configured in file `.pre-commit-config.yaml`.


## Testing

The Python code is tested with test runner [pytest](https://pytest.org):

``` console
$ ./test.py
```

The command line interface is tested with
[Cram](https://bitheap.org/cram/):

``` console
$ PATH="venv/bin:${PATH}" ./test.cram
```


## Debugging

You can use the `[-d | --debug]` switch to debug:

``` console
$ git-big-picture -d -v firefox
```

Although debugging output is somewhat sparse...


## Profiling

There are two ways to profile git-big-picture, using the built-in
`--pstats` option or using the Python module `cProfile`:

Using `--pstats`:

``` console
$ git-big-picture --pstats=profile-stats -o graph.svg
```

... will write the profiler output to `profile-stats`.

Profile the script with `cProfile`

``` console
$ python -m cProfile -o profile-stats git-big-picture -o graph.svg
```

In either case, you can then use the excellent visualisation tool
[gprof2dot](http://code.google.com/p/jrfonseca/wiki/Gprof2Dot) which,
incidentally, uses Graphviz too:

``` console
$ gprof2dot -f pstats profile-stats | dot -Tsvg -o profile_stats.svg
```


## Changelog

- `UNRELEASED` — YYYY-MM-DD
  - **New Features and Improvements**
    - Add support for Python 3.13 and 3.14
      ([#485](https://github.com/git-big-picture/git-big-picture/pull/485),
      [#601](https://github.com/git-big-picture/git-big-picture/pull/601),
      [#675](https://github.com/git-big-picture/git-big-picture/pull/675))
  - **Dropped Features**
    - Drop support for end-of-life Python 3.8 and 3.9
      ([#478](https://github.com/git-big-picture/git-big-picture/pull/478),
      [#483](https://github.com/git-big-picture/git-big-picture/pull/483),
      [#601](https://github.com/git-big-picture/git-big-picture/pull/601))
  - **Under the Hood**
    - Fix typos in the readme
      ([#401](https://github.com/git-big-picture/git-big-picture/pull/401))
    - Make GitHub Actions enforce codespell clean code
      ([#402](https://github.com/git-big-picture/git-big-picture/pull/402))
    - Drop GitHub Actions permissions to minimum for security
      ([#403](https://github.com/git-big-picture/git-big-picture/pull/403))
    - Migrate from YAPF to ruff format
      ([#484](https://github.com/git-big-picture/git-big-picture/pull/484))
    - Remove `tests_require=` from `setup.py` for Setuptools >=72.0.0
      ([#537](https://github.com/git-big-picture/git-big-picture/pull/537))
    - Migrate to `pyproject.toml`
      ([#602](https://github.com/git-big-picture/git-big-picture/pull/602))
    - Migrate the readme from reStructuredText to Markdown
      ([#673](https://github.com/git-big-picture/git-big-picture/pull/673),
      [#682](https://github.com/git-big-picture/git-big-picture/pull/XXXXXXXX))
    - Fix an ASCII Git graph in the readme
      ([#673](https://github.com/git-big-picture/git-big-picture/pull/673))
    - Document that the project is in maintenance mode
      ([#674](https://github.com/git-big-picture/git-big-picture/pull/674))
    - Explicitly specify initial branch name in tests
      ([#678](https://github.com/git-big-picture/git-big-picture/pull/678))
    - Document changes since release 1.3.0
      ([#683](https://github.com/git-big-picture/git-big-picture/pull/683))
- `v1.3.0` — 2024-03-08
  - **New Features and Improvements**
    - Make Graphviz output more deterministic
      ([#398](https://github.com/git-big-picture/git-big-picture/pull/398))
    - Add support for Python 3.11
      ([#296](https://github.com/git-big-picture/git-big-picture/pull/296))
    - Add support for Python 3.12
      ([#365](https://github.com/git-big-picture/git-big-picture/pull/365))
    - Fix link clickability for help output and man page
      ([#371](https://github.com/git-big-picture/git-big-picture/pull/371))
    - `README.rst`: Make screenshot dimensions match reality
      ([#399](https://github.com/git-big-picture/git-big-picture/pull/399))
  - **Dropped Features**
    - Drop support for end-of-life Python 3.7
      ([#335](https://github.com/git-big-picture/git-big-picture/pull/335))
- `v1.2.2` — 2022-09-27
  - **Under the Hood**
    - Fix cram tests for grep \>=3.8
      ([#233](https://github.com/git-big-picture/git-big-picture/pull/233))
- `v1.2.1` — 2022-03-26
  - **Bugs Fixed**
    - Fix output with argument `--processed`
      ([#197](https://github.com/git-big-picture/git-big-picture/issues/197),
      [#199](https://github.com/git-big-picture/git-big-picture/pull/199))
- `v1.2.0` — 2022-03-01
  - **New Features and Improvements**
    - Add argument `--simplify` to removed edges implied by transitivity
      based on Graphviz filter `tred`
      ([#180](https://github.com/git-big-picture/git-big-picture/issues/180),
      [#182](https://github.com/git-big-picture/git-big-picture/pull/182))
    - Switch default history direction from upwards to rightwards
      ([#184](https://github.com/git-big-picture/git-big-picture/pull/184))
    - Add support for Python 3.10
      ([#162](https://github.com/git-big-picture/git-big-picture/pull/162))
    - Use `python3` rather than `python` in Cram tests
      ([#89](https://github.com/git-big-picture/git-big-picture/pull/89))
  - **Dropped Features**
    - Drop support for end-of-life Python 3.6
      ([#162](https://github.com/git-big-picture/git-big-picture/pull/162))
- `v1.1.1` — 2021-01-20
  - **Bugs Fixed**
    - Fix version number in man page
      ([#86](https://github.com/git-big-picture/git-big-picture/pull/86))
  - **Under the Hood**
    - Move Git user setup into Cram tests (to make them work better
      outside of CI)
      ([#85](https://github.com/git-big-picture/git-big-picture/pull/85))
    - Extend changelog + release 1.1.1
      ([#87](https://github.com/git-big-picture/git-big-picture/pull/87))
- `v1.1.0` — 2021-01-20
  - **New Features and Improvements**
    - Add manpage from Debian package
      ([#79](https://github.com/git-big-picture/git-big-picture/pull/79))
    - Improve `--help` output
      ([#80](https://github.com/git-big-picture/git-big-picture/pull/80))
    - Document the meaning of term "bifurcation commit"
      ([#80](https://github.com/git-big-picture/git-big-picture/pull/80),
      [#84](https://github.com/git-big-picture/git-big-picture/issues/84))
  - **Under the Hood**
    - Remove TODOs from README
      ([#77](https://github.com/git-big-picture/git-big-picture/issues/77),
      [#78](https://github.com/git-big-picture/git-big-picture/pull/78))
    - Make CI prevent copies of `--help` output from going out-of-sync
      ([#80](https://github.com/git-big-picture/git-big-picture/pull/80))
    - Extend changelog + release 1.1.0
      ([#81](https://github.com/git-big-picture/git-big-picture/pull/81))
    - Migrate back to Cram
      ([#82](https://github.com/git-big-picture/git-big-picture/pull/82))
    - Extend .gitignore
      ([#83](https://github.com/git-big-picture/git-big-picture/pull/83))
- `v1.0.0` — 2021-01-13
  - **Security Fixes**
    - [CVE-2021-3028](https://cve.mitre.org/cgi-bin/cvename.cgi?name=2021-3028)
      — Fix local code execution through attacker controlled branch
      names
      ([#62](https://github.com/git-big-picture/git-big-picture/pull/62))
  - **New Features and Improvements**
    - Re-joined forces and moved
      <https://github.com/esc/git-big-picture> to new org home
      <https://github.com/git-big-picture/git-big-picture>
    - Support history directions other than upwards
      ([#35](https://github.com/git-big-picture/git-big-picture/pull/35),
      [#36](https://github.com/git-big-picture/git-big-picture/issues/36),
      [#59](https://github.com/git-big-picture/git-big-picture/pull/59))
    - Allow including commit messages in node labels
      ([#16](https://github.com/git-big-picture/git-big-picture/issues/16),
      [#31](https://github.com/git-big-picture/git-big-picture/pull/31),
      [#32](https://github.com/git-big-picture/git-big-picture/pull/32))
    - Support `python -m git_big_picture`
      ([#58](https://github.com/git-big-picture/git-big-picture/pull/58))
    - Improved `--help` output
      ([#54](https://github.com/git-big-picture/git-big-picture/pull/54))
    - Improve tempfile prefix
      ([#68](https://github.com/git-big-picture/git-big-picture/pull/68))
    - Add support for Python 3.8 and 3.9
      ([#42](https://github.com/git-big-picture/git-big-picture/pull/42))
  - **Dropped Features**
    - Drop support for end-of-life versions of Python (2.7, 3.4, 3.5)
      ([#38](https://github.com/git-big-picture/git-big-picture/pull/38))
  - **Bugs Fixed**
    - Handle `Ctrl+C` gracefully
      ([#70](https://github.com/git-big-picture/git-big-picture/pull/70))
    - Stop leaving temp files behind
      ([#25](https://github.com/git-big-picture/git-big-picture/pull/25),
      [#49](https://github.com/git-big-picture/git-big-picture/pull/49))
    - Be robust with regard to branch names that contain quotation marks
      ([#27](https://github.com/git-big-picture/git-big-picture/pull/27),
      [#62](https://github.com/git-big-picture/git-big-picture/pull/62))
    - `readme`: Fix a typo and word casing
      ([#43](https://github.com/git-big-picture/git-big-picture/pull/43))
    - Fix typo "piture"
      ([#51](https://github.com/git-big-picture/git-big-picture/pull/51))
  - **Under the Hood**
    - screenshots: Reduce image size using lossless
      [zopflipng](https://github.com/google/zopfli/blob/master/README.zopflipng)
      1.0.3
      ([#39](https://github.com/git-big-picture/git-big-picture/pull/39))
    - Apply move of Git repository to all URLs but Travis CI
      ([#40](https://github.com/git-big-picture/git-big-picture/pull/40))
    - Replace Travis CI by GitHub Actions
      ([#41](https://github.com/git-big-picture/git-big-picture/pull/41))
    - Make CI cover support for macOS
      ([#44](https://github.com/git-big-picture/git-big-picture/pull/44))
    - Make GitHub Dependabot keep our GitHub Actions up to date
      ([#45](https://github.com/git-big-picture/git-big-picture/pull/45),
      [#46](https://github.com/git-big-picture/git-big-picture/pull/46))
    - Integrate [pre-commit](https://pre-commit.com/) for dev and CI
      ([#47](https://github.com/git-big-picture/git-big-picture/pull/47),
      [#53](https://github.com/git-big-picture/git-big-picture/pull/53),
      [#55](https://github.com/git-big-picture/git-big-picture/pull/55))
    - For safety, stop using `shlex.split` (outside of tests)
      ([#48](https://github.com/git-big-picture/git-big-picture/pull/48),
      [#65](https://github.com/git-big-picture/git-big-picture/pull/65))
    - Migrate from unmaintained Cram to maintained Scruf
      ([#50](https://github.com/git-big-picture/git-big-picture/pull/50),
      [#64](https://github.com/git-big-picture/git-big-picture/pull/64))
    - Delete empty `requirements.txt`
      ([#52](https://github.com/git-big-picture/git-big-picture/pull/52))
    - Migrate from optparse to argparse
      ([#54](https://github.com/git-big-picture/git-big-picture/pull/54))
    - Fix variable mix-up
      ([#57](https://github.com/git-big-picture/git-big-picture/pull/57))
    - Start using standard setuptools entry point
      ([#58](https://github.com/git-big-picture/git-big-picture/pull/58))
    - Address dead test code
      ([#60](https://github.com/git-big-picture/git-big-picture/pull/60))
    - Start measuring code coverage
      ([#61](https://github.com/git-big-picture/git-big-picture/pull/61))
    - Replace nose by pytest for a test runner
      ([#63](https://github.com/git-big-picture/git-big-picture/issues/63),
      [#67](https://github.com/git-big-picture/git-big-picture/pull/67))
    - Start auto-formatting using [yapf](https://github.com/google/yapf)
      ([#66](https://github.com/git-big-picture/git-big-picture/issues/66))
    - `setup.py`: Replace ASCII "--" with "—" (em dash) in description
      ([#69](https://github.com/git-big-picture/git-big-picture/pull/69))
    - `Readme`: Improve section on people involved
      ([#71](https://github.com/git-big-picture/git-big-picture/pull/71))
    - tests: Cover option precedence on the command line
      ([#72](https://github.com/git-big-picture/git-big-picture/pull/72))
    - Pin and auto-update test requirements
      ([#73](https://github.com/git-big-picture/git-big-picture/pull/73),
      [#75](https://github.com/git-big-picture/git-big-picture/pull/75))
    - Document changes of release 1.0.0
      ([#74](https://github.com/git-big-picture/git-big-picture/pull/74))
    - Release version 1.0.0
      ([#76](https://github.com/git-big-picture/git-big-picture/issues/76))
- `v0.10.1` — 2018-11-04
  - Fix PyPI release
- `v0.10.0` — 2018-11-04
  - First release after 6 years
  - Support for Python: 2.7, 3.4, 3.5, 3.6, 3.7
    ([#13](https://github.com/git-big-picture/git-big-picture/pull/13),
    [#14](https://github.com/git-big-picture/git-big-picture/pull/14),
    [#24](https://github.com/git-big-picture/git-big-picture/pull/24))
  - Add Python classifiers to setup.py
  - Tempfile suffix now matches format
    ([#28](https://github.com/git-big-picture/git-big-picture/pull/28))
  - Continuous integration via travis.ci
    ([#29](https://github.com/git-big-picture/git-big-picture/pull/29))
  - Fixed installation instructions
    ([#26](https://github.com/git-big-picture/git-big-picture/pull/26))
- `v0.9.0` — 2012-11-20
  - rst-ify readme
  - Fix long standing bug in graph search algorithm
  - Fix long standing conversion from tabbed to 4-spaces
  - Overhaul and refactor the test-suite
  - Remove old `--some` crufty code and option
  - Add ability to find root-, merge- and bifurcation-commits
  - Overhaul command line interface with new options
  - Add command line interface tests using Cram
  - Overhaul documentation to reflect changes
- `v0.8.0` — 2012-11-05
  - Snapshot of all developments Mar 2010 - Now
  - Extended command line options for viewing and formatting
  - Option to filter on all, some or decorated commits
  - Simple test suite for python module and command line


## License

Licensed under GPL v3 or later, see file COPYING for details.


## Authors/Contributors

- Sebastian Pipping ([@hartwork](https://github.com/hartwork))
- Julius Plenz ([@Feh](https://github.com/Feh))
- Valentin Haenel ([@esc](https://github.com/esc))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))
- Chris West ([@FauxFaux](https://github.com/FauxFaux))
- Antonio Valentino ([@avalentino](https://github.com/avalentino))
- Rafał Zawadzki ([@bluszcz](https://github.com/bluszcz))
- Dan Wallis ([@fredden](https://github.com/fredden))
- Sergey Azarkevich ([@azarkevich](https://github.com/azarkevich))
- Johannes Koepcke ([@jkoepcke](https://github.com/jkoepcke))
- Rolf Offermanns ([@zapp42](https://github.com/zapp42))
- François Maheux ([@franckspike](https://github.com/franckspike))
- Doug Torrance ([@d-torrance](https://github.com/d-torrance))
