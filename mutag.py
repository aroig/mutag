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


import os
import sys

from optparse import OptionParser, OptionGroup
from configparser import RawConfigParser

import mutag.archui as ui
from mutag.mutag import Mutag
from mutag import __version__


def eval_command(opts, args):
  conf = RawConfigParser(defaults={})
  conf.read([os.path.expanduser('~/.config/mutag/mutag.conf')])
  ui.set_debug(opts.debug)

  ui.use_color(conf.getboolean("mutag", 'color'))
  # If the output is not a terminal, remove the colors
  if not sys.stdout.isatty(): ui.use_color(False)

  mutag = Mutag(conf=conf,
                muhome=opts.muhome)

  if opts.query == None:
    print("No query given")

  # Get the messages
  L = mutag.query(opts.query, modified_only=opts.changed)

  if opts.autotag:
    # Perform autotagging
    mutag.autotag(L, opts.autotag, dryrun=opts.dryrun)

  elif len(args) == 0:
    # List the messages matching the query
    for msg in L:
      ui.print_color(msg.tostring(fmt='compact'))

  else:
    # Change tags
    mutag.change_tags(L, args, dryrun=opts.dryrun)




# Main stuff
# -----------------------

usage = """usage: %prog [options] [-q <query>] <tags>
"""

parser = OptionParser(usage=usage)

parser.add_option("-q", "--query", action="store", type="string", default=None, dest="query",
                  help="mu query to which the action is restricted. Default is none")

parser.add_option("-c", "--changed", action="store_true", default=False, dest="changed",
                  help="Restricts to messages that changed on disk since last run")

parser.add_option("-a", "--autotag", action="store", type="string", default=None, dest="autotag",
                  help="Tag rule to apply")

parser.add_option("--dryrun", action="store_true", default=False, dest="dryrun",
                  help="Performs a dry run. Does not change anything on disk.")

parser.add_option("--muhome", action="store", type="string", default='~/.mu', dest="muhome",
                  help="Path to the mu database")

parser.add_option("--version", action="store_true", default=False, dest="version",
                  help="Print the version and exit")

parser.add_option("--debug", action="store_true", default=False, dest="debug",
                  help="Print debug information")



(opts, args) = parser.parse_args()

if opts.version:
  print(__version__)
  sys.exit(0)


try:
  eval_command(opts, args)

except KeyboardInterrupt:
  print("")
  sys.exit()

except EOFError:
  print("")
  sys.exit()
