
.PHONY: install

all:

PREFIX ?= /usr
DESTDIR ?=

COMPONENT_DIR = $(DESTDIR)$(PREFIX)/share/ibus/component
ENGINE_DIR = $(DESTDIR)$(PREFIX)/share/ibus-plover

install:
	mkdir -p -m 755 $(ENGINE_DIR)
	install -m755 -t $(ENGINE_DIR) ibus-engine-plover
	install -m644 -t $(ENGINE_DIR) config.py engine.py ibus-plover.png main.py plover.xml
	sed -i 's,/usr/share/ibus-plover/,$(PREFIX)/share/ibus-plover/,' $(ENGINE_DIR)/plover.xml
	mkdir -p -m 755 $(COMPONENT_DIR)
	ln -s $(shell python2 -c 'import os.path, sys; print os.path.relpath(*sys.argv[-2:])' $(ENGINE_DIR) $(COMPONENT_DIR))/plover.xml $(COMPONENT_DIR)/
