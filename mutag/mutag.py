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


  def parsefiles(self, filelist):
    L = []
    for path in filelist:
      path = os.path.abspath(os.path.expanduser(path))
      if os.path.isfile(path):
        rpath = os.path.realpath(path)
        rmaildir = os.path.realpath(self.maildir)
        if os.path.commonprefix([rpath, rmaildir]) == rmaildir:
          msg = Message()
          msg.from_file(path, maildir=self.maildir)
          L.append(msg)
        else:
          ui.print_error("File does not belong to the configured maildir:\n%s" % path)
      else:
        ui.print_error("File does not exist:\n%s" % path)
    return L


  def modified(self, mtime):
    L = []
    for mp in self.get_maildir_files():
      mt = int(os.stat(mp).st_mtime)
      if mt > mtime:
        msg = Message()
        msg.from_file(mp, maildir=self.maildir)
        L.append(msg)
    return L

  def query_mu(self, query):

    # split the query string
    qlist = shlex.split(query)

    # parse sexp
    try:
      sexpdata = self._mu('find', ['--threads', '--format', 'sexp'] + qlist, silent=True, catchout=True)
      L = self._parse_msgsexp(sexpdata)
    except subprocess.CalledProcessError as err:
      if err.returncode == 4:   # No results
        L = []
      else:
        raise

    # Fills in 'threademails' and 'threadroot' fields from threading data
    self.collect_thread_data(L)

    return L


  def query(self, query=None, path=None, modified_only=False):
    if path:
      return self.parsefiles([path])
    elif modified_only:
      mtime = self.get_last_mtime()
      return self.modified(mtime)
    elif query:
      return self.query_mu(query)
    else:
      return []


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


  def collect_thread_data(self, msglist):
    class Node (dict):
      value = None     # message at the node
      root  = None     # oldest ancestor with value != None
      data  = None     # collected thata for the children
      child = None     # dict of children

    threads = Node()

    # populate a tree rooted on threads node
    for msg in msglist:
      if 'thread' in msg:
        pth = threads
        for k in msg['thread']:
          if not pth.child:
            pth.child = {}
          if not k in pth.child:
            pth.child[k] = Node()
          pth = pth.child[k]

        pth.value = msg

    # Recursively collect data
    def _collect_thread_data_rec(node, root):

      if root == None and node.value != None:
        root = node

      node.root = root
      node.data = {'emails': set()}

      if node.value:
        node.data['emails'].update(node.value['emails'])

      if node.child:
        for child in node.child.values():
          _collect_thread_data_rec(child, root)
          node.data['emails'].update(child.data['emails'])


    # Recursively update msg objects
    def _collect_thread_update_msg_rec(node):
      if node.root != None and node.value != None:
        node.value['threademails'] = node.root.data['emails']
        node.value['threadroot']   = node.root.value['message-id']

      if node.child:
        for child in node.child.values():
          _collect_thread_update_msg_rec(child)

    _collect_thread_data_rec(threads, None)
    _collect_thread_update_msg_rec(threads)



  def autotag(self, msglist, dryrun=False):
    try:
      fd = open(self.tagrules_path, 'r')
      rawcode = fd.read()
    except:
      ui.print_error("Can't open tagrules at %s" % self.tagrules_path)
      return

    try:
      rules = imp.new_module('tagrules')
      exec(rawcode, rules.__dict__)
      tr = rules.TagRules()
    except Exception as err:
      ui.print_error("Exception loading tagrules %s\n%s" % (self.tagrules_path, str(err)))
      return

    for msg in msglist:
      tags = msg.get_tags()
      newtags = tr.get_tags(msg)
      ui.print_debug("%s -> %s" % (', '.join(tags), ', '.join(newtags)))
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
