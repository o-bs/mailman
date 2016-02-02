# Copyright (C) 2016 by the Free Software Foundation, Inc.
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

"""REST API for a mailing list's header matches."""

__all__ = [
    'HeaderMatch',
    'HeaderMatches',
    ]


from mailman.interfaces.action import Action
from mailman.interfaces.mailinglist import IHeaderMatchList
from mailman.rest.helpers import (
    CollectionMixin, GetterSetter, bad_request, child, created, etag,
    no_content, not_found, okay)
from mailman.rest.validator import Validator, enum_validator


def lowercase(value):
    return str(value).lower()


class _HeaderMatchBase:
    """Common base class."""

    def __init__(self, mlist):
        self._mlist = mlist
        self.header_matches = IHeaderMatchList(self._mlist)

    def _location(self, index):
        return self.api.path_to('lists/{}/header-matches/{}'.format(self._mlist.list_id, index))

    def _resource_as_dict(self, header_match):
        """See `CollectionMixin`."""
        resource = dict(
            index=header_match.index,
            header=header_match.header,
            pattern=header_match.pattern,
            self_link=self._location(header_match.index),
            )
        if header_match.action is not None:
            resource['action'] = header_match.action
        return resource


class HeaderMatch(_HeaderMatchBase):
    """A header match."""

    def __init__(self, mlist, index):
        super().__init__(mlist)
        self._index = index

    def on_get(self, request, response):
        """Get a header match."""
        try:
            header_match = self.header_matches[self._index]
        except IndexError:
            not_found(response, 'No header match at this index: {}'.format(
                      self._index))
        else:
            okay(response, etag(self._resource_as_dict(header_match)))

    def on_delete(self, request, response):
        """Remove a header match."""
        try:
            del self.header_matches[self._index]
        except IndexError:
            not_found(response, 'No header match at this index: {}'.format(
                      self._index))
        else:
            no_content(response)

    def patch_put(self, request, response, is_optional):
        """Update the header match."""
        try:
            header_match = self.header_matches[self._index]
        except IndexError:
            not_found(response, 'No header match at this index: {}'.format(
                      self._index))
            return
        kws = dict(
            header=GetterSetter(lowercase),
            pattern=GetterSetter(str),
            index=GetterSetter(int),
            action=GetterSetter(enum_validator(Action)),
            )
        if is_optional:
            # For a PATCH, all attributes are optional.
            kws['_optional'] = kws.keys()
        else:
            # For a PUT, index can remain unchanged and action can be None.
            kws['_optional'] = ('action', 'index')
        try:
            Validator(**kws).update(header_match, request)
        except ValueError as error:
            bad_request(response, str(error))
            return
        else:
            no_content(response)

    def on_put(self, request, response):
        """Full update of the header match."""
        self.patch_put(request, response, is_optional=False)

    def on_patch(self, request, response):
        """Partial update of the header match."""
        self.patch_put(request, response, is_optional=True)


class HeaderMatches(_HeaderMatchBase, CollectionMixin):
    """The list of all header matches."""

    def _get_collection(self, request):
        """See `CollectionMixin`."""
        return list(self.header_matches)

    def on_get(self, request, response):
        """/header-matches"""
        resource = self._make_collection(request)
        okay(response, etag(resource))

    def on_post(self, request, response):
        """Add a header match."""
        validator = Validator(
            header=str,
            pattern=str,
            action=enum_validator(Action),
            _optional=('action',)
            )
        try:
            arguments = validator(request)
        except ValueError as error:
            bad_request(response, str(error))
            return
        try:
            self.header_matches.append(**arguments)
        except ValueError:
            bad_request(response, b'This header match already exists')
        else:
            header_match = self.header_matches[-1]
            created(response, self._location(header_match.index))

    def on_delete(self, request, response):
        """Delete all header matches for this mailing list."""
        self.header_matches.clear()
        no_content(response)

    @child(r'^(?P<index>\d+)')
    def header_match(self, request, segments, **kw):
        return HeaderMatch(self._mlist, int(kw['index']))