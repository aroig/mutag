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

debug      = False
use_color  = True

cc = {"t"  : "\033[0m",      # reset
      "r"  : "\033[1;31m",   # red
      "g"  : "\033[1;32m",   # green
      "y"  : "\033[1;33m",   # yellow
      "b"  : "\033[1;34m",   # blue
      "m"  : "\033[1;35m",   # magenta
      "c"  : "\033[1;36m",   # cyan
      "w"  : "\033[1;39m"    # white
      }



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
  return int(cr[0]), int(cr[1])


def get_line_width():
  row, col = get_terminal_size()
  maxcol = 80

  if col and col < maxcol: return col
  else:   return 80

def strip_color(s):
  return re.sub('\033\[[0-9;]+m', '', s)

def color(s):
  ret = s + '#t'
  if use_color:
    for k in cc: ret = ret.replace('#'+k, cc[k])
  else:
    for k in cc: ret = ret.replace('#'+k, '')
  ret = ret.replace('##', '#')
  return ret



def print_debug(t):
  if debug: print(color("%g--> ") + t)

def print_color(text):
  print(color(text))

def print_message(text):
  print_color(" " + text)

def print_error(text):
  print(color('#rerror: #w' + text + '\n'), file=sys.stderr)

def print_warning(text):
  print(color('#ywarning: #w' + text), file=sys.stderr)



def print_item(text):
  print(color('#b * #w' + text))

def print_heading(text):
  print(color('#b > #w' + text))

def print_enum(i, n, text):
  print(color('#b(%d/%d) #t%s' % (i, n, text)))



def print_status(text, flag=None, nl=False):
  width = get_line_width()
  fwidth = 10
  mwidth = width - fwidth

  if flag:
    if flag.lower() == 'fail':     sta = '#b[#r%s#b]' % flag
    elif flag.lower() == 'busy':   sta = '#b[#c%s#b]' % flag
    elif flag.lower() == 'done':   sta = '#b[#g%s#b]' % flag
    elif flag.lower() == 'start':  sta = '#b[#y%s#b]' % flag
    elif flag.lower() == 'stop':   sta = '#b[#y%s#b]' % flag
    else:                          sta = '#b[#w%s#b]' % flag

    fmt = '\r#b:: #w{0:<%s}{1:>%s}' % (mwidth, fwidth)
    sys.stdout.write(color(fmt.format(text, sta)))
    if nl: sys.stdout.write('\n')
  else:
    fmt = '\r#b:: #w{0:<%s}\n' % 70
    sys.stdout.write(color(fmt.format(text)))

def print_progress(text, r):
  width = get_line_width()
  ewidth = 9
  bwidth = int(width/2 - ewidth)
  mwidth = int(width/2)

  barstr = int(r*bwidth)*'#' + (bwidth-int(r*bwidth))*'='
  fmt = ' {0:<%s} [{1}] {2:3d}%%' % mwidth

  sys.stdout.write(fmt.format(text, barstr, int(100*r)))



def ask_question_string(question):
  sys.stderr.write(color('#b ? #w' + question + " "))
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
    else: sys.stderr.write('Invalid answer.\n')
