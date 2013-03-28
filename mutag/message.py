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
import pprint

from datetime import datetime
from email.parser import BytesParser
from email.generator import BytesGenerator
from email.header import decode_header
import email.utils

from email import charset
# Set the email charset to quoted printable for headers and content.
charset.add_charset('utf-8', charset.QP, charset.QP)


class Message(dict):
    _tags_sep = {'default'   : ', ',
                'X-Keywords': ', ',
                'X-Label'   : ' ',
                'Keywords'  : ' '}


    def __init__(self):
        super().__init__()
        self.msg = None
        self.headers = None
        self.tagsheader = 'X-Keywords'


    def tostring(self, fmt='compact'):
        if fmt == 'compact':
            if len(self['from']) > 0:
                author = '%s <%s>' % (self['from'][0]['name'], self['from'][0]['email'])
            else:
                author = ' <none> '
            tagstr = '#W, '.join(sorted(['#Y%s' % t for t in self['tags']]))
            datestr = self['date'].strftime('%Y-%m-%d %H:%M')
            return '#M{0} #C{1} #G{2} #W[{3}#W]'.format(datestr, author, str(self['subject']), tagstr)

        elif fmt == 'raw':
            return pprint.pformat(self, indent=2) + '\n\n'


    def raw(self):
        with open(self['path'], 'r', errors='ignore') as fd:
            return fd.read()


    def _fill_derived_fields(self):
        msg = self
        for k in ['from', 'to', 'cc']:
            msg[k+'str'] = ', '.join(['%s <%s>' % (x['name'], x['email']) for x in self[k]])

        msg['emails'] = set([ad['email'] for ad in msg['to']]) | \
                        set([ad['email'] for ad in msg['from']]) | \
                        set([ad['email'] for ad in msg['cc']])

        msg['thread-emails'] = set(msg.get('emails', set([])))
        msg['thread-root'] = str(msg.get('message-id', ""))



    def get_header(self, header):
        if header in self.headers:
            # TODO: may want to use self.headers.get_all(), which returns a list and catches all of the headers
            raw = self.headers.get(header, "")
            ret = ""
            for txt, enc in decode_header(raw):
                if enc == 'unknown':
                    ret = ret + str(txt, 'ascii', errors='ignore')
                elif enc == 'unknown-8bit':
                    ret = ret + str(txt, 'utf-8', errors='ignore')
                elif enc:
                    ret = ret + str(txt, enc, errors='ignore')
                elif type(txt) != str:
                    ret = ret + str(txt, 'utf-8', errors='ignore')
                else:
                    ret = ret + txt
            return ret
        else:
            return ""


    def from_mudict(self, d):
        msg = self

        for k in ['docid', 'maildir', 'message-id', 'path', 'priority']:
            if k in d: msg[k] = d[k]
            else:      msg[k] = None

        for k in ['subject']:
            if k in d: msg[k] = d[k]
            else:      msg[k] = ""

        for k in ['from', 'to', 'cc']:
            if k in d: msg[k] = [{'name': x[0], 'email':x[1].lower()} for x in d[k]]
            else:      msg[k] = []

        for k in ['flags', 'tags']:
            if k in d: msg[k] = set(d[k])
            else:      msg[k] = set([])

        msg['size'] = int(d['size'])
        if 'date' in d: msg['date'] = datetime.fromtimestamp(int(d['date'][0])*0xFFFF + int(d['date'][1]))
        else:           msg['date'] = None

        if 'thread' in d:
            msg['thread'] = tuple(d['thread']['path'].split(':'))

        self._fill_derived_fields()


    def from_file(self, path, maildir):
        msg = self
        msg['path'] = path
        self.load_headers()
        # TODO: priority, flags, size

        # Parse filename
        m = re.search('^(/[^/]*)/(cur|new|tmp)/(.*)$', path.replace(maildir, ''))
        if m:
            msg['maildir'] = m.group(1)
            fname = m.group(3)
            m = re.search('U=([0-9]*)', fname)
            if m:
                msg['docid'] = int(m.group(1))

        # TODO: should I remove < > from message-id ?
        msg['message-id'] = self.get_header('message-id')
        msg['subject'] = self.get_header('subject')
        datetup = email.utils.parsedate_tz(self.get_header('date'))
        if datetup:
            # TODO: implement proper handling of timezones!
            utfoffset = datetup[9]
            msg['date'] = datetime(*datetup[0:6])
        else:
            msg['date'] = None

        msg['to'] = [{'name': x[0], 'email': x[1].lower()}
                     for x in email.utils.getaddresses([self.get_header('to')])]

        msg['from'] = [{'name': x[0], 'email': x[1].lower()}
                       for x in email.utils.getaddresses([self.get_header('from')])]

        msg['cc'] = [{'name': x[0], 'email': x[1].lower()}
                     for x in email.utils.getaddresses([self.get_header('cc')])]

        if self.tagsheader in self.headers:
            msg['tags'] = set([t.strip() for t in self.headers[self.tagsheader].split(',') if len(t.strip()) > 0])
        else:
            msg['tags'] = set()

        self._fill_derived_fields()


    def load_message(self):
        with open(self['path'], 'rb') as fd:
            self.msg = BytesParser().parse(fd)


    def load_headers(self):
        with open(self['path'], 'rb') as fd:
            self.headers = BytesParser().parse(fd, headersonly=True)


    def get_content(self):
        if not self.msg:
            self.load_message()

        payload = []
        for part in self.msg.walk():
            if 'text/' in part.get_content_type():
                payload.append(part.get_payload(decode=True).decode('utf-8'))
        return '\n'.join(payload)


    def message_addheader(self, content, headername, headervalue):
        """Changes the value of headername to headervalue if the header exists,
        or adds it if it does not exist"""

        headername = headername.encode()
        header = headername + b': ' + headervalue.encode()

        insertionpoint = content.find(b"\n\n")

        if insertionpoint == 0 or insertionpoint == -1:
            newline = b''
            insertionpoint = 0
            leader = b''
        else:
            newline = b'\n'
            leader = content[0:insertionpoint]

        if re.search(b'^' + headername + b':(.*)$', leader, flags = re.MULTILINE):
            leader = re.sub(b'^' + headername + b':(.*)$', header, leader,
                            flags = re.MULTILINE)
        else:
            leader = leader + newline + header

        trailer = content[insertionpoint:]
        return leader + trailer


    def set_flags(self, flags):
        """Sets flags of message"""
        # careful, we need flagstr in alphabetical order!
        flagstr = ''
        if 'draft' in flags: flagstr = flagstr + 'D'
        if 'flagged' in flags: flagstr = flagstr + 'F'
        if 'seen' in flags: flagstr = flagstr + 'S'
        if 'passed' in flags: flagstr = flagstr + 'P'
        if 'replied' in flags: flagstr = flagstr + 'R'
        if 'trashed' in flags: flagstr = flagstr + 'T'

        if self['path'] and set(flags) != set(self['flags']):
            path, basename = os.path.split(re.sub(':2,[SDFTRP]*$', '', self['path']))
            path, subdir = os.path.split(path)
            newpath = os.path.join(path, 'cur', basename + ":2,%s" % flagstr)

            if newpath != self['path']:
                os.link(self['path'], newpath)
                os.unlink(self['path'])
                self['path'] = newpath


    def set_tags(self, tags):
        """Sets tags of message"""
        with open(self['path'], 'rb') as fd:
            content = fd.read()

        # change tags
        sep = self._tags_sep.get(self.tagsheader, self._tags_sep['default'])
        tags_str = sep.join(sorted(tags))
        content = self.message_addheader(content, self.tagsheader, tags_str)

        # save changed file into temp path
        parent = os.path.dirname(os.path.dirname(self['path']))
        tmppath = os.path.join(parent, 'tmp', os.path.basename(self['path']))

        with open(tmppath, 'wb') as fd:
            fd.write(content)

        # move back to initial position
        os.rename(tmppath, self['path'])

        # update tags
        self['tags'] = set(tags)


    def get_mtime(self):
        return int(os.stat(self['path']).st_mtime)


    def __str__(self):
        ret = ""
        for k in self:
            ret = ret + '{0}: {1}\n'.format(k, str(self[k]))
        return ret

# vim: expandtab:shiftwidth=4:tabstop=4:softtabstop=4:textwidth=80
