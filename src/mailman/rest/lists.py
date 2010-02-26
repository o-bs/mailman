# Copyright (C) 2010 by the Free Software Foundation, Inc.
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

"""REST for mailing lists."""

from __future__ import absolute_import, unicode_literals

__metaclass__ = type
__all__ = [
    'AList',
    'AllLists',
    ]


from restish import http, resource
from zope.component import getUtility

from mailman.interfaces.domain import BadDomainSpecificationError
from mailman.interfaces.listmanager import (
    IListManager, ListAlreadyExistsError)
from mailman.interfaces.member import MemberRole
from mailman.rest.helpers import etag, path_to
from mailman.rest.members import AMember



def member_matcher(request, segments):
    """A matcher of member URLs inside mailing lists.

    e.g. /member/aperson@example.org
    """
    if len(segments) != 2:
        return None
    try:
        role = MemberRole[segments[0]]
    except ValueError:
        # Not a valid role.
        return None
    # No more segments.
    # XXX 2010-02-25 barry Matchers are undocumented in restish; they return a
    # 3-tuple of (match_args, match_kws, segments).
    return (), dict(role=role, address=segments[1]), ()

# XXX 2010-02-24 barry Seems like contrary to the documentation, matchers
# cannot be plain function, because matchers must have a .score attribute.
# OTOH, I think they support regexps, so that might be a better way to go.
member_matcher.score = ()



class _ListBase(resource.Resource):
    """Shared base class for mailing list representations."""

    def _list_data(self, mlist):
        """Return the list data for a single mailing list."""
        return dict(
            fqdn_listname=mlist.fqdn_listname,
            host_name=mlist.host_name,
            list_name=mlist.list_name,
            real_name=mlist.real_name,
            self_link=path_to('lists/{0}'.format(mlist.fqdn_listname)),
            )

    def _format_list(self, mlist):
        """Format the mailing list for a single mailing list."""
        return etag(self._list_data(mlist))


class AList(_ListBase):
    """A mailing list."""

    def __init__(self, list_name):
        self._mlist = getUtility(IListManager).get(list_name)

    @resource.GET()
    def mailing_list(self, request):
        """Return a single mailing list end-point."""
        if self._mlist is None:
            return http.not_found()
        return http.ok([], self._format_list(self._mlist))

    @resource.child(member_matcher)
    def member(self, request, segments, role, address):
        return AMember(self._mlist, role, address)


class AllLists(_ListBase):
    """The mailing lists."""

    @resource.POST()
    def create(self, request):
        """Create a new mailing list."""
        # XXX 2010-02-23 barry Sanity check the POST arguments by
        # introspection of the target method, or via descriptors.
        list_manager = getUtility(IListManager)
        try:
            # webob gives this to us as a string, but we need unicodes.
            kws = dict((key, unicode(value))
                       for key, value in request.POST.items())
            mlist = list_manager.new(**kws)
        except ListAlreadyExistsError:
            return http.bad_request([], b'Mailing list exists')
        except BadDomainSpecificationError as error:
            return http.bad_request([], b'Domain does not exist {0}'.format(
                error.domain))
        # wsgiref wants headers to be bytes, not unicodes.
        location = path_to('lists/{0}'.format(mlist.fqdn_listname))
        # Include no extra headers or body.
        return http.created(location, [], None)

    @resource.GET()
    def container(self, request):
        """Return the /lists end-point."""
        mlists = list(getUtility(IListManager))
        if len(mlists) == 0:
            resource = dict(start=None, total_size=0)
            return http.ok([], etag(resource))
        entries = [self._list_data(mlist) for mlist in mlists]
        # Tag the list entries, but use the dictionaries.
        [etag(data) for data in entries]
        resource = dict(
            start=0,
            total_size=len(mlists),
            entries=entries,
            )
        return http.ok([], etag(resource))
