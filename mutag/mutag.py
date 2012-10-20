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
import subprocess
from datetime import datetime

from mutag.sexparser import parse_sexp
from mutag.message import Message

# TODO: establish some user interface guidelines

class MutagError(Exception):
  def __init__(self, msg=None):
    super().__init(msg)


class Mutag(object):
  def __init__(self, conf, muhome, maildir):
    self.conf = conf
    self.muhome = muhome
    self.maildir = maildir

  def _mu(self, cmd, args):
    mu_cmd = 'mu'
    try:
      ret = subprocess.check_output([mu_cmd, cmd, '--muhome', self.muhome] + args)
    except subprocess.CalledProcessError:
      print("Something went wrong")
      raise

    return ret.encode('utf-8')

  def _import_module(path):
    return __import__(path, globals(), locals(), [''])


  def get_last_mtime(self):
    path = os.path.expanduser(self.conf.get('paths', 'lastmtime'))
    try:
      with open(path, 'r') as fd:
        mtime = long(fd.read())
    except OSError:
      mtime = 0
    return mtime


  def save_last_mtime(self, mtime):
    path = os.path.expanduser(self.conf.get('paths', 'lastmtime'))
    with open(path, 'w') as fd:
      fd.write(str(mtime))


  def _parse_msgsexp(self, sexp):
    data = parse_sexp(sexpdata)
    L = []
    for s in data:
      msg = Message()

      for k in ['docid', 'maildir', 'message-id', 'path', 'priority', 'size', 'subject']:
        msg[k] = data[k]

      for k in ['from', 'to']:
        msg[k] = {'name': d[k][0], 'email':d[k][1]}

      for k in ['flags']:
        msg[k] = set(d[k])

      msg['date'] = datetime.fromtimestamp(d[0]*0xFFFF + d[1])

      L.append(msg)
    return L


  def query(self, query, modified_only=False):
    sexpdata = self._mu('find', [query, '--format', 'sexp'])
    L = self._parse_msgsexp('(%s)' % sexpdata)

    if modified_only:
      mtime = self.get_last_mtime()
      return [msg for msg in L if msg.get_mtime() >= mtime]
    else:
      return L


  def print_tagschange(self, msg, oldtags, newtags):
    # TODO
    pass


  def change_tags(self, msglist, tagactions):
    for ta in tagactions:
      addtags = set()
      deltags = set()

      mdel = re.search('^\s*-(.*)\s*$', ta)
      madd = re.search('^\s*\+(.*)\s*$', ta)
      if mdel:   deltags.add(mdel.group(1))
      elif madd: addtags.add(madd.group(1))
      else:      addtags.add(ta.strip())

    for msg in msglist:
      tags = msg.get_tags()
      newtags = tags.union(addtags).difference(deltags)
      self.print_tagschange(msg, tags, newtags)
      if not dryrun: msg.set_tags(newtags)


  def autotag(self, msglist, tagrules, dryrun=False):
    trpath = os.path.join(bla, 'tagrules', tagrules + '.py')
    if not os.path.exists(trpath):
      print("Can't find tagrules file %s.py." % tagrules)
      raise MutagError()

    rules = self._import_module(trpath)
    tr = rules.TagRules()

    for msg in msglist:
      tags = msg.get_tags()
      newtags = tr.get_tags(msg)
      if tags != newtags:
        self.print_tagschange(msg, tags, newtags)
        if not dryrun: msg.set_tags(newtags)
