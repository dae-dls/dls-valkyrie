
# ------------------------------------------------------------------
# Tests.

test-01-writer_reader:
	python3 -m pytest -sv -rfp --tb=line tests/01-writer_reader/test_01.py

test-01-writer_reader-pushpull:
	python3 -m pytest -sv tests/01-writer_reader/test_01.py::Test::test_01_pushpull

test-02-missed_unthreaded:
	python3 -m pytest -sv tests/02-missed_unthreaded/test_02.py

test-03-missed_threaded:
	python3 -m pytest -sv tests/03-missed_threaded/test_03.py

test-04-dataless:
	python3 -m pytest -sv tests/04-dataless/test_04.py

test-05-speed:
	python3 -m pytest -sv tests/05-speed/test_05.py

test-06-pullpush:
	python3 -m pytest -sv tests/06-pullpush/test_06.py

test-07-websockets:
	python3 -m pytest -sv tests/07-websockets/test_07.py

# ------------------------------------------------------------------
# GitLab CI.

gitlab_ci_test:
	python3 -m pytest -sv -rfp --capture=no --cov=dls_valkyrie_lib \
		tests/01-writer_reader/test_01.py \
		tests/02-missed_unthreaded/test_02.py \
		tests/03-missed_threaded/test_03.py \
		tests/04-dataless/test_04.py \
		tests/05-speed/test_05.py \
		tests/06-pullpush/test_06.py

test-ci:
	make -s gitlab_ci_test

gitrun-unittest:
	gitlab-runner exec docker unittest 2>&1 | tee gitrun-unittest.log

# ------------------------------------------------------------------
# Utility.

.PHONY: list
list:
	@awk "/^[^\t:]+[:]/" Makefile | grep -v ".PHONY"

show-version:
	PYTHONPATH=$(PYTHONPATH) python3 dls_valkyrie_lib/version.py --json
	PYTHONPATH=$(PYTHONPATH) python3 dls_valkyrie_lib/version.py

# ------------------------------------------------------------------
# Version bumping.  Configured in setup.cfg. 
# Thanks: https://pypi.org/project/bump2version/
bump-patch:
	bump2version --list patch

bump-minor:
	bump2version --list minor

bump-major:
	bump2version --list major
	
bump-dryrun:
	bump2version --dry-run patch
	