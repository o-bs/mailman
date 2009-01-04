# Copyright (C) 1998-2009 by the Free Software Foundation, Inc.
#
# This file is part of GNU Mailman.
#
# GNU Mailman is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# GNU Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# GNU Mailman.  If not, see <http://www.gnu.org/licenses/>.

"""Extend mailbox.UnixMailbox.
"""

import sys
import email
import mailbox

from email.Errors import MessageParseError
from email.Generator import Generator
from email.Parser import Parser

from mailman import Defaults
from mailman.Message import Message



def _safeparser(fp):
    try:
        return email.message_from_file(fp, Message)
    except MessageParseError:
        # Don't return None since that will stop a mailbox iterator
        return ''



class Mailbox(mailbox.PortableUnixMailbox):
    def __init__(self, fp):
        mailbox.PortableUnixMailbox.__init__(self, fp, _safeparser)

    # msg should be an rfc822 message or a subclass.
    def AppendMessage(self, msg):
        # Check the last character of the file and write a newline if it isn't
        # a newline (but not at the beginning of an empty file).
        try:
            self.fp.seek(-1, 2)
        except IOError, e:
            # Assume the file is empty.  We can't portably test the error code
            # returned, since it differs per platform.
            pass
        else:
            if self.fp.read(1) <> '\n':
                self.fp.write('\n')
        # Seek to the last char of the mailbox
        self.fp.seek(1, 2)
        # Create a Generator instance to write the message to the file
        g = Generator(self.fp)
        g.flatten(msg, unixfrom=True)
        # Add one more trailing newline for separation with the next message
        # to be appended to the mbox.
        print >> self.fp



# This stuff is used by pipermail.py:processUnixMailbox().  It provides an
# opportunity for the built-in archiver to scrub archived messages of nasty
# things like attachments and such...
def _archfactory(mailbox):
    # The factory gets a file object, but it also needs to have a MailList
    # object, so the clearest <wink> way to do this is to build a factory
    # function that has a reference to the mailbox object, which in turn holds
    # a reference to the mailing list.  Nested scopes would help here, BTW,
    # but we can't rely on them being around (e.g. Python 2.0).
    def scrubber(fp, mailbox=mailbox):
        msg = _safeparser(fp)
        if msg == '':
            return msg
        return mailbox.scrub(msg)
    return scrubber


class ArchiverMailbox(Mailbox):
    # This is a derived class which is instantiated with a reference to the
    # MailList object.  It is build such that the factory calls back into its
    # scrub() method, giving the scrubber module a chance to do its thing
    # before the message is archived.
    def __init__(self, fp, mlist):
        scrubber_module = Defaults.ARCHIVE_SCRUBBER
        if scrubber_module:
            __import__(scrubber_module)
            self._scrubber = sys.modules[scrubber_module].process
        else:
            self._scrubber = None
        self._mlist = mlist
        mailbox.PortableUnixMailbox.__init__(self, fp, _archfactory(self))

    def scrub(self, msg):
        if self._scrubber:
            return self._scrubber(self._mlist, msg)
        else:
            return msg