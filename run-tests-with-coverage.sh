#! /usr/bin/env bash
# This file is part of git-big-picture
#
# Copyright (C) 2020 Sebastian Pipping <sebastian@pipping.org>
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

set -e

# Constants
venv=.coverage-venv
source_dir="${PWD}"


# Create a tempdir, jump into it, wipe its content on exit
temp_dir="$(mktemp -d)"
wipe_tempdir() {
    rm -R "${temp_dir}"
}
trap wipe_tempdir EXIT
cd "${temp_dir}"


# NOTE: Collecting code coverage across subprocesses is a bit tricky in general,
#       see https://coverage.readthedocs.io/en/coverage-5.1/api_coverage.html for background.
#
#       On top of that we are dealing with subprocesses here that have a different working directory
#       than their parents and hence interpret relative paths in .coveragerc differently.
#
#       To deal with this problem, we (1) run the tests outside of the source directory and
#       (2) use a dedicated virtualenv so that:
#
#        - We can tinker with file sitecustomize.py without worry of affecting any existing
#          environments.
#
#        - We can create an copy of .coveragerc with absolute path on the fly so that all processes
#          work with the same set of absolute paths, no matter their initial working directory,
#          while still not hardcoding a specific temp directory.

# Prepare a virtualenv ready to run tests with subprocess coverage
# Also check for (and enforce) conflict-free and all-pinned dependencies
python3 -m venv ${venv}
source ${venv}/bin/activate
pip install --quiet --disable-pip-version-check -r "${source_dir}"/test_requirements.txt
pip install --quiet --disable-pip-version-check -e "${source_dir}"
pip check > /dev/null
diff -U0 \
    <(sed -e '/#.*/d' -e '/^$/d' "${source_dir}"/test_requirements.txt | sort -f) \
    <(pip freeze | fgrep -v git_big_picture | sort -f)
sed "s,\./,${source_dir}/,g" "${source_dir}"/.coveragerc > .coveragerc
cat <<SITECUSTOMIZE_PY_EOF > "$(ls -1d ${venv}/lib/python*)"/site-packages/sitecustomize.py
try:
    import coverage
    coverage.process_startup()
except ImportError:
    pass
SITECUSTOMIZE_PY_EOF


# Actually run the tests
exit_code=0
coverage erase

coverage run ${venv}/bin/pytest "${source_dir}"/test.py \
    || exit_code=$?
PATH="${venv}/bin:${PATH}" COVERAGE_PROCESS_START=.coveragerc \
    coverage run ${venv}/bin/scruf "${source_dir}"/test.scf \
    || exit_code=$?

coverage combine
coverage html -d "${source_dir}"/htmlcov/
coverage report
exit ${exit_code}
