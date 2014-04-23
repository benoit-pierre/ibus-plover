# vim: set fileencoding=utf-8 :
#
# ibus-plover - Plover support for Input Bus
#
# Copyright (c) 2013-2014 Benoit Pierre <benoit.pierre@gmail.com>
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
from gi.repository import GLib
from gi.repository import GObject

import os
import sys
import getopt
import locale
import logging

from engine import EnginePlover

class IMApp:
    def __init__(self, exec_by_ibus):
        engine_name = "plover" if exec_by_ibus else "plover (debug)"
        self.__component = \
                IBus.Component.new("org.freedesktop.IBus.Plover",
                                   "Plover Component",
                                   "0.1.0",
                                   "GPL",
                                   "Benoit Pierre <benoit.pierre@gmail.com>",
                                   "http://example.com",
                                   "/usr/bin/exec",
                                   "ibus-plover")
        engine = IBus.EngineDesc.new("plover",
                                     engine_name,
                                     "English Plover",
                                     "en",
                                     "GPL",
                                     "Benoit Pierre <benoit.pierre@gmail.com>",
                                     "",
                                     "us")
        self.__component.add_engine(engine)
        self.__mainloop = GLib.MainLoop()
        self.__bus = IBus.Bus()
        self.__bus.connect("disconnected", self.__bus_disconnected_cb)
        self.__factory = IBus.Factory.new(self.__bus.get_connection())
        self.__factory.add_engine("plover",
                GObject.type_from_name("EnginePlover"))
        if exec_by_ibus:
            self.__bus.request_name("org.freedesktop.IBus.Plover", 0)
        else:
            self.__bus.register_component(self.__component)

    def run(self):
        self.__mainloop.run()

    def __bus_disconnected_cb(self, bus):
        self.__mainloop.quit()


def launch_engine(exec_by_ibus):
    IBus.init()
    IMApp(exec_by_ibus).run()

def print_help(out, v = 0):
    print >> out, "-i, --ibus             executed by IBus."
    print >> out, "-h, --help             show this message."
    print >> out, "-d, --daemonize        daemonize ibus"
    sys.exit(v)

def main():
    try:
        locale.setlocale(locale.LC_ALL, "")
    except:
        pass

    exec_by_ibus = False
    daemonize = False

    shortopt = "ihd"
    longopt = ["ibus", "help", "daemonize"]

    try:
        opts, args = getopt.getopt(sys.argv[1:], shortopt, longopt)
    except getopt.GetoptError, err:
        print_help(sys.stderr, 1)

    for o, a in opts:
        if o in ("-h", "--help"):
            print_help(sys.stdout)
        elif o in ("-d", "--daemonize"):
            daemonize = True
        elif o in ("-i", "--ibus"):
            exec_by_ibus = True
        else:
            print >> sys.stderr, "Unknown argument: %s" % o
            print_help(sys.stderr, 1)

    if daemonize:
        if os.fork():
            sys.exit()

    if not exec_by_ibus and not daemonize:
        logging.basicConfig()
        logging.getLogger('ibus.plover').setLevel(logging.DEBUG)
    else:
        logging.basicConfig(filename='/tmp/ibus-plover.log', level=logging.DEBUG)

    launch_engine(exec_by_ibus)

if __name__ == "__main__":
    main()
