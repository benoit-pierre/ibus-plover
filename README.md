===========
IBus-Plover
===========

- Author: Benoit Pierre (benoit.pierre@gmail.com)
- Source: https://github.com/benoit-pierre/ibus-plover

Dependencies
============

* [IBus] (https://code.google.com/p/ibus/)
* [Plover] (http://plover.stenoknight.com/)

N.B.: for QT support, you'll need a [patched version of ibus-qt] (https://github.com/benoit-pierre/ibus-qt/commit/8ec39b148347e0e3841231e47c5507025b5580db) to correctly handle strokes.

Quick Start
===========

- install dependencies
- install ibus-plover globally (use the PKGBUILD in archlinux, or the Makefile install rule): this need to be done so the engine is registered to IBus (plover.xml must be copied in /usr/share/ibus/component)
- restart IBus: Plover should now be available in the English input methods list
- add Plover to the list of input methods: you will now be able to select it using the global shortcut or the systray menu
 
N.B.: the dictionaries from Plover configuration will be used.

Limitations
===========

Due to the way IBus works:

- preedit text visualization can be buggy in some applications (like partially obscured because the application does not scroll automatically)
- committing text with a return does not work in all cases (work in Google Doc, but not when composing in GMail...)
- no state is saved when switching context (like applications): preedit text is lost
- also no way (that I found) to be able to detect which application an input context is used for (to tailor some settings based on application)

Debugging
=========

If you run "python2 ./main.py" from the source directory, this will replace the engine with a debug version: you'll get some traces on stdout.

N.B.: ibus-plover must still be installed for this too work (so it's registered).
