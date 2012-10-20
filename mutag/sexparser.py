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

# Based on http://rosettacode.org/wiki/S-Expressions


import re

term_regex = r'''(?mx)
    \s*(?:
        (?P<brackl>\()|
        (?P<brackr>\))|
        (?P<num>\d+\.\d+|\d+)\b|
        (?P<sq>"[^"]*")|
        (?P<nil>nil)\b|
        (?P<dot>\.)|
        (?P<s>\S+)\b
       )'''


def plist_to_dict(lst):
  d = {}
  for i in range(0, len(lst)):
    if i % 2 == 0:
      if type(lst[i]) == str:
        m = re.match(':(.*)', lst[i])
        if m:
          k = m.group(1)
          continue
      return None
    else:
      d[k] = lst[i]
  return d


def alist_to_tuplelist(lst):
  L = []
  for it in lst:
    if type(it) == type([]) and len(it) == 3 and it[1] == '.':
      L.append((it[0], it[2]))
    else:
      return None
  return L



def parse_sexp(sexp):
  stack = []
  out = []
  for termtypes in re.finditer(term_regex, sexp):
    term, value = [(t,v) for t,v in termtypes.groupdict().items() if v][0]
    if   term == 'brackl':
      stack.append(out)
      out = []

    elif term == 'brackr':
      assert stack, "Trouble with nesting of brackets"
      tmpout, out = out, stack.pop(-1)

      d = plist_to_dict(tmpout)
      if d:
        out.append(d)
        continue

      tl = alist_to_tuplelist(tmpout)
      if tl:
        out.append(tl)
        continue

      out.append(tmpout)

    elif term == 'num':
      v = float(value)
      if v.is_integer(): v = int(v)
      out.append(v)

    elif term == 'sq':
      out.append(value[1:-1])

    elif term == 's':
      out.append(value)

    elif term == 'nil':
      out.append(None)

    elif term == 'dot':
      out.append('.')

    else:
      raise NotImplementedError("Error: %r" % (term, value))

  assert not stack, "Trouble with nesting of brackets"
  return out[0]


def print_sexp(exp):
  out = ''
  if type(exp) == type([]):
    out += '(' + ' '.join(print_sexp(x) for x in exp) + ')'
  elif type(exp) == type({}):
    out += '(' + ' '.join(':%s %s' % (k, print_sexp(v)) for k,v in exp) + ')'
  elif type(exp) == type('') and re.search(r'[\s()]', exp):
    out += '"%s"' % repr(exp)[1:-1].replace('"', '\"')
  elif exp == None:
    out += 'nil'
  else:
    out += '%s' % exp
  return out
