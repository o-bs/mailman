# Copyright (C) 2014 by the Free Software Foundation, Inc.
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

"""Test the digest runner."""

__all__ = [
    'TestDigest',
    'TestI18nDigest',
    ]


import unittest

from email.iterators import _structure as structure
from email.mime.text import MIMEText
from io import StringIO
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.email.message import Message
from mailman.runners.digest import DigestRunner
from mailman.testing.helpers import (
    LogFileMark, digest_mbox, get_queue_messages, make_digest_messages,
    make_testable_runner, message_from_string,
    specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from string import Template



class TestDigest(unittest.TestCase):
    """Test the digest runner."""

    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._mlist.digest_size_threshold = 1
        self._digestq = config.switchboards['digest']
        self._shuntq = config.switchboards['shunt']
        self._virginq = config.switchboards['virgin']
        self._runner = make_testable_runner(DigestRunner, 'digest')
        self._process = config.handlers['to-digest'].process

    def _check_virgin_queue(self):
        # There should be two messages in the virgin queue: the digest as
        # plain-text and as multipart.
        messages = get_queue_messages('virgin')
        self.assertEqual(len(messages), 2)
        self.assertEqual(
            sorted(item.msg.get_content_type() for item in messages),
            ['multipart/mixed', 'text/plain'])
        for item in messages:
            self.assertEqual(item.msg['subject'],
                             'Test Digest, Vol 1, Issue 1')

    def test_simple_message(self):
        make_digest_messages(self._mlist)
        self._check_virgin_queue()

    def test_non_ascii_message(self):
        msg = Message()
        msg['From'] = 'anne@example.org'
        msg['To'] = 'test@example.com'
        msg['Content-Type'] = 'multipart/mixed'
        msg.attach(MIMEText('message with non-ascii chars: \xc3\xa9',
                            'plain', 'utf-8'))
        mbox = digest_mbox(self._mlist)
        mbox.add(msg.as_string())
        # Use any error logs as the error message if the test fails.
        error_log = LogFileMark('mailman.error')
        make_digest_messages(self._mlist, msg)
        # The runner will send the file to the shunt queue on exception.
        self.assertEqual(len(self._shuntq.files), 0, error_log.read())
        self._check_virgin_queue()

    def test_mime_digest_format(self):
        # Make sure that the format of the MIME digest is as expected.
        self._mlist.digest_size_threshold = 0.6
        self._mlist.volume = 1
        self._mlist.next_digest_number = 1
        self._mlist.send_welcome_message = False
        # Fill the digest.
        process = config.handlers['to-digest'].process
        size = 0
        for i in range(1, 5):
            text = Template("""\
From: aperson@example.com
To: xtest@example.com
Subject: Test message $i
List-Post: <test@example.com>

Here is message $i
""").substitute(i=i)
            msg = message_from_string(text)
            process(self._mlist, msg, {})
            size += len(text)
            if size >= self._mlist.digest_size_threshold * 1024:
                break
        # Run the digest runner to create the MIME and RFC 1153 digests.
        runner = make_testable_runner(DigestRunner)
        runner.run()
        items = get_queue_messages('virgin')
        self.assertEqual(len(items), 2)
        # Find the MIME one.
        mime_digest = None
        for item in items:
            if item.msg.is_multipart():
                assert mime_digest is None, 'We got two MIME digests'
                mime_digest = item.msg
        fp = StringIO()
        # Verify the structure is what we expect.
        structure(mime_digest, fp)
        self.assertMultiLineEqual(fp.getvalue(), """\
multipart/mixed
    text/plain
    text/plain
    message/rfc822
        text/plain
    message/rfc822
        text/plain
    message/rfc822
        text/plain
    message/rfc822
        text/plain
    text/plain
""")



class TestI18nDigest(unittest.TestCase):
    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        config.push('french', """
        [mailman]
        default_language: fr
        """)
        self.addCleanup(config.pop, 'french')
        self._mlist = create_list('test@example.com')
        self._mlist.preferred_language = 'fr'
        self._mlist.digest_size_threshold = 0
        self._process = config.handlers['to-digest'].process
        self._runner = make_testable_runner(DigestRunner)

    def test_multilingual_digest(self):
        # When messages come in with a content-type character set different
        # than that of the list's preferred language, recipients will get an
        # internationalized digest.
        msg = mfs("""\
From: aperson@example.org
To: test@example.com
Subject: =?iso-2022-jp?b?GyRCMGxIVhsoQg==?=
MIME-Version: 1.0
Content-Type: text/plain; charset=iso-2022-jp
Content-Transfer-Encoding: 7bit

\x1b$B0lHV\x1b(B
""")
        self._process(self._mlist, msg, {})
        self._runner.run()
        # There are two digests in the virgin queue; one is the MIME digest
        # and the other is the RFC 1153 digest.
        messages = get_queue_messages('virgin')
        self.assertEqual(len(messages), 2)
        if messages[0].msg.is_multipart():
            mime, rfc1153 = messages[0].msg, messages[1].msg
        else:
            rfc1153, mime = messages[0].msg, messages[1].msg
        # The MIME version contains a mix of French and Japanese.  The digest
        # chrome added by Mailman is in French.
        self.assertEqual(mime['subject'].encode(),
                         '=?iso-8859-1?q?Groupe_Test=2C_Vol_1=2C_Parution_1?=')
        self.assertEqual(str(mime['subject']),
                         'Groupe Test, Vol 1, Parution 1')
        # The first subpart contains the iso-8859-1 masthead.
        masthead = mime.get_payload(0).get_payload(decode=True).decode(
            'iso-8859-1')
        self.assertMultiLineEqual(masthead.splitlines()[0],
                                  'Envoyez vos messages pour la liste Test à')
        # The second subpart contains the utf-8 table of contents.
        self.assertEqual(mime.get_payload(1)['content-description'],
                         "Today's Topics (1 messages)")
        toc = mime.get_payload(1).get_payload(decode=True).decode('utf-8')
        self.assertMultiLineEqual(toc.splitlines()[0], 'Thèmes du jour :')
        # The third subpart contains the posted message in Japanese.
        self.assertEqual(mime.get_payload(2).get_content_type(),
                         'message/rfc822')
        post = mime.get_payload(2).get_payload(0)
        self.assertEqual(post['subject'], '=?iso-2022-jp?b?GyRCMGxIVhsoQg==?=')
        # Compare the bytes so that this module doesn't contain string
        # literals in multiple incompatible character sets.
        self.assertEqual(post.get_payload(decode=True), b'\x1b$B0lHV\x1b(B\n')
        # The RFC 1153 digest will have the same subject, but its payload will
        # be recast into utf-8.
        self.assertEqual(str(rfc1153['subject']),
                         'Groupe Test, Vol 1, Parution 1')
        self.assertEqual(rfc1153.get_charset(), 'utf-8')
        lines = rfc1153.get_payload(decode=True).decode('utf-8').splitlines()
        self.assertEqual(lines[0], 'Envoyez vos messages pour la liste Test à')
