# vim:set et sts=4 sw=4:
#
# ibus-plover - Plover support for Input Bus
#
# Copyright (c) 2013 Benoit Pierre <benoit.pierre@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from gi.repository import GLib
from gi.repository import IBus
from gi.repository import Pango

keysyms = IBus

from plover.translation import Translator
from plover.steno import Stroke
from plover.formatting import Formatter
from plover.dictionary.loading_manager import manager as DictionaryManager
import plover.config

import termios
import time
import tty
import sys

KEYSTRING_TO_STENO_KEY = {
    16: "S-",
    17: "T-",
    18: "P-",
    19: "H-",
    20: "*",
    21: "*",
    22: "-F",
    23: "-P",
    24: "-L",
    25: "-T",
    26: "-D",
    30: "S-",
    31: "K-",
    32: "W-",
    33: "R-",
    34: "*",
    35: "*",
    36: "-R",
    37: "-B",
    38: "-G",
    39: "-S",
    40: "-Z",
    46: "A-",
    47: "O-",
    49: "-E",
    50: "-U",
}

KEYCOMBO_TO_KEYSTRING = {
    'Return': '\n',
}

USE_DELETE_SURROUNDING_TEXT = True

NB_PREDIT_STROKES = 5

class Steno:

    def __init__(self):

        self.config = plover.config.Config()
        with open(plover.config.CONFIG_FILE) as f:
            self.config.load(f)
        self.dicts = DictionaryManager.load(self.config.get_dictionary_file_names())
        self.formatter = Formatter()
        self.formatter.set_output(self)
        self.translator = Translator()
        self.translator.add_listener(self.formatter.format)
        self.translator.get_dictionary().set_dicts(self.dicts)
        self.translator.set_min_undo_length(NB_PREDIT_STROKES)
        self.text_commit = None
        self.text_preedit = []

    def send_key(self, keyval, keycode):
        self.forward_key_event(keyval, keycode, 0x0000)

    def send_backspaces(self, b):
        print 'send_backspaces(%u)' % b
        while b > 0 and len(self.text_preedit) > 0:
            t = self.text_preedit.pop()
            l = len(t)
            if l > b:
                t = t[:-b]
                self.text_preedit.append(t)
            b -= l
        self.text_commit = None

    def send_string(self, t):
        print 'send_string(%s)' % t
        self.text_preedit.append(t)
        if len(self.text_preedit) > NB_PREDIT_STROKES:
            self.text_commit = self.text_preedit.pop(0)
        else:
            self.text_commit = None


    def send_key_combination(self, c):
        print 'send_key_combination(%sc)' % c
        key = KEYCOMBO_TO_KEYSTRING.get(c, None)
        if type(key) is str:
            self.send_string(key)
        elif key is not None:
            self.send_key(*key)

    def send_engine_command(self, c):
        print 'send_engine_command(%sc)' % c

    def stroke(self, keys):
        print 'stroke(%s)' % keys
        self.translator.translate(Stroke(keys))

    def reset(self):
        self.translator.clear_state()
        self.text_commit = None
        self.text_preedit = []

class EnginePlover(IBus.Engine):
    __gtype_name__ = 'EnginePlover'

    def __init__(self):
        super(EnginePlover, self).__init__()
        self.__is_invalidate = False
        self.__preedit_string = u""
        self.__lookup_table = IBus.LookupTable.new(10, 0, True, True)
        self.__prop_list = IBus.PropList()
        self.__prop_list.append(IBus.Property(key="test", icon="ibus-local"))
        self._pressed = set()
        self._keys = set()
        self._steno = Steno()
        self._mutted = False
        self._left_shift_pressed = False
        self._right_shift_pressed = False
        self._both_shift_pressed = False

    def do_process_key_event(self, keyval, keycode, state):
        print "process_key_event(0x%04x, %u, %04x)" % (keyval, keycode, state)
        if IBus.ModifierType.MOD5_MASK == state:
            if keysyms.d == keyval:
                print 'mutting'
                self._mutted = True
            elif keysyms.e == keyval:
                print 'unmutting'
                self._mutted = False
            elif keysyms.t == keyval:
                self._mutted = not self._mutted
                print 'mutted:', self._mutted
            return True
        both_shift_pressed = self._both_shift_pressed
        if 42 == keycode:
            self._left_shift_pressed = 0 == (state & IBus.ModifierType.RELEASE_MASK)
        if 54 == keycode:
            self._right_shift_pressed = 0 == (state & IBus.ModifierType.RELEASE_MASK)
        self._both_shift_pressed = self._left_shift_pressed and self._right_shift_pressed
        if both_shift_pressed and not self._both_shift_pressed:
            self._mutted = not self._mutted
        if self._mutted:
            return False
        if keysyms.Escape == keyval:
            if 0 == len(self._steno.text_preedit):
                return False
            self._steno.reset()
            self.hide_preedit_text()
            return True
        if keysyms.Return == keyval:
            if 0 == len(self._steno.text_preedit):
                # Nothing to commit...
                return False
            text = ''.join(self._steno.text_preedit)
            self._steno.reset()
            self.commit_text(IBus.Text.new_from_string(text))
            self.hide_preedit_text()
            return True
        if 0 != (state & ~(IBus.ModifierType.RELEASE_MASK |
                           IBus.ModifierType.SHIFT_MASK |
                           IBus.ModifierType.LOCK_MASK)):
            return False
        steno_key = KEYSTRING_TO_STENO_KEY.get(keycode, None)
        if steno_key is None:
            if keycode in xrange(16, 28) or \
               keycode in xrange(30, 41) or \
               keycode in xrange(44, 54):
                return True
            return False
        is_press = 0 == (state & IBus.ModifierType.RELEASE_MASK)
        if is_press:
            self._keys.add(steno_key)
            self._pressed.add(steno_key)
        else:
            if steno_key in self._pressed:
                self._pressed.remove(steno_key)
                if 0 == len(self._pressed):
                    self._steno.stroke(list(self._keys))
                    self._keys.clear()
                    if self._steno.text_commit is not None:
                        text = self._steno.text_commit
                        self.commit_text(IBus.Text.new_from_string(text))
                    if len(self._steno.text_preedit) > 0:
                        text = ''.join(self._steno.text_preedit)
                        self.update_preedit_text(IBus.Text.new_from_string(text), 0, True)
                    else:
                        self.hide_preedit_text()
            return True
        return True

    def do_focus_in(self):
        print "focus_in"
        self.register_properties(self.__prop_list)

    def do_focus_out(self):
        print "focus_out"

    def do_reset(self):
        print "reset"
        self._steno.reset()

