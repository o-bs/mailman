# Copyright (C) 2012-2016 by the Free Software Foundation, Inc.
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

"""Test the high level list lifecycle API."""

import os
import shutil
import unittest

from mailman.app.lifecycle import create_list, remove_list
from mailman.interfaces.address import InvalidEmailAddressError
from mailman.interfaces.domain import BadDomainSpecificationError
from mailman.interfaces.listmanager import IListManager
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestLifecycle(unittest.TestCase):
    """Test the high level list lifecycle API."""

    layer = ConfigLayer

    def test_posting_address_validation(self):
        # Creating a mailing list with a bogus address raises an exception.
        self.assertRaises(InvalidEmailAddressError,
                          create_list, 'bogus address')

    def test_unregistered_domain(self):
        # Creating a list with an unregistered domain raises an exception.
        self.assertRaises(BadDomainSpecificationError,
                          create_list, 'test@nodomain.example.org')

    def test_remove_list_error(self):
        # An error occurs while deleting the list's data directory.
        mlist = create_list('test@example.com')
        os.chmod(mlist.data_path, 0)
        self.addCleanup(shutil.rmtree, mlist.data_path)
        self.assertRaises(OSError, remove_list, mlist)
        os.chmod(mlist.data_path, 0o777)

    def test_create_no_such_style(self):
        mlist = create_list('ant@example.com', style_name='bogus')
        # The MailmanList._preferred_language column isn't set so there's no
        # valid mapping to an ILanguage.  Therefore this call will produce a
        # KeyError.
        self.assertRaises(KeyError, getattr, mlist, 'preferred_language')

    def test_remove_list_without_data_path(self):
        mlist = create_list('ant@example.com')
        shutil.rmtree(mlist.data_path)
        remove_list(mlist)
        self.assertIsNone(getUtility(IListManager).get('ant@example.com'))
