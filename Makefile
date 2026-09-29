# Automation layer (install, run, debug, clean, lint) [cite: 363]

# Makefile for Fly-in (Drone Routing System)

PYTHON := python3
MAIN := src/main.py

.PHONY: install run debug clean lint lint-strict help

# Default target
all: run

# Install dependencies
install:
	pip install -r requirements.txt

# Execute the main simulation (Example usage: make run MAP=maps/easy1.txt)
run:
	@if [ -z "$(MAP)" ]; then \
		$(PYTHON) $(MAIN) test_map.txt; \
	else \
		$(PYTHON) $(MAIN) $(MAP); \
	fi

viz:
	$(PYTHON) $(MAIN) $(MAP) --visual;

gui:
	$(PYTHON) $(MAIN) $(MAP) --gui;


# Run main script under pdb (Python Debugger)
debug:
	$(PYTHON) -m pdb $(MAIN) $(if $(MAP),$(MAP),test_map.txt)

# Remove Python caches and temporary files
clean:
	rm -rf __pycache__ src/__pycache__
	rm -rf .mypy_cache .pytest_cache
	find . -type f -name "*.pyc" -delete

# Mandatory linting checks according to subject specifications
lint:
	flake8 .
	mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs .

# Optional strict linting checks
lint-strict:
	flake8 .
	mypy --strict .

# Display help menu
help:
	@echo "Available rules:"
	@echo "  make install     - Install project dependencies"
	@echo "  make run [MAP=]  - Run simulation (default: test_map.txt)"
	@echo "  make debug [MAP=]- Run simulation in debug mode (pdb)"
	@echo "  make lint        - Run standard flake8 and mypy checks"
	@echo "  make lint-strict - Run flake8 and mypy in strict mode"
	@echo "  make clean       - Remove caches and temporary files"