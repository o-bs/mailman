# Copyright (C) 1998,1999,2000 by the Free Software Foundation, Inc.
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


"""Routines for presentation of list-specific HTML text."""


import os
# XXX: should be converted to use re module
import regsub 
import string
import mm_cfg
import Utils
from htmlformat import *



class HTMLFormatter:
    def InitVars(self):
        if self.internal_name():
            self._template_dir = os.path.join(mm_cfg.LIST_DATA_DIR,
                                              self._internal_name)
        else:
            self._template_dir = mm_cfg.TEMPLATE_DIR

    def GetMailmanFooter(self):
	owners_html = Container()
	for i in range(len(self.owner)):
	    owner = self.owner[i]
	    owners_html.AddItem(Link('mailto:%s' % owner, owner))
	    if i + 1 <> len(self.owner):
		owners_html.AddItem(', ')

	# Remove the .Format() when htmlformat conversion is done.
	return Container(
	    '<hr>',
	    Address(
		Container( 
                    Link(self.GetScriptURL('listinfo'), self.real_name),
		    _(' list run by '), owners_html,
		    '<br>',
                    Link(self.GetScriptURL('admin'),
                         _('%s administrative interface') % self.real_name),
                    ' (requires authorization)',
                    '<p>', MailmanLogo()))).Format()

    def SnarfHTMLTemplate(self, file, lang=None):
        # XXX: hack, blech, yuk
        if lang is None:
            lang = self.preferred_language
        HTMLFormatter.InitVars(self)
	filename = os.path.join(self._template_dir, lang, file)
	f = open(filename,'r')
	str = f.read()
	f.close()
	return str

    def FormatUsers(self, digest, lang=None):
        if lang is None:
            lang = self.preferred_language
        conceal_sub = mm_cfg.ConcealSubscription
        people = []
	if digest:
            digestmembers = self.GetDigestMembers()
            for dm in digestmembers:
                if not self.GetUserOption(dm, conceal_sub):
                    people.append(dm)
            num_concealed = len(digestmembers) - len(people)
	else:
            members = self.GetMembers()
            for m in members:
                if not self.GetUserOption(m, conceal_sub):
                    people.append(m)
	    num_concealed = len(members) - len(people)
        people.sort()
	if (num_concealed > 0):
	    plurality = (((num_concealed > 1) and "s") or "")
	    concealed = (_("<em>(%d private member%s not shown)</em>")
			 % (num_concealed, plurality))
 	else:
 	    concealed = ""
        ObscureEmail = Utils.ObscureEmail
        options_url = self.GetScriptURL('options')
        disdel = mm_cfg.DisableDelivery
        items = []
        for person in people:
            id = ObscureEmail(person)
            if self.obscure_addresses:
                showing = ObscureEmail(person, for_text=1)
            else:
                showing = person
            url = "%s/%s" % (options_url, id)
            got = Link(url, showing)
            if self.GetUserOption(person, disdel):
                got = Italic("(", got, ")")
            items.append(got)
	# Just return the .Format() so this works until I finish
	# converting everything to htmlformat...
	return (concealed +
		apply(UnorderedList, tuple(items)).Format())


    def FormatOptionButton(self, type, value, user):
	users_val = self.GetUserOption(user, type)
	if users_val == value:
	    checked = ' CHECKED'
	else:
	    checked = ''
	name = {mm_cfg.DontReceiveOwnPosts : "dontreceive",
                mm_cfg.DisableDelivery     : "disablemail",
                mm_cfg.DisableMime         : "mime",
                mm_cfg.AcknowledgePosts    : "ackposts",
                mm_cfg.Digests             : "digest",
                mm_cfg.ConcealSubscription : "conceal"
                }[type]
	import sys
	return ('<input type=radio name="%s" value="%d"%s>'
		% (name, value, checked))

    def FormatDigestButton(self):
	if self.digest_is_default:
	    checked = ' CHECKED'
	else:
	    checked = ''
	return '<input type=radio name="digest" value="1"%s>' % checked

    def FormatDisabledNotice(self, user):
	if self.GetUserOption(user, mm_cfg.DisableDelivery):
	    text = Center(Header(3, _(
                "Note - your list delivery is currently disabled."))).Format()
	    text = text + "\n"
	    text = text + _("You may have set non-delivery deliberately, or"
                            " it may have been triggered by bounces from your"
                            " delivery address.  In either case, to reenable "
                            " delivery, change the ")
	    text = text + Link('#disable',
			       _("Disable mail delivery")).Format()
	    text = text + _(" option.  Contact ")
	    text = text + Link('mailto:' + self.GetAdminEmail(),
			       _("your list administrator")).Format()
	    text = text + _(" if you have questions.")
	    return text
	else:
	    return ""

    def FormatUmbrellaNotice(self, user, type):
        if self.umbrella_list:
	    return _("(Note - you are subscribing to a list of mailing lists,"
                     " so the %s notice will be sent to the admin address"
                     " for your membership, %s.)<p>") % (
                type, self.GetMemberAdminEmail(user))
	else:
	    return ""

    def FormatSubscriptionMsg(self):
        "Tailor to approval, roster privacy, and web vetting requirements."
        msg = ""
        also = ""
        if self.subscribe_policy == 1:
            msg = msg + _("You will be sent email requesting confirmation, "
                          "to prevent others from gratuitously subscribing "
                          "you.  ")
        if self.subscribe_policy == 2:
            msg = msg + _("This is a closed list, which means your "
                          "subscription will be held for approval.  You will "
                          "be notified of the administrator's decision by "
                          "email.  ")
            also = _("also ")
        if self.subscribe_policy == 3:
            msg = msg + _("You will be sent email requesting confirmation, "
                          "to prevent others from gratuitously subscribing "
                          "you.  Once confirmation is received, your "
                          "request will be held for approval by the list "
                          "administrator.  You will be notified of the "
                          "administrator's decision by email.  ")
            also = _("also ")
        if self.private_roster == 1:
            msg = msg + _("This is %sa private list, which means that "
                          "the members list is not available to non-"
                          "members.  ") % also
        elif self.private_roster:
            msg = msg + _("This is %sa hidden list, which means that "
                          "the members list is available only to the "
                          "list administrator.  ") % also
        else:
            msg = msg + _("This is %sa public list, which means that the "
                          "members list is openly available") % also
            if self.obscure_addresses:
                msg = msg + _(" (but we obscure the addresses so they are "
                              "not easily recognizable by spammers).  ")
            else:
                msg = msg + ".  "

        if self.umbrella_list:
            msg = msg + _("<p>(Note that this is an umbrella list, intended to"
                          " have only other mailing lists as members.  Among"
                          " other things, this means that your confirmation"
                          " request will be sent to the '%s' account for"
                          " your address.)") % self.umbrella_member_suffix

        return msg

    def FormatUndigestButton(self):
	if self.digest_is_default:
	    checked = ''
	else:
	    checked = ' CHECKED'
	return '<input type=radio name="digest" value="0"%s>' % checked

    def FormatMimeDigestsButton(self):
	if self.mime_is_default_digest:
	    checked = ' CHECKED'
	else:
	    checked = ''
	return '<input type=radio name="mime" value="1"%s>' % checked
    def FormatPlainDigestsButton(self):
	if self.mime_is_default_digest:
	    checked = ''
	else:
	    checked = ' CHECKED'
	return '<input type=radio name="plain" value="1"%s>' % checked

    def FormatEditingOption(self, lang):
        "Present editing options, according to list privacy."

        text = (_('To change your subscription (set options like digest'
                  ' and delivery modes, get a reminder of your password,'
                  ' or unsubscribe from ')
                + self.real_name
                + _('), %senter your subscription email address:')
                + '<p><center> ')

        if self.private_roster == 0:
            text = text % _("<b><i> either</i></b> ")
        else:
            text = text % ""
        text = (text
                + TextBox('info', size=30).Format()
                + "  "
                + SubmitButton('UserOptions', _('Edit Options')).Format()
                + "</center>")
        if self.private_roster == 0:
            text = text + _("<p>... <b><i>or</i></b> select your entry from "
                             " the subscribers list (see above).")
        return text
        
    def RestrictedListMessage(self, which, restriction):
        if not restriction:
            return ""
        elif restriction == 1:
            return (_("<i>The %s is only available to the list members.</i>)")
                    % which)
        else:
            return (_("<i>The %s is only available to the list"
                      " administrator.</i>") % which)

    def FormatRosterOptionForUser(self, lang):
        return self.RosterOption(lang).Format()

    def RosterOption(self, lang):
        "Provide avenue to subscribers roster, contingent to .private_roster."
        container = Container()
        if not self.private_roster:
            container.AddItem(_("Click here for the list of ")
                              + self.real_name
                              + _(" subscribers: "))
            container.AddItem(SubmitButton('SubscriberRoster',
					   _("Visit Subscriber list")))
        else:
            if self.private_roster == 1:
                only = _('members')
                whom = _('Address:')
            else:
                only = _('the list administrator')
                whom = _('Admin address:')
            # Solicit the user and password.
            container.AddItem(self.RestrictedListMessage(_('subscribers list'),
                                                         self.private_roster)
                              + _(" <p>Enter your ")
                              + string.lower(whom[:-1])
                              + _(" and password to visit"
                              "  the subscribers list: <p><center> ")
                              + whom
                              + " ")
            container.AddItem(self.FormatBox('roster-email'))
            container.AddItem(_("Password: ")
                              + self.FormatSecureBox('roster-pw')
                              + "&nbsp;&nbsp;")
            container.AddItem(SubmitButton('SubscriberRoster',
					   _('Visit Subscriber List')))
            container.AddItem("</center>")
        return container

    def FormatFormStart(self, name, extra=''):
	base_url = self.GetScriptURL(name)
        if extra:
            full_url = "%s/%s" % (base_url, extra)
        else:
            full_url = base_url
	return ('<FORM Method=POST ACTION="%s">' % full_url)

    def FormatArchiveAnchor(self):
	return '<a href="%s">' % self.GetBaseArchiveURL()

    def FormatFormEnd(self):
	return '</FORM>'

    def FormatBox(self, name, size=20):
	return '<INPUT type="Text" name="%s" size="%d">' % (name, size)

    def FormatSecureBox(self, name):
	return '<INPUT type="Password" name="%s" size="15">' % name

    def FormatButton(self, name, text='Submit'):
	return '<INPUT type="Submit" name="%s" value="%s">' % (name, text)

    def FormatReminder(self, lang):
	if self.send_reminders:
	    return _('Once a month, your password will be emailed to you as'
                     ' a reminder.')
	return ''

    def ParseTags(self, template, replacements, lang=None):
	if lang is None:
            lang = self.preferred_language
	text = self.SnarfHTMLTemplate(template, lang)
	parts = regsub.splitx(text, '</?[Mm][Mm]-[^>]*>')
	i = 1
	while i < len(parts):
	    tag = string.lower(parts[i])
	    if replacements.has_key(tag):
		parts[i] = replacements[tag]
	    else:
		parts[i] = ''
	    i = i + 2
	return string.join(parts, '')

    # This needs to wait until after the list is inited, so let's build it
    # when it's needed only.
    def GetStandardReplacements(self, lang=None):
        if lang is None:
            lang = self.preferred_language
        dmember_len = len(self.GetDigestMembers())
        member_len = len(self.GetMembers())
        values = self.GetAvailableLanguages()
        legend = map(_, map(Utils.GetLanguageDescr, values))
        selected = values.index(self.preferred_language)

	return { 
	    '<mm-mailman-footer>' : self.GetMailmanFooter(),
	    '<mm-list-name>' : self.real_name,
	    '<mm-email-user>' : self._internal_name,
	    '<mm-list-description>' : self.description,
	    '<mm-list-info>' : string.join(string.split(self.info, '\n'),
					   '<br>'),
	    '<mm-form-end>'  : self.FormatFormEnd(),
	    '<mm-archive>'   : self.FormatArchiveAnchor(),
	    '</mm-archive>'  : '</a>',
            '<mm-list-subscription-msg>' : self.FormatSubscriptionMsg(),
            '<mm-restricted-list-message>' : \
            	self.RestrictedListMessage(_('current archive'),
                                           self.archive_private),
	    '<mm-num-reg-users>' : `member_len`,
	    '<mm-num-digesters>' : `dmember_len`,
	    '<mm-num-members>' : (`member_len + dmember_len`),
	    '<mm-posting-addr>' : '%s' % self.GetListEmail(),
	    '<mm-request-addr>' : '%s' % self.GetRequestEmail(),
	    '<mm-owner>' : self.GetAdminEmail(),
	    '<mm-reminder>' : self.FormatReminder(self.preferred_language),
            '<mm-host>' : self.host_name,
	    '<mm-list-langs>' : SelectOptions('language', values, legend,
                                              selected).Format(),
	    }

    def GetAllReplacements(self, lang=None):
        """
        returns standard replaces plus formatted user lists in
        a dict just like GetStandardReplacements.
        """
        if lang is None:
            lang = self.preferred_language
        d = self.GetStandardReplacements(lang)
        d.update({"<mm-regular-users>": self.FormatUsers(0, lang),
                  "<mm-digest-users>": self.FormatUsers(1, lang)})
        return d
                  
    def InitTemplates(self, langs=None):
	def ExtensionFilter(item):
	    return item[-5:] == '.html'

        if not langs:
            langs = [mm_cfg.DEFAULT_SERVER_LANGUAGE]

        for L in langs:
	  files = filter(ExtensionFilter,
                         os.listdir(os.path.join(mm_cfg.TEMPLATE_DIR, L)))
	  Utils.MakeDirTree(os.path.join(self._template_dir, L))
    
	  for filename in files:
	     file1 = open(os.path.join(mm_cfg.TEMPLATE_DIR, L, filename))
	     text = file1.read()
	     file1.close()
	     file2 = open(os.path.join(self._template_dir, L, filename), 'w+')
	     file2.write(text)
	     file2.close()
