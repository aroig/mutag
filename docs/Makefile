#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# paur - A unified interface to pacman and AUR
# Copyright 2012 Abdó Roig-Maranges <abdo.roig@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

SOURCES = $(wildcard *.rst)
HTML_TARGETS = $(patsubst %.rst,%.html,$(SOURCES))
MAN_TARGETS = mutag.1

RM = rm
RST2HTML=`type rst2html >/dev/null 2>&1 && echo rst2html || echo rst2html.py`
RST2MAN=`type rst2man >/dev/null 2>&1 && echo rst2man || echo rst2man.py`

all: man html

html: $(HTML_TARGETS)

$(HTML_TARGETS): %.html : %.rst
	$(RST2HTML) $? $@

man: $(MAN_TARGETS)

$(MAN_TARGETS): % : %.rst
	$(RST2MAN) $? $@

clean:
	$(RM) -f $(HTML_TARGETS)
	$(RM) -f $(MAN_TARGETS)

.PHONY: clean
