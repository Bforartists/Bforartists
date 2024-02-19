# SPDX-FileCopyrightText: 2011-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# note: this isn't needed for building,
# its just for some convenience targets.

PY_FILES=$(shell find ./ -type f -name '*.py')
# Filter out files which use `bpy`.
PY_FILES_MYPY=$(filter-out \
	./__init__.py \
	./bl_extension_monkeypatch.py \
	./bl_extension_ops.py \
	./bl_extension_ui.py \
	./bl_extension_utils.py \
	./example_extension/__init__.py \
	./example_extension/foo.py \
	,$(PY_FILES))

PY_FILES_MYPY_STANDALONE= \
	./bl_extension_utils.py \

EXTRA_WATCH_FILES=Makefile

# For tests that launch Blender directly.
BLENDER_BIN?=$(shell which blender)
PYTHON_BIN?=$(shell which python3)

pep8: FORCE
	flake8 $(PY_FILES) --ignore=E501,E302,E123,E126,E128,E129,E124,E122,W504

# `--no-namespace-packages` is needed otherwise `./cli/blender_ext.py` loads in parent modules
# (the Blender add-on which imports `bpy`).
check_mypy: FORCE
	mypy --no-namespace-packages --strict $(PY_FILES_MYPY)
	mypy --strict --follow-imports=skip $(PY_FILES_MYPY_STANDALONE)

check_ruff: FORCE
	ruff check $(PY_FILES_MYPY)
	ruff check $(PY_FILES_MYPY_STANDALONE)

check_pylint:
	pylint $(PY_FILES) \
	--disable=C0111,C0301,C0302,C0103,C0415,R1705,R0902,R0903,R0913,E0611,E0401,I1101,R0801,C0209,W0511,W0718,W0719,C0413,R0911,R0912,R0914,R0915

# python3 ./tests/test_cli.py
test: FORCE
	env USE_HTTP=0 $(PYTHON_BIN) ./tests/test_cli.py
	env USE_HTTP=1 $(PYTHON_BIN) ./tests/test_cli.py

# NOTE: these rely on the blender binary.
test_blender: FORCE
	env ASAN_OPTIONS=check_initialization_order=0:leak_check_at_exit=0 \
	    $(BLENDER_BIN) --background --factory-startup -noaudio --python tests/test_blender.py -- --verbose

watch_test_blender: FORCE
	while true; do \
		$(MAKE) test_blender; \
		inotifywait -q -e close_write $(EXTRA_WATCH_FILES) $(PY_FILES) ; \
		tput clear; \
	done

# https://www.cyberciti.biz/faq/howto-create-linux-ram-disk-filesystem/
# mkfs -q /dev/ram1 8192
# mkdir -p /ramcache
# sudo mount /dev/ram1 /ramcache
# sudo chmod 777 /ramcache
# mkdir /ramcache/tmp

watch_test: FORCE
	while true; do \
		$(MAKE) test; \
		inotifywait -q -e close_write $(EXTRA_WATCH_FILES) $(PY_FILES) ; \
		tput clear; \
	done

watch_check_mypy:
	while true; do \
		$(MAKE) check_mypy; \
		inotifywait -q -e close_write $(EXTRA_WATCH_FILES) \
		            $(PY_FILES_MYPY) \
		            ./bl_extension_utils.py ; \
		tput clear; \
	done

watch_check_ruff:
	while true; do \
		$(MAKE) check_ruff; \
		inotifywait -q -e close_write $(EXTRA_WATCH_FILES) \
		            $(PY_FILES_MYPY) \
		            ./bl_extension_utils.py ; \
		tput clear; \
	done

watch_check_pylint:
	while true; do \
		$(MAKE) check_pylint; \
		inotifywait -q -e close_write $(EXTRA_WATCH_FILES) $(PY_FILES) ; \
		tput clear; \
	done


FORCE:
