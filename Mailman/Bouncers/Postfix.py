# Copyright (C) 1998,1999,2000,2001 by the Free Software Foundation, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software 
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

"""Parse bounce messages generated by Postfix.

This also matches something called `Keftamail' which looks just like Postfix
bounces with the word Postfix scratched out and the word `Keftamail' written
in in crayon.

It also matches something claiming to be `The BNS Postfix program'.
/Everybody's/ gotta be different, huh?

"""


import re
from Mailman.pythonlib.StringIO import StringIO



def flatten(msg, leaves):
    # give us all the leaf (non-multipart) subparts
    if msg.ismultipart():
        for part in msg.get_payload():
            flatten(part, leaves)
    else:
        leaves.append(msg)



# are these heuristics correct or guaranteed?
pcre = re.compile(r'\t\t\tthe\s*(bns)?\s*(postfix|keftamail)', re.IGNORECASE)
rcre = re.compile(r'failure reason:$', re.IGNORECASE)
acre = re.compile(r'<(?P<addr>[^>]*)>:')

def findaddr(msg):
    addrs = []
    body = StringIO(msg.get_payload())
    # simple state machine
    #     0 == nothing found
    #     1 == salutation found
    state = 0
    while 1:
        line = body.readline()
        if not line:
            break
        # preserve leading whitespace
        line = line.rstrip()
        # yes use match to match at beginning of string
        if state == 0 and (pcre.match(line) or rcre.match(line)):
            state = 1
        elif state == 1 and line:
            mo = acre.search(line)
            if mo:
                addrs.append(mo.group('addr'))
            # probably a continuation line
    return addrs



def process(msg):
    if msg.gettype() <> 'multipart/mixed':
        return None
    # We're looking for the plain/text subpart with a Content-Description: of
    # `notification'.
    leaves = []
    flatten(msg, leaves)
    for subpart in leaves:
        if subpart.gettype() == 'text/plain' and \
           subpart.get('content-description', '').lower() == 'notification':
            # then...
            return findaddr(subpart)
    return None
