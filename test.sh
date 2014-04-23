#! /bin/sh

export GTK_IM_MODULE=ibus
export QT_IM_MODULE=ibus
export XMODIFIERS="@im=ibus"

ibus-daemon --xim --replace --daemonize #--panel=disable

exec python2 ./main.py "$@"

# vim: sw=4
