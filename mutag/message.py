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

from email.parser import Parser
from email import charset

# Set the email charset to quoted printable for headers and content.
charset.add_charset('utf-8', charset.QP, charset.QP)


class Message(dict):
  def __init__(self):
    super().__init__()
    self.msg = None
    self.headers = None
    self.tagsheader = 'X-Keywords'


  def load_message(self):
    with open(self['path'], 'r') as fd:
      self.msg = Parser().parse(fd)


  def load_headers(self):
    with open(self['path'], 'r') as fd:
      self.headers = Parser().parse(fd, headersonly=True)


  def get_content(self):
    if not self.msg:
      self.load_message()

    payload = self.msg.get_payload(decode=True)
    return payload.decode('utf-8')


  def get_tags(self):
    if self.msg != None:
      msg = self.msg
    elif self.headers != None:
      msg = self.headers
    else:
      self.load_headers()
      msg = self.headers

    if self.tagsheader.lower() in msg:
      tags = set([t.strip() for t in msg[self.tagsheader.lower()].split(',') if len(t.strip()) > 0])
    else:
      tags = set()
    return tags


  def message_addheader(self, content, headername, headervalue):
    """Changes the value of headername to headervalue if the header exists,
    or adds it if it does not exist"""

    insertionpoint = content.find("\n\n")
    leader = content[0:insertionpoint]

    if insertionpoint == 0 or insertionpoint == -1:
      newline = ''
      insertionpoint = 0
    else:
      newline = "\n"

    if re.search('^%s:(.*)\n' % headername, leader + '\n', re.MULTILINE):
      leader = re.sub('%s:(.*)\n', '%s: %s\n' % (headername, headervalue),
                        leader)
    else:
      leader = leader + newline + "%s: %s" % (headername, headervalue)

    trailer = content[insertionpoint:]
    return leader + trailer


  def set_tags(self, tags):
    with open(self['path'], 'r') as fd:
      content = fd.read()

    # change tags
    tags_str = ', '.join(sorted(tags))
    content = self.message_addheader(content, self.tagsheader, tags_str)

    # save changed file into temp path
    tmppath = os.path.join(os.path.basename(os.path.dirname(self['path'])), 'tmp', os.path.basename(self['path']))
    with open(tmppath, 'w') as fd:
      fd.write(content)

    # move back to initial position
    os.rename(tmppath, self['path'])


  def get_mtime(self):
    return long(os.stat(self['path']).st_mtime)


  def __str__(self):
    for k in self:
      print('{0>10}: {1}'.format(k, str(self[k])))
