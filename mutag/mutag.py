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
import subprocess
from datetime import datetime

from mutag.sexparser import parse_sexp
from mutag.message import Message
import mutag.archui as ui

# TODO: establish some user interface guidelines

class MutagError(Exception):
  def __init__(self, msg=None):
    super().__init__(msg)


class Mutag(object):
  def __init__(self, conf, muhome):
    self.conf = conf
    self.muhome = muhome
    self.tagrules_path = os.path.expanduser(self.conf.get('paths', 'tagrules'))


  def _mu(self, cmd, args):
    mu_cmd = 'mu'
    try:
      ret = subprocess.check_output([mu_cmd, cmd, '--muhome', self.muhome] + args)
    except subprocess.CalledProcessError:
      print("Something went wrong")
      raise
    return ret.decode('utf-8')


  def _import_module(self, name):
    file, pathname, desc = imp.find_module(name, path=[self.tagrules_path])
    return imp.load_module(name, file, pathname, desc)


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
    data = parse_sexp(sexp)
    L = []
    for d in data:
      msg = Message()

      for k in ['docid', 'maildir', 'message-id', 'path', 'priority', 'size']:
        if k in d: msg[k] = d[k]
        else:      msg[k] = None

      for k in ['subject']:
        if k in d: msg[k] = d[k]
        else:      msg[k] = ""

      for k in ['from', 'to']:
        if k in d: msg[k] = [{'name': x[0], 'email':x[1]} for x in d[k]]
        else:      msg[k] = []

        if k in d: msg[k+'str'] = ', '.join(['%s <%s>' % (x['name'], x['email']) for x in msg[k]])
        else:      msg[k+'str'] = ''

      msg['emails'] = set([ad['email'] for ad in msg['to']]).union([ad['email'] for ad in msg['from']])

      for k in ['flags', 'tags']:
        if k in d: msg[k] = set(d[k])
        else:      msg[k] = None

      if 'date' in d: msg['date'] = datetime.fromtimestamp(d['date'][0]*0xFFFF + d['date'][1])
      else:           msg['date'] = None

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
    alltags = oldtags.union(newtags)
    L = []
    for t in sorted(alltags):
      if t in oldtags and t in newtags:       L.append('#W%s' % t)
      elif t in oldtags and not t in newtags: L.append('#R-%s' % t)
      elif not t in oldtags and t in newtags: L.append('#G+%s' % t)
    tagch = ' '.join(L)
    ui.print_color('#C{0} {1}\n'.format(msg['subject'], tagch))


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
      self.print_tagschange(msg, tags, newtags)
      if not dryrun: msg.set_tags(newtags)


  def autotag(self, msglist, tagrules, dryrun=False):
    try:
      rules = self._import_module(tagrules)
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
