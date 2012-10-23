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
import re
import sys
import imp
import glob
import shlex
import subprocess

import mutag.plistseq as plistseq
from mutag.message import Message
import mutag.archui as ui

class MutagError(Exception):
  def __init__(self, msg=None):
    super().__init__(msg)


class Mutag(object):
  def __init__(self, prof):
    self.muhome = prof['muhome']
    self.maildir = prof['maildir']
    self.tagrules_path = prof['tagrules']
    self.lastmtime_path = prof['lastmtime']


  def _mu(self, cmd, args, catchout=False, silent=False):
    mu_cmd = 'mu'
    with open('/dev/null', 'w') as devnull:
      if silent: out = devnull
      else:      out = None
      cmd_args = [mu_cmd, cmd, '--muhome', self.muhome] + args
      if catchout:
        ret = subprocess.check_output(cmd_args, stderr=out)
        return ret.decode('utf-8')
      else:
        subprocess.check_call(cmd_args, stdout=out, stderr=out)


  def _import_module(self, path):
    name = os.path.basename(path).split('.')[0]
    dirname = os.path.dirname(path)
    file, pathname, desc = imp.find_module(name, path=[dirname])
    return imp.load_module(name, file, pathname, desc)


  def _parse_msgsexp(self, sexpstr):
    data = plistseq.parse(sexpstr)
    L = []
    for d in data:
      msg = Message()
      msg.from_mudict(d)
      L.append(msg)
    return L


  def get_maildir_files(self):
    files = []
    for fd in os.listdir(self.maildir):
      path = os.path.join(self.maildir, fd)
      if os.path.isdir(path) and not os.path.exists(os.path.join(path, ".noindex")):
        for mp in glob.glob(os.path.join(path, '*/*')):
          if os.path.isfile(mp):
            files.append(mp)
    return files


  def get_last_mtime(self):
    try:
      with open(self.lastmtime_path, 'r') as fd:
        mtime = int(fd.read())
    except OSError:
      mtime = 0
    return mtime


  def save_last_mtime(self, mtime):
    with open(self.lastmtime_path, 'w') as fd:
      fd.write(str(mtime))


  def modified(self, mtime=None):
    L = []
    if mtime == None: mtime = self.get_last_mtime()
    for mp in self.get_maildir_files():
      mt = int(os.stat(mp).st_mtime)
      if mt > mtime:
        msg = Message()
        msg.from_file(mp, maildir=self.maildir)
        L.append(msg)
    return L


  def query(self, query, modified_only=False):
    # None query matches all
    if query == None:
      qlist = ['']
    else:
      qlist = shlex.split(query)

    # Return a list of modified messages
    if modified_only:
      return self.modified()

    # Otherwise make a query to mu
    try:
      sexpdata = self._mu('find', ['--format', 'sexp'] + qlist, silent=True, catchout=True)
      L = self._parse_msgsexp(sexpdata)
    except subprocess.CalledProcessError as err:
      if err.returncode == 4:   # No results
        L = []
      else:
        raise
    return L


  def count(self, query, modified_only=False):
    return len(self.query(query, modified_only))


  def print_tagschange(self, msg, oldtags, newtags):
    alltags = oldtags.union(newtags)
    L = []
    for t in sorted(alltags):
      if t in oldtags and t in newtags:       L.append('#Y%s' % t)
      elif t in oldtags and not t in newtags: L.append('#R-%s' % t)
      elif not t in oldtags and t in newtags: L.append('#G+%s' % t)
    tagch = '#W, '.join(L)
    ui.print_color('#C{0} #W[{1}#W]\n'.format(msg['subject'], tagch))


  def change_tags(self, msglist, tagactions, dryrun=False):
    addtags = set()
    deltags = set()
    for ta in tagactions:
      mdel = re.search('^\s*-(.*)\s*$', ta)
      madd = re.search('^\s*\+(.*)\s*$', ta)

      if mdel:   deltags.add(mdel.group(1))
      elif madd: addtags.add(madd.group(1))
      else:      addtags.add(ta.strip())

    for msg in msglist:
      tags = msg.get_tags()
      newtags = tags.union(addtags).difference(deltags)
      if tags != newtags:
        self.print_tagschange(msg, tags, newtags)
        if not dryrun: msg.set_tags(newtags)


  def autotag(self, msglist, dryrun=False):
    try:
      rules = self._import_module(self.tagrules_path)
    except ImportError:
      ui.print_error("Can't find tagrules path %s" % self.tagrules_path)
      return

    try:
      tr = rules.TagRules()
    except AttributeError:
      ui.print_error("Can't find class TagRules in %s.py" % tagrules)
      return

    for msg in msglist:
      tags = msg.get_tags()
      newtags = tr.get_tags(msg)
      if tags != newtags:
        self.print_tagschange(msg, tags, newtags)
        if not dryrun: msg.set_tags(newtags)


  def index(self, dryrun=False):
    if not dryrun: self._mu('index', ['--maildir', self.maildir, '--autoupgrade'], catchout=False)


  def update_mtime(self, dryrun=False):
    L = self.get_maildir_files()
    if len(L) > 0:
      mtime = max([int(os.stat(mp).st_mtime) for mp in L])
      if not dryrun: self.save_last_mtime(mtime)
