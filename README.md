mutag
=====

A script to manipulate tags on the email messages in a maildir. It depends on
[mu](http://www.djcbsoftware.nl/code/mu/), that is used for email index and querying.

The tags are stored in a special header 'X-Keywords'. This header can be synced to gmail
labels using a properly configured [offlineimap](http://offlineimap.org/) since version
6.5.6

**NOTE**: Use this software at your own risk. This is a "works for me" kind of software,
That I made public in case anyone is interested, but is not thorougly tested, and may lead
to data loss. Also, there is no documentation for now.
