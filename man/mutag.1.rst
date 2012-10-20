====
paur
====

--------------------------------------------------------------
a uniform interface to pacman, AUR and local user repositories
--------------------------------------------------------------

:Author: Abdó Roig-Maranges<abdo.roig@gmail.com>
:Date: VERSION
:Manual section: 1

SYNOPOSIS
=========
| paur [COMMAND] [OPTION] TARGETS...

DESCRIPTION
===========
paur is an interface to pacman, AUR, and local user package repositories,
written in python. paur stands for Pacman, Aur and User as uniform Repositories.

HOW IT WORKS
============
paur recognizes three sources of packages:
1. User: PKGBUILD's stored in a local directory.
2. Arch repositories: as configured in /etc/pacman.conf
3. AUR: obtained via the AUR http API.

The repositories have an intrinsic priority order. By default the priorities go
as listed above. That is, if the same package appears in a User repository, and
in Arch, the User one is chosen. This priority order may be overriden with the
configuration variable repoorder.

As a general rule, it is preferable to keep packages in User with a unique name,
just to avoid confusion. However, let's say I mantain a package bla-git in
AUR. Then it makes sense to keep the development of bla-git in User with the
same name, an even use paur to upload the PKGBUILD to AUR.


COMMANDS
========

-S, --sync
  Synchronize packages with remote repositories

-Q, --query
  Query local database

-U, --upgrade
  Upgrade a package from a file

-R, --remove
  Remove packages from system

-P, --push
  Push a source tarball to AUR

-V, --version
  Print version and exit

SYNC OPTIONS -S
===============

-s, --search
  Search in the remote packages matching the regular expression TARGET

-u, --sysupgrade
  Perform a system upgrade

-i, --info
  Print information from given TARGETS

-t, --deptree
  Print a dependency tree for given TARGETS

-o, --owns
  Print a list of packages owning the given files as TARGETS

-l, --list

-a, --allpkg

-c, --check

-f, --full
  When added to -s perfors a full search (matching on name or description)

-p, --pkgbuild


QUERY OPTIONS -Q
================

-s, --search
  Search in the remote packages matching the regular expression TARGET

-u, --sysupgrade
  Perform a system upgrade

-i, --info
  Print information from given TARGETS

-t, --deptree
  Print a dependency tree for given TARGETS

-o, --owns
  Print a list of packages owning the given files as TARGETS

-l, --list

-a, --allpkg

-c, --check

-f, --full
  When added to -s perfors a full search (matching on name or description)

-p, --pkgbuild


UPGRADE OPTIONS -U
==================

-s, --search
  Search in the remote packages matching the regular expression TARGET

-u, --sysupgrade
  Perform a system upgrade

-i, --info
  Print information from given TARGETS

-t, --deptree
  Print a dependency tree for given TARGETS

-o, --owns
  Print a list of packages owning the given files as TARGETS

-l, --list

-a, --allpkg

-c, --check

-f, --full
  When added to -s perfors a full search (matching on name or description)

REMOVE OPTIONS -R
=================

-s, --search
  Search in the remote packages matching the regular expression TARGET

-u, --sysupgrade
  Perform a system upgrade

-i, --info
  Print information from given TARGETS

-t, --deptree
  Print a dependency tree for given TARGETS

-o, --owns
  Print a list of packages owning the given files as TARGETS

-l, --list

-a, --allpkg

-c, --check

-f, --full
  When added to -s perfors a full search (matching on name or description)

PUSH OPTIONS -P
===============



COMMON OPTIONS
==============

-y, --refresh
  Refresh arch databases and update version in PKGBUILD's for the development
  packages in the user repositories

-z, --fetch-dev
  Fetches sources for installed development packages

-b, --build


--aur
  Restrict to packages from AUR

--arch
  Restrict to packages from Arch repositories

--user
  Restrict to packages from user repositories

--debug
  Prints debugging information

CONFIGURATION
=============
There is a system-wide configuration file /etc/paur.conf and a user specific
configuration file in $XDG_CONFIG/paur/config.

KNOWN BUGS
==========


SEE ALSO
========
pacman(1) makepkg(1) abs(1) paur.conf(5)
