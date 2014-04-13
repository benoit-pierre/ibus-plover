# vim:set et sts=4 sw=4 fileencoding=utf-8 :
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


from gi.repository import IBus

from plover.translation import _State, Translation, Translator
from plover.steno import Stroke
from plover.formatting import _Action, Formatter
from plover.dictionary.loading_manager import manager as DictionaryManager
import plover.config

import logging

KEYSTRING_TO_STENO_KEY_ALT = {
    59: "S-",
    60: "T-",
    61: "P-",
    62: "H-",
    63: "*",
    65: "*",
    66: "-F",
    67: "-P",
    68: "-L",
    87: "-T",
    88: "-D",
    2: "S-",
    3: "K-",
    4: "W-",
    5: "R-",
    6: "*",
    8: "*",
    9: "-R",
    10: "-B",
    11: "-G",
    12: "-S",
    13: "-Z",
    18: "A-",
    19: "O-",
    22: "-E",
    23: "-U",
}

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

NB_PREDIT_STROKES = 10


class Log:

    def __init__(self, engine):
        self._log = logging.getLogger('ibus.plover')
        self._id = id(engine)

    def debug(self, s):
        self._log.debug('%x:%s' % (self._id, s))


class Steno:

    def __init__(self, output, log):

        self._log = log
        self._output = output
        self._config = plover.config.Config()
        with open(plover.config.CONFIG_FILE) as f:
            self._config.load(f)
        self._dicts = DictionaryManager.load(self._config.get_dictionary_file_names())
        self._formatter = Formatter()
        self._formatter.set_output(self._output)
        self._translator = Translator()
        self._translator.add_listener(self._formatter.format)
        self._translator.get_dictionary().set_dicts(self._dicts)
        self._translator.set_min_undo_length(NB_PREDIT_STROKES)
        self.reset(full=True)

    def flush(self):
        self._output.flush()
        self.reset()

    def stroke(self, stroke):
        self._log.debug('stroke(%s)' % stroke.rtfcre)
        self._output.stroke_start()
        self._translator.translate(stroke)
        self._output.stroke_end()

    def reset(self, full=False):
        self._log.debug('reset steno state (full=%s)' % full)
        state = _State()
        state.tail = self._translator.get_state().last()
        if full or state.tail is None:
            state.tail = Translation([Stroke('*')], None)
            state.tail.formatting = [_Action(attach=True)]
        self._translator.set_state(state)
        self._output.reset()


class Output:

    def __init__(self, engine, log):
        self._log = log
        self._engine = engine
        self._text_preedit = []
        self._text_commit = None
        self._immediate_mode = False

    def _has_preedit(self):
        return 0 != len(self._text_preedit)

    def _hide_preedit(self):
        self._engine.text_preedit(None)

    def _show_preedit(self):
        text = u''.join(self._text_preedit)
        text = text.replace('\n', u'␍')
        if ' ' == text[-1]:
            text = text[:-1] + u'␠'
        self._log.debug('updating preedit text: %s' % text)
        self._engine.text_preedit(text)

    def _commit_preedit(self):
        text = ''.join(self._text_preedit)
        self._text_preedit = []
        self._engine.text_commit(text)

    def flush(self):
        if self._has_preedit():
            self._commit_preedit()
        self._hide_preedit()

    def stroke_start(self):
        self._text_commit = None

    def stroke_end(self):
        if self._text_commit is not None:
            self._engine.text_commit(self._text_commit)
        if self._has_preedit():
            self._show_preedit()
        else:
            self._hide_preedit()

    def set_immediate_mode(self, enable=True):
        if self._immediate_mode == enable:
            return
        self._immediate_mode = enable
        if self._immediate_mode:
            self.flush()

    def send_key(self, keyval, keycode):
        self._engine.forward_key_event(keyval, keycode, 0x0000)

    def send_backspaces(self, num):
        self._log.debug('send_backspaces(%u)' % num)
        if self._immediate_mode:
            self._engine.text_delete(num)
            return
        while num > 0 and len(self._text_preedit) > 0:
            text = self._text_preedit.pop()
            text_len = len(text)
            if text_len > num:
                text = text[:-num]
                self._text_preedit.append(text)
            num -= text_len

    def send_string(self, t):
        self._log.debug('send_string(%s)' % t)
        if self._immediate_mode:
            self._engine.text_commit(t)
            return
        self._text_preedit.append(t)
        if len(self._text_preedit) > NB_PREDIT_STROKES:
            self._text_commit = self._text_preedit.pop(0)

    def send_key_combination(self, c):
        self._log.debug('send_key_combination(%sc)' % c)
        key = KEYCOMBO_TO_KEYSTRING.get(c, None)
        if type(key) is str:
            self.send_string(key)
        elif key is not None:
            self.send_key(*key)

    def send_engine_command(self, c):
        self._log.debug('send_engine_command(%sc)' % c)

    def reset(self):
        self._log.debug('reset output')
        self._text_preedit = []
        self._text_commit = None
        self._hide_preedit()


class EnginePlover(IBus.Engine):
    __gtype_name__ = 'EnginePlover'

    def __init__(self):
        super(EnginePlover, self).__init__()
        self._log = Log(self)
        self._log.debug('__init__')
        self._pressed = set()
        self._keys = set()
        self._output = Output(self, self._log)
        self._steno = Steno(self._output, self._log)
        self._muted = False
        self._left_shift_pressed = False
        self._right_shift_pressed = False
        self._both_shift_pressed = False
        self._support_surrounding_text = False
        self._immediate_mode = False
        self._preedit = None
        self._use_alt_mapping = False
        self._show_strokes = False

    def do_process_key_event(self, keyval, keycode, state):
        self._log.debug("process_key_event(0x%04x, %u, %04x)" % (keyval, keycode, state))
        handled = self._process_key_event(keyval, keycode, state)
        if handled:
            self._log.debug('handled')
        else:
            self._log.debug('forwarded')
        return handled

    def text_commit(self, text):
        self.text_preedit(None)
        text = IBus.Text.new_from_string(text)
        self.commit_text(text)

    def text_preedit(self, text):
        self._preedit = text
        if self._preedit is None:
            self.hide_preedit_text()
        else:
            text = IBus.Text.new_from_string(text)
            self.update_preedit_text(text, 0, True)

    def text_delete(self, num):
        self.delete_surrounding_text(-num, num)

    def _has_preedit(self):
        return self._preedit is not None

    def _show_stroke(self):
        stroke = Stroke(list(self._keys))
        text = stroke.rtfcre
        if self._has_preedit():
            text = self._preedit + ' ' + text
        text = IBus.Text.new_from_string(text)
        self.update_preedit_text(text, 0, True)

    def _mute(self):
        self._log.debug('muting')
        self._steno.flush()
        self._muted = True

    def _unmute(self):
        self._log.debug('unmuting')
        self._muted = False

    def _toggle_mute(self):
        if self._muted:
            self._unmute()
        else:
            self._mute()

    def _set_immediate_mode(self, enable=True):
        if self._immediate_mode == enable:
            return
        self._log.debug('immediate mode %s' % enable)
        self._immediate_mode = enable
        self._output.set_immediate_mode(self._immediate_mode)
        self._steno.reset()

    def _stroke_started(self):
        """ Return True if a stroke is in progress. """
        return 0 != len(self._pressed)

    def _process_key_event(self, keyval, keycode, state):

        is_press = 0 == (state & IBus.ModifierType.RELEASE_MASK)

        # Handle special key combo to enable/disable/toggle.
        if IBus.ModifierType.HYPER_MASK == state:
            if IBus.d == keyval:
                self._mute()
            elif IBus.e == keyval:
                self._unmute()
            elif IBus.t == keyval:
                self._toggle_mute()
            return True

        # Handle both shift keys pressed combo to toggle mute.
        both_shift_pressed = self._both_shift_pressed
        if IBus.Shift_L == keyval:
            self._left_shift_pressed = is_press
        if IBus.Shift_R == keyval:
            self._right_shift_pressed = is_press
        self._both_shift_pressed = self._left_shift_pressed and self._right_shift_pressed
        if both_shift_pressed and not self._both_shift_pressed:
            self._toggle_mute()

        # Disabled?
        if self._muted:
            return False

        if not self._stroke_started():

            # Let the application handle keys with modifiers (other than shifted).
            if 0 != (state & ~(IBus.ModifierType.RELEASE_MASK |
                               IBus.ModifierType.SHIFT_MASK |
                               IBus.ModifierType.LOCK_MASK)):

                # Ctrl+Tab immediate mode (if supported).
                if self._support_surrounding_text and IBus.Tab == keyval and \
                   0 != (IBus.ModifierType.CONTROL_MASK & state):
                    if not is_press:
                        self._set_immediate_mode(not self._immediate_mode)
                    return True

                return False

            if not self._immediate_mode:

                # Space will commit preedit if any, or else be forwarded.
                if IBus.space == keyval:
                    if self._has_preedit():
                        self._steno.flush()
                        return True
                    return False

                # BackSpace is forwarded if no preedit.
                if IBus.BackSpace == keyval:
                    if self._has_preedit():
                        # TODO: convert to the right stroke?
                        return True
                    return False

                # Escape/Return/Tab trigger a commit before being forwarded.
                if keyval in (IBus.Escape, IBus.Return, IBus.Tab):
                    self._steno.flush()
                    return False

        if self._use_alt_mapping:
            mapping = KEYSTRING_TO_STENO_KEY_ALT
        else:
            mapping = KEYSTRING_TO_STENO_KEY
        steno_key = mapping.get(keycode, None)
        if steno_key is None:
            if self._stroke_started() or self._has_preedit():
                return True
            if keycode in xrange(16, 28) or \
               keycode in xrange(30, 41) or \
               keycode in xrange(44, 54):
                return True
            return False

        if is_press:
            self._keys.add(steno_key)
            self._pressed.add(steno_key)
            if self._show_strokes:
                self._show_stroke()
        else:
            if steno_key in self._pressed:
                self._pressed.remove(steno_key)
                if 0 == len(self._pressed):
                    stroke = Stroke(list(self._keys))
                    self._steno.stroke(stroke)
                    self._keys.clear()

        return True

    def do_focus_in(self):
        self._log.debug("focus_in")

    def do_focus_out(self):
        self._log.debug("focus_out")

    def do_reset(self):
        self._log.debug("reset")
        self._steno.reset(full=True)

    def do_set_capabilities(self, caps):
        self._log.debug("set_capabilities(%x)" % caps)
        self._support_surrounding_text = caps & IBus.Capabilite.SURROUNDING_TEXT

