# Minimal Makefile for the genesisng project
#

BUILDDIR    = build
CACHEDIR    = __pycache__
DISTDIR     = dist
SPHINXDIR   = docs
SPHINXBUILD = _build

.PHONY: help clean wheel

default: wheel

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  wheel       to make a wheel package (PEP)"
	@echo "  clean       to clean up build files"

clean:
	rm -rf $(BUILDDIR)
	rm -rf $(DISTDIR)
	rm -rf $(SPHINXDIR)/$(SPHINXBUILD)
	find $(CURDIR) -type d -name $(CACHEDIR) -exec rm -rf {} +

wheel:
	python3 -m pep517.build --binary $(CURDIR)
