#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# archui - a very simple arch linux style UI library
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

import sys
import re
import os

_debug      = False
_use_color  = True

cc = {"t"  : "\033[0m",      # reset
      "r"  : "\033[1;31m",   # red
      "g"  : "\033[1;32m",   # green
      "y"  : "\033[1;33m",   # yellow
      "b"  : "\033[1;34m",   # blue
      "m"  : "\033[1;35m",   # magenta
      "c"  : "\033[1;36m",   # cyan
      "w"  : "\033[1;37m",   # white

      "R"  : "\033[0;31m",   # dark red
      "G"  : "\033[0;32m",   # dark green
      "Y"  : "\033[0;33m",   # dark yellow
      "B"  : "\033[0;34m",   # dark blue
      "M"  : "\033[0;35m",   # dark magenta
      "C"  : "\033[0;36m",   # dark cyan
      "W"  : "\033[0;37m"    # dark white
      }


fc = {'done'  : '#g',
      'fail'  : '#r',
      'busy'  : '#c'
      }

mc = '#b'

_last_status = ""


def set_debug(dbg):
  global _debug
  _debug = dbg

def use_color(cl):
  global _use_color
  _use_color = cl

def set_main_color(c):
  global mc
  mc = c



def get_terminal_size():
  env = os.environ
  def ioctl_GWINSZ(fd):
    try:
      import fcntl, termios, struct, os
      cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
                                           '1234'))
    except:
      return None
    return cr
  cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
  if not cr:
    try:
      fd = os.open(os.ctermid(), os.O_RDONLY)
      cr = ioctl_GWINSZ(fd)
      os.close(fd)
    except:
      pass
  if not cr:
    cr = (None, None)
#    try:
#      cr = (env['LINES'], env['COLUMNS'])
#    except:
#      cr = (25, 80)

  if cr[0]: row = int(cr[0])
  else:     row = None

  if cr[1]: col = int(cr[1])
  else:     col = None

  return (row, col)


def get_line_width():
  row, col = get_terminal_size()
  maxcol = 80

  if col and col < maxcol: return col
  else:   return 80

def strip_color(s):
  return re.sub('\033\[[0-9;]+m', '', s)

def color(s):
  global _use_color
  ret = s + '#t'
  if _use_color:
    for k in cc: ret = ret.replace('#'+k, cc[k])
  else:
    for k in cc: ret = ret.replace('#'+k, '')
  ret = ret.replace('##', '#')
  return ret


def print_color(text, file=sys.stdout):
  file.write('%s' % color(text))
  file.flush()

def print_debug(t):
  global _debug
  if _debug: print_color("%g--> %s\n" % t, file=sys.stderr)

def print_message(text):
  print_color(" %s\n" % text, file=sys.stdout)

def print_error(text):
  print_color('#rerror: #w%s\n' % text, file=sys.stderr)

def print_warning(text):
  print_color('#ywarning: #w%s\n' % text, file=sys.stderr)



def print_item(text):
  print_color('%s * #w%s\n' % (mc, text), file=sys.stdout)

def print_heading(text):
  print_color('%s > #w%s\n' % (mc, text), file=sys.stdout)

def print_enum(i, n, text):
  print_color('%s(%d/%d) #t%s\n' % (mc, i, n, text), file=sys.stdout)



# TODO: get rid of nl where I use it
def print_status(text=None, flag=None, nl=False):
  width = get_line_width()
  fwidth = 10
  mwidth = width - fwidth

  if re.match("^.*\n\s*$", text, re.MULTILINE): nl = True
  else:                                         nl = False
  text = text.strip()

  global _last_status
  if text == None: text = _last_status
  else:            _last_status = text

  if flag:
    if flag.lower() in fc: col = fc[flag.lower()]
    else:                  col = '#w'
    sta = '%s[%s%s%s]' % (mc, col, flag, mc)

    fmt = '\r%s:: #w{0:<%s}{1:>%s}\r' % (mc, mwidth, fwidth)
    if nl: fmt = fmt + '\n'

    print_color(fmt.format(text, sta), file=sys.stdout)
  else:
    fmt = '\r%s:: #w{0:<%s}\n' % (mc, width)
    print_color(fmt.format(text), file=sys.stdout)

def print_progress(text, r):
  width = get_line_width()
  ewidth = 9
  bwidth = int(width/2 - ewidth)
  mwidth = int(width/2)

  barstr = int(r*bwidth)*'#' + (bwidth-int(r*bwidth))*'='
  fmt = ' {0:<%s} [{1}] {2:3d}%%' % mwidth

  sys.stdout.write(fmt.format(text, barstr, int(100*r)))
  sys.stdout.flush()



def ask_question_string(question):
  print_color('%s ? #w%s ' % (mc, question), file=sys.stderr)
  return input()

def ask_question_yesno(question, default=None):
  if default == 'yes':    hint = '[Y/n]'
  elif default == 'no':   hint = '[y/N]'
  else:                   hint = '[y/n]'
  while(True):
    val = ask_question_string(question + ' ' + hint)
    val = val.strip().lower()
    if val == 'y':              return 'yes'
    elif val == 'n':            return 'no'
    elif default and val == '': return default
    else: print_color('Invalid answer.\n')
