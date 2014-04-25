
.PHONY: install

all:

PREFIX ?= /usr
DESTDIR ?=

COMPONENT_DIR = $(DESTDIR)$(PREFIX)/share/ibus/component
ENGINE_DIR = $(DESTDIR)$(PREFIX)/share/ibus-plover

install:
	mkdir -p -m 755 $(COMPONENT_DIR)
	install -m644 -t $(COMPONENT_DIR) plover.xml
	sed -i 's,/usr/share/ibus-plover/,$(PREFIX)/share/ibus-plover/,' $(COMPONENT_DIR)/plover.xml
	mkdir -p -m 755 $(ENGINE_DIR)
	install -m644 -t $(ENGINE_DIR) engine.py ibus-plover.png main.py
	install -m755 -t $(ENGINE_DIR) ibus-engine-plover
