#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# a parser for a sequence of plists
# Copyright 2011 Abdó Roig-Maranges <abdo.roig@gmail.com>
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


from pyparsing import *

# define punctuation literals
LPAR, RPAR, LBRK, RBRK, LBRC, RBRC, VBAR = map(Suppress, "()[]{}|")
DOT, DDOT = map(Suppress, ".:")

decimal  = Regex(r'-?0|[1-9]\d*').setParseAction(lambda t: int(t[0]))
token    = Word(alphanums + '-')
qstring  = dblQuotedString.setParseAction(removeQuotes)
string   = token | qstring
nil      = Literal("nil").setParseAction(lambda t: [None])
elem     = nil | token | qstring | string

aitem    = Group(LPAR + elem + DOT + elem + RPAR).setParseAction(lambda t: [tuple(t.asList()[0])])
alist    = Group(LPAR + ZeroOrMore(aitem) + RPAR).setParseAction(lambda t: t.asList())
slist    = Group(LPAR + ZeroOrMore(elem) + RPAR).setParseAction(lambda t: t.asList())

pkey     = DDOT + token
elplist  = Group(LPAR + ZeroOrMore(Group(pkey + elem)) + RPAR).setParseAction(lambda t: {k: v for k, v in t[0]})

pvalue   = alist | slist | elplist | elem
plist    = Group(LPAR + ZeroOrMore(Group(pkey + pvalue)) + RPAR).setParseAction(lambda t: {k: v for k, v in t[0]})
plistseq = ZeroOrMore(plist)


def parse(raw):
  pls = plistseq.parseString(raw)
  return pls.asList()
