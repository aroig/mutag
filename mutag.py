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
from mutag.mutag import Mutag, MutagError
from mutag import __version__


def get_profile(conf, opts):

    if opts.profile: name = opts.profile
    else:            name = conf.get('mutag', 'defaultprofile')

    # TODO: catch nonexistent profile

    prof = {}
    prof['muhome'] = os.path.expanduser(conf.get('profile %s' % name, 'muhome'))
    prof['maildir'] = os.path.expanduser(conf.get('profile %s' % name, 'maildir'))

    prof['trashtag'] = conf.get('profile %s' % name, 'trashtag')
    prof['trashfolder'] = conf.get('profile %s' % name, 'trashfolder')
    prof['gmailfolders'] = set([f.strip() for f in conf.get('profile %s' % name, 'gmailfolders').split(',')])

    prof['expiredays'] = int(conf.get('profile %s' % name, 'expiredays'))

    prof['mtimelist'] = os.path.expanduser(conf.get('profile %s' % name, 'mtimelist'))
    prof['lastmtime'] = os.path.expanduser(conf.get('profile %s' % name, 'lastmtime'))
    prof['tagrules'] = os.path.expanduser(conf.get('profile %s' % name, 'tagrules'))

    if opts.muhome: prof['muhome'] = os.path.expanduser(opts.muhome)
    if opts.muhome: prof['maildir'] = os.path.expanduser(opts.maildir)

    return prof


def eval_command(opts, args):
    conf = RawConfigParser(defaults={})
    conf.read([os.path.expanduser('~/.config/mutag/mutag.conf')])
    ui.set_debug(opts.debug)

    ui.use_color(conf.getboolean("mutag", 'color'))
    # If the output is not a terminal, remove the colors
    if not sys.stdout.isatty(): ui.use_color(False)

    prof = get_profile(conf, opts)
    mutag = Mutag(prof = prof)

    # escape '\' in query so xapian understands us.
    if opts.query:
        opts.query = opts.query.replace('\\', '\\\\')

    if opts.cmd == 'autotag':
        mutag.autotag(query=opts.query, path=opts.path, modified_only=opts.modified, related=True, dryrun=opts.dryrun, silent=opts.silent)

    elif opts.cmd == 'expire':
        mutag.expire(dryrun=opts.dryrun, silent=opts.silent)

    elif opts.cmd in set(['autotag', 'expire']) and opts.index:
        mutag.index(dryrun=opts.dryrun, silent=opts.silent)

    elif opts.cmd == 'count':
        num = mutag.count(opts.query, modified_only=opts.modified)
        print(num)

    elif opts.cmd == 'dedup':
        # TODO
        print("dedup not implemented")
        sys.exit()

    elif opts.cmd == 'tag':
        L = mutag.query(opts.query, path = opts.path,
                        modified_only=opts.modified, related=False)
        mutag.change_tags(L, args, dryrun=opts.dryrun, silent=opts.silent)
        if opts.index:
            mutag.index(dryrun=opts.dryrun, silent=opts.silent)

    elif opts.cmd == 'flag':
        L = mutag.query(opts.query, path = opts.path,
                        modified_only=opts.modified, related=False)
        mutag.change_flags(L, args, dryrun=opts.dryrun, silent=opts.silent)
        if opts.index:
            mutag.index(dryrun=opts.dryrun, silent=opts.silent)

    elif opts.cmd == 'list':
        L = mutag.query(opts.query, path = opts.path,
                        modified_only=opts.modified, related=False)
        for msg in L:
            ui.print_color(msg.tostring(fmt=opts.format))

    elif opts.cmd == 'print':
        L = mutag.query(opts.query, path = opts.path,
                        modified_only=opts.modified, related=False)
        for msg in L:
            print(msg.raw())

    elif opts.cmd == 'filename':
        L = mutag.query(opts.query, path = opts.path,
                        modified_only=opts.modified, related=False)
        for msg in L:
            print(msg['path'])

    elif opts.cmd == 'rebuild':
        mutag.rebuild(dryrun=opts.dryrun, silent=opts.silent)

    elif opts.cmd == 'trash':
        mutag.empty_trash(dryrun=opts.dryrun, silent=opts.silent)

    # Index if asked to and not done in a specific command
    if opts.index and not opts.cmd in ['autotag', 'tag', 'rebuild']:
        mutag.index(dryrun=opts.dryrun, silent=opts.silent)

    # Update mtime
    if opts.update:
        mutag.update_mtime(dryrun=opts.dryrun, silent=opts.silent)

    # commit mail
    if opts.commit:
        mutag.commit(dryrun=opts.dryrun, silent=opts.silent)




# Main stuff
# -----------------------

usage = """usage: %prog [options] [-q <query>] <tags>
"""

parser = OptionParser(usage=usage)

# Commands
parser.add_option("-C", "--count", action="store_const", const="count", default=None, dest="cmd",
                  help="Count messages")

parser.add_option("-A", "--autotag", action="store_const", const="autotag", default=None, dest="cmd",
                  help="Tag rule to apply")

parser.add_option("-E", "--expire", action="store_const", const="expire", default=None, dest="cmd",
                  help="Expire old messages")

parser.add_option("-D", "--dedup", action="store_const", const="dedup", default=None, dest="cmd",
                  help="Remove duplicate message with same uid content on same folder")

parser.add_option("-T", "--tag", action="store_const", const="tag", default=None, dest="cmd",
                  help="Change tags")

parser.add_option("-G", "--flag", action="store_const", const="flag", default=None, dest="cmd",
                  help="Change flags")

parser.add_option("-L", "--list", action="store_const", const="list", default=None, dest="cmd",
                  help="List messages")

parser.add_option("-P", "--print", action="store_const", const="print", default=None, dest="cmd",
                  help="Print raw messages")

parser.add_option("-F", "--filename", action="store_const", const="filename", default=None, dest="cmd",
                  help="Print the filenames")

parser.add_option("--rebuild", action="store_const", const="rebuild", default=None, dest="cmd",
                  help="rebuilds the entire database and quits")

parser.add_option("--empty-trash", action="store_const", const="trash", default=None, dest="cmd",
                  help="empties the trash folder")




# queries
parser.add_option("-q", "--query", action="store", type="string", default=None, dest="query",
                  help="mu query to which the action is restricted. Default is none")

parser.add_option("-m", "--modified", action="store_true", default=False, dest="modified",
                  help="Restricts to messages that are modified since last call to mutag -u")

parser.add_option("-t", "--target", action="store", type="string", default=None, dest="path",
                  help="Restrict to the message at the given path")


# Options
parser.add_option("-p", "--profile", action="store", type="string", default=None, dest="profile",
                  help="Select a configuration profile")

parser.add_option("-f", "--format", action="store", type="string", default='compact', dest="format",
                  help="Format to print output")

parser.add_option("-u", "--update", action="store_true", default=False, dest="update",
                  help="Update list of modification times for the files.")

parser.add_option("-i", "--index", action="store_true", default=False, dest="index",
                  help="Index new messages")

parser.add_option("-c", "--commit", action="store_true", default=False, dest="commit",
                  help="Commit mail if stored in a git repo")


parser.add_option("-s", "--silent", action="store_true", default=False, dest="silent",
                  help="Runs silently.")

parser.add_option("--dryrun", action="store_true", default=False, dest="dryrun",
                  help="Performs a dry run. Does not change anything on disk.")

parser.add_option("--muhome", action="store", type="string", default=None, dest="muhome",
                  help="Path to the mu database")

parser.add_option("--maildir", action="store", type="string", default=None, dest="maildir",
                  help="Path to maildir")

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

except MutagError as err:
    ui.print_error(str(err))
    sys.exit(1)

except KeyboardInterrupt:
    print("")
    sys.exit()

except EOFError:
    print("")
    sys.exit()

# vim: expandtab:shiftwidth=4:tabstop=4:softtabstop=4:textwidth=80
