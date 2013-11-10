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
import shutil
import subprocess
import datetime

import mutag.plistseq as plistseq
from mutag.message import Message
import mutag.archui as ui

class MutagError(Exception):
    def __init__(self, msg=None):
        super(MutagError, self).__init__(msg)

class MuError(MutagError):
    def __init__(self, msg=None):
        super(MuError, self).__init__(msg)


class Mutag(object):
    def __init__(self, prof):
        self.muhome = prof['muhome']
        self.maildir = prof['maildir']

        self.trash_tag = prof['trashtag'].strip()
        if len(self.trash_tag) == 0: self.trash_tag = None

        self.trash_path = os.path.join(self.maildir, prof['trashfolder'])
        self.gmail_folders = prof['gmailfolders']

        self.expire_days = prof['expiredays']

        self.tagrules_path = prof['tagrules']
        self.lastmtime_path = prof['lastmtime']
        self.mtimelist_path = prof['mtimelist']



    # Auxiliar functions
    # ----------------------------------------------

    def _mu(self, cmd, args, catchout=False, silent=False):
        mu_cmd = 'mu'
        with open('/dev/null', 'w') as devnull:
            if silent: out = devnull
            else:      out = None

            cmd_args = [mu_cmd, cmd, '--muhome', self.muhome] + args

            if catchout:
                ret = subprocess.check_output(cmd_args, stderr=subprocess.STDOUT)
                return ret.decode('utf-8')
            else:
                subprocess.check_call(cmd_args, stdout=out, stderr=out)



    def _git(self, args, tgtdir=None, catchout=False, silent=False):
        git_cmd = 'git'
        with open('/dev/null', 'w') as devnull:
            if silent: out = devnull
            else:      out = None

            cmd_args = [git_cmd] + args

            if catchout:
                ret = subprocess.check_output(cmd_args, stderr=subprocess.STDOUT, cwd=tgtdir)
                return ret.decode('utf-8')
            else:
                subprocess.check_call(cmd_args, stdout=out, stderr=out, cwd=tgtdir)



    def _parse_msgsexp(self, sexpstr):
        data = plistseq.parse(sexpstr)
        L = []
        for d in data:
            msg = Message()
            msg.from_mudict(d)
            L.append(msg)
        return L


    def _print_tagschange(self, msg, oldtags, newtags):
        alltags = oldtags.union(newtags)
        L = []
        for t in sorted(alltags):
            if t in oldtags and t in newtags:       L.append('#Y%s' % t)
            elif t in oldtags and not t in newtags: L.append('#R-%s' % t)
            elif not t in oldtags and t in newtags: L.append('#G+%s' % t)
        tagch = '#W, '.join(L)
        ui.print_color('#C{0} #W[{1}#W]'.format(msg['subject'], tagch))


    def _print_expired(self, msg):
        ui.print_color('expired: %s' % msg.tostring('compact'))


    def _load_tagrules(self):
        try:
            fd = open(self.tagrules_path, 'r')
            rawcode = fd.read()
        except:
            ui.print_error("Can't open tagrules at %s" % self.tagrules_path)
            return

        try:
            rules = imp.new_module('tagrules')
            exec(rawcode, rules.__dict__)
            return rules.TagRules(path=self.maildir)
        except Exception as err:
            ui.print_error("Exception loading tagrules %s\n%s" % (self.tagrules_path, str(err)))
            return



    # Maildir handling
    # ----------------------------------------------

    def should_ignore_path(self, path):
        return any([os.path.exists(os.path.join(path, ".noindex")),
                   os.path.exists(os.path.join(path, ".notag"))])


    def _get_maildir_files_rec(self, files, path):
        for fd in os.listdir(path):
            newpath = os.path.join(path, fd)
            if os.path.isdir(newpath) and not self.should_ignore_path(newpath):
                self._get_maildir_files_rec(files, newpath)
            elif os.path.isfile(newpath) and fd[0] != '.':
                files.append(newpath)


    def get_maildir_files(self):
        files = []
        self._get_maildir_files_rec(files, self.maildir)
        return files


    def get_last_mtime(self):
        try:
            with open(self.lastmtime_path, 'r') as fd:
                mtime = int(fd.read())
        except OSError:
            mtime = 0
        return mtime



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


    def move_to_maildir(self, msg, tgt):
        path = msg['path']

        rem, base = os.path.split(path)
        rem, sub = os.path.split(rem)

        newpath = os.path.join(tgt, sub, base)
        if path and os.path.exists(path):
            shutil.move(path, newpath)
            msg['path'] = newpath


    def trash(self, msg):
        """Trash a message. Moves to trash. On gmail folders only marks it as
           trash. Next sync will take care of removing it. Otherwise, if I remove
           it from 'All Mail' next sync puts back the message before it realizes
           it was trashed!
        """
        if os.path.exists(msg['path']):
            # tag as trashed
            if self.trash_tag: msg.set_tags([self.trash_tag])
            else:              msg.set_tags(['\\Trash'])

            # set maildir flags
            msg.set_flags(['trashed', 'seen'])

            # make hard link in trash
            os.link(msg['path'], os.path.join(self.trash_path, 'cur', os.path.basename(msg['path'])))

            # remove from original folder only if it is not a gmail folder
            if not re.sub('^/', '', msg['maildir']) in self.gmail_folders:
                os.unlink(msg['path'])


    # Mu database
    # ----------------------------------------------

    def query_mu(self, query=None, mtime=None, related=False):
        args = ['--threads', '--format=sexp']

        if related: args.append('--include-related')
        if mtime:   args.append('--after=%d' % int(mtime))
        if query:   args.extend(shlex.split(query))
        else:       args.append("")

        # parse sexp
        try:
            sexpdata = self._mu('find', args, silent=True, catchout=True)
            L = self._parse_msgsexp(sexpdata)
            return L

        except subprocess.CalledProcessError as err:
            if err.returncode == 4:  return []  # no results
            elif err.output:         raise MuError(str(err.output.decode('utf-8')))
            else:                    raise MuError(str(err))


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
            node.data = {'emails': set(), 'tags': set()}

            if node.value:
                node.data['emails'].update(node.value['emails'])
                node.data['tags'].update(node.value['tags'])

            if node.child:
                for child in node.child.values():
                    _collect_thread_data_rec(child, root)
                    node.data['emails'].update(child.data['emails'])
                    node.data['tags'].update(child.data['tags'])



        # Recursively update msg objects
        def _collect_thread_update_msg_rec(node):
            if node.root != None and node.value != None:
                node.value['thread-emails'] = set(node.root.data['emails'])
                node.value['thread-tags']   = set(node.root.data['tags'])
                node.value['thread-root']   = str(node.root.value['message-id'])

            if node.child:
                for child in node.child.values():
                    _collect_thread_update_msg_rec(child)

        _collect_thread_data_rec(threads, None)
        _collect_thread_update_msg_rec(threads)





    # Interface
    # ----------------------------------------------

    def query(self, query=None, path=None, modified_only=False, related=False):

        if path:
            L = self.parsefiles([path])
        else:
            if modified_only: mtime = self.get_last_mtime()
            else:             mtime = None

            L = self.query_mu(query, mtime, related=related)

            # Fills in thread related data
            self.collect_thread_data(L)
        return L



    def count(self, query, modified_only=False):
        if modified_only: mtime = self.get_last_mtime()
        else:             mtime = None

        try:
            return len(self.query_mu(query, mtime, related=False))

        except MuError:
            return 0



    def change_tags(self, msglist, tagactions, dryrun=False, silent=False):
        addtags = set()
        deltags = set()
        for ta in tagactions:
            mdel = re.search('^\s*-(.*)\s*$', ta)
            madd = re.search('^\s*\+(.*)\s*$', ta)

            if mdel:   deltags.add(mdel.group(1))
            elif madd: addtags.add(madd.group(1))
            else:      addtags.add(ta.strip())

        for msg in msglist:
            tags = set(msg['tags'])
            newtags = tags.union(addtags).difference(deltags)
            if tags != newtags:
                if not silent: self._print_tagschange(msg, tags, newtags)
                if not dryrun: msg.set_tags(newtags)



    def change_flags(self, msglist, flagactions, dryrun=False, silent=False):
        addflags = set()
        delflags = set()
        for fa in flagactions:
            mdel = re.search('^\s*-(.*)\s*$', fa)
            madd = re.search('^\s*\+(.*)\s*$', fa)

            if mdel:   delflags.add(mdel.group(1))
            elif madd: addflags.add(madd.group(1))
            else:      addflags.add(fa.strip())

        for msg in msglist:
            flags = set(msg['flags'])
            newflags = flags.union(addflags).difference(delflags)
            if flags != newflags:
                if not silent: self._print_tagschange(msg, flags, newflags)
                if not dryrun: msg.set_flags(newflags)



    def autotag(self, query, path=None, modified_only=True, related=True, dryrun=False, silent=False):
        if not silent: ui.print_color("Autotaging new messages under #B%s#t" % self.maildir)
        if not silent: ui.print_color("  retrieving messages")
        msglist = self.query(query, path=path, modified_only=modified_only, related=related)

        if not silent: ui.print_color("  retagging messages")
        tr = self._load_tagrules()
        tagged_count = 0
        for msg in msglist:
            if self.should_ignore_path(os.path.join(self.maildir, re.sub('^/', '', msg['maildir']))):
                continue

            tags = set(msg['tags'])

            if self.trash_tag in tags or 'trashed' in msg['flags']  or 'deleted' in msg['flags']:
                continue

            newtags = tr.get_tags(msg)
            ui.print_debug("%s -> %s" % (', '.join(tags), ', '.join(newtags)))
            if tags != newtags:
                tagged_count = tagged_count + 1
                if not silent: self._print_tagschange(msg, tags, newtags)
                if not dryrun: msg.set_tags(newtags)

        if not silent:
            ui.print_color("Processed #G%d#t files, and retagged #G%d#t." % (len(msglist), tagged_count))



    def expire(self, dryrun=False, silent=False):
        """Marks all messages that need expiring as trashed"""
        ui.print_color("Expiring old messages under #B%s#t" % self.maildir)
        tr = self._load_tagrules()
        expire_date = datetime.datetime.today() - datetime.timedelta(days=self.expire_days)

        expired_count = 0
        msglist = self.query(query=tr.expire_query(expire_date), related=True)
        for msg in msglist:
            if self.should_ignore_path(os.path.join(self.maildir, re.sub('^/', '', msg['maildir']))):
                continue

            if not self.trash_tag in msg['tags'] and msg['date'] and msg['date'] < expire_date:
                if tr.expire(msg):
                    if not silent: self._print_expired(msg)
                    expired_count = expired_count + 1
                    if not dryrun: self.trash(msg)
                else:
                    tags = msg['tags']
                    if not dryrun: msg.set_tags(tags | set([tr.noexpire_tag]))

        if not silent:
            ui.print_color("Processed #G%d#t files, and expired #G%d#t." % (len(msglist), expired_count))



    def index(self, dryrun=False, silent=False):
        args = ['--maildir', self.maildir, '--autoupgrade']
        if silent: args.append('--quiet')
        if not silent: ui.print_color("  indexing new messages")
        try:
            if not dryrun: self._mu('index', args, catchout=True)

        except subprocess.CalledProcessError as err:
            if err.output:  raise MuError(str(err.output.decode('utf-8')))
            else:           raise MuError(str(err))



    def rebuild(self, dryrun=False, silent=False):
        args = ['--rebuild', '--maildir', self.maildir, '--autoupgrade']
        if silent: args.append('--quiet')
        try:
            if not dryrun: self._mu('index', args, catchout=False)

        except subprocess.CalledProcessError as err:
            if err.output:  raise MuError(str(err.output.decode('utf-8')))
            else:           raise MuError(str(err))



    def empty_trash(self, dryrun=False, silent=False):
        for f in glob.glob(os.path.join(self.trash_path, '*', '*')):
            if not silent: ui.print_color("deleting: %s" % f)
            if not dryrun: os.remove(f)



    def update_mtime(self, dryrun=False, silent=False):
        if not silent: ui.print_color("  updating last mtime")
        L = self.get_maildir_files()
        if len(L) > 0:
            mtime = max([int(os.stat(mp).st_mtime) for mp in L])
            if not dryrun:
                with open(self.lastmtime_path, 'w') as fd:
                    fd.write(str(mtime))



    def save_mtimes(self, dryrun=False, silent=False):
        if not silent: ui.print_color("  updating mtime list")
        L = self.get_maildir_files()
        if len(L) > 0:
            with open(self.mtimelist_path, 'w') as fd:
                maxmt = 0
                for mp in sorted(L):
                    mt = os.stat(mp).st_mtime
                    if mt > maxmt: maxmt = mt
                    fd.write("%f: %s\n" % (mt, os.path.relpath(mp, self.maildir)))
                fd.flush()
                fd.close()

            with open(self.lastmtime_path, 'w') as fd:
                fd.write(str(int(maxmt)))
                fd.flush()
                fd.close()



    def recover_mtimes(self, dryrun=False, silent=False):
        if not silent: ui.print_color("  recovering file mtimes")
        line_re = re.compile("^([0-9.]+):\s*(.*)$")

        with open(self.mtimelist_path, 'r') as fd:
            for line in fd:
                m = line_re.match(line)
                mt = float(m.group(1))
                path = os.path.join(self.maildir, m.group(2))

                if os.path.exists(path):
                    cmt = os.stat(path).st_mtime
                    if cmt != mt:
                        ui.print_debug("set mtime %f. %s" % (mt, m.group(2)))
                        if not dryrun: os.utime(path, (mt, mt))



    def commit(self, dryrun=False, silent=False):
        cmt_msg = "mutag auto-commit"

        if not dryrun and os.path.exists(os.path.join(self.maildir, '.git')):
            try:
                # detect if there are changes on working dir
                raw = self._git(['status', '--porcelain'], tgtdir=self.maildir,
                                catchout=True, silent=True)

                # commit only if there are changes
                if len(raw.strip()) > 0:
                    if not silent: ui.print_color("  commiting files in %s" % self.maildir)
                    self._git(['add', '-A', '.'], tgtdir=self.maildir, catchout=False, silent=True)
                    self._git(['commit', '-m', cmt_msg], tgtdir=self.maildir, catchout=False, silent=True)

                else:
                    if not silent: ui.print_color("  working dir is clean")

            except subprocess.CalledProcessError as err:
                if err.output:  raise MuError(str(err.output.decode('utf-8')))
                else:           raise MuError(str(err))


# vim: expandtab:shiftwidth=4:tabstop=4:softtabstop=4:textwidth=80
