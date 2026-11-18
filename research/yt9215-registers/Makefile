# Checks and builds for the YT921x register description, bindings and manual.
#
#   make generate   rewrite the generated files from yt921x.yaml
#   make check      everything below except docs
#   make docs       build the manual (the Sphinx project is the repository root)

PYTHON ?= python3
CC ?= gcc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -pedantic
ROOT := $(abspath ../..)
BUILD ?= $(ROOT)/_build

.PHONY: generate check check-generated check-c check-rust check-python docs clean

generate:
	$(PYTHON) tools/generate.py

check: check-generated check-c check-rust check-python

check-generated:
	$(PYTHON) tools/generate.py --check
	$(PYTHON) -m unittest tests/test_generated.py

check-c:
	mkdir -p $(BUILD)/c
	$(CC) $(CFLAGS) -Ibindings/c bindings/c/yt921x.c bindings/c/tests/test_yt921x.c \
		-o $(BUILD)/c/test_yt921x
	$(BUILD)/c/test_yt921x
	$(CC) $(CFLAGS) -Ibindings/c -Ibindings/c/examples -Ibindings/c/tests bindings/c/yt921x.c \
		bindings/c/examples/guide.c bindings/c/tests/test_guide.c -o $(BUILD)/c/test_guide
	$(BUILD)/c/test_guide

check-rust:
	cd bindings/rust && cargo test && cargo build --examples && \
		cargo build --lib --target thumbv7em-none-eabihf

check-python:
	$(PYTHON) -m unittest discover -s bindings/micropython/tests
	if command -v mpy-cross >/dev/null; then \
		for f in yt921x_regs.py yt921x.py examples/guide.py; do \
			mpy-cross -o /dev/null bindings/micropython/$$f || exit 1; \
		done; \
	fi

docs:
	$(PYTHON) -m sphinx -b html -W --keep-going -n $(ROOT) $(BUILD)/html

clean:
	rm -rf $(BUILD) docs/reference bindings/rust/target
