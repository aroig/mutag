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


# { 'size': 691,
#   'tags': set(['mail', 'bla', '\\\\Inbox', 'ornitorrinc', 'abcd', 'mamut', '\\\\Sent', 'sdf']),
#   'to': [],
#   'date': datetime.datetime(2008, 9, 29, 11, 19, 38),
#   'priority': 'normal',
#   'flags': {'seen'},
#   'message-id': '6c19a60e0809290730h76c42c9fg8664aa60ff413f9e@mail.gmail.com',
#   'fromstr': 'Abdó <abdo.roig@gmail.com>',
#   'path': '/home/abdo/Projects/offlineimap-gmail/mail/All Mail/cur/1350601747_2.15371.grothendieck,U=3,FMD5=883ba13d52aa35908bd3344dc0604026:2,S',
#   'docid': 3,
#   'emails': {'abdo.roig@gmail.com'},
#   'subject': 'test',
#   'maildir': '/All Mail',
#   'from': [{'name': 'Abdó', 'email': 'abdo.roig@gmail.com'}],
#   'tostr': ''
# }


import os
import re
import json
import subprocess

class TagRules(object):

  # Initialization
  # --------------------------

  def __init__(self):
    super().__init__()

    # Do initializations of the object, like setting variables, etc.
    # You can also load external data here.

    # For example, you can declare a dictionary of addresses for which you
    # want special tags.
    self.taglist = {
      'emacs-orgmode@gnu.org'   : ['list', 'org'],
      'bla@gmail.com'           : ['boss']
      # etc.
      }

    # Rules to apply
    self.rules = [
      ('contacts',     self._tags_taglist),
      # Whatever rules you like to apply
      ]


  # Interface
  # --------------------------

  # This is the only required function. It takes a message as argument,
  # and returns a set of tags that will replace the current msg tags.

  def get_tags(self, msg):
    tags = msg.get_tags()
    for rname, rfunc in self.rules:
      rfunc(msg, tags)
    return tags


  # The tagging rules
  # --------------------------

  # apply tags according to the taglist dictionary.
  # msg: the message
  # tags: a set of currently computed tags.
  def _tags_taglist(self, msg, tags):
    for k, val in self.taglist.items():
      if k in msg['emails']:
        tags.update(val)
