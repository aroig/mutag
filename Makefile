#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# mutag - A tagging tool for mails indexed by mu
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

SHELL = bash
PYTHON = python3

NAME = mutag
VERSION=$(shell $(PYTHON) $(NAME).py --version)

PREFIX ?= /usr
MANDIR ?= $(PREFIX)/share/man/man1
DOCDIR ?= $(PREFIX)/share/doc/$(NAME)
ZSHDIR ?= $(PREFIX)/share/zsh/site-functions
BASHDIR ?= /etc/bash_completion.d

.PHONY: all man install clean build

all: build man

build:
	ln -svf ../$(NAME).py bin/$(NAME)
	$(PYTHON) setup.py build --executable="/usr/bin/env $(PYTHON)"
	@echo
	@echo "Build process finished, run '$(PYTHON) setup.py install' to install" \
		"or '$(PYTHON) setup.py --help' for more information".

clean:
	-python setup.py clean --all
	-find . -name '*.pyc' -exec rm -f {} \;
	-find . -name '.cache*' -exec rm -f {} \;
	-find . -name '*.html' -exec rm -f {} \;
	@make -C man clean

man:
	@make -C man man

install:
	$(PYTHON) setup.py install --prefix=$(DESTDIR)$(PREFIX)
	@install -Dm755 completion/zsh/_$(NAME) $(DESTDIR)$(ZSHDIR)/_$(NAME)
#	@install -Dm755 completion/bash/$(NAME) $(DESTDIR)$(BASHDIR)/$(NAME)
	@install -Dm644 man/$(NAME).1 $(DESTDIR)$(MANDIR)/$(NAME).1
	@install -Dm644 README $(DESTDIR)$(DOCDIR)/README
#	@cp -R docs/* $(DESTDIR)$(DOCDIR)
	@cp -R conf $(DESTDIR)$(DOCDIR)/config
