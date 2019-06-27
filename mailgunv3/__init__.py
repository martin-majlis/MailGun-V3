from __future__ import unicode_literals

import base64
import enum
import hashlib
import hmac
import json
import random
import requests

#from mailgun3 import Mailgun
BASE_URL = 'https://api.mailgun.net/v3'


class MailGunV3(object):
    """
    This is the only class that should be directly initialized.
    """

    def __init__(self, domain, private_key, public_key):
        self.domain = domain
        self.private_key = private_key
        self.public_key = public_key
        self.auth = ('api', private_key)

    def _post(self, url, data, auth=None, files=None, include_domain=True):
        return requests.post(url, auth=auth or self.auth, data=data, files=files)

    def _get(self, url, params=None, auth=None, include_domain=True):
        return requests.get(url, auth=auth or self.auth, params=params)

    def _put(self, url, params=None, auth=None, include_domain=True):
        return requests.put(url, auth=auth or self.auth, params=params)

    def _delete(self, url, params=None, auth=None, include_domain=True):
        return requests.delete(url, auth=auth or self.auth, params=params)

    def mailinglist(self, email):
        return MailingList(self, email)

    def message(self,
                from_email,
                to,
                cc=None,
                bcc=None,
                subject=None,
                text=None,
                html=None,
                user_variables=None,
                reply_to=None,
                headers=None,
                inlines=None,
                attachments=None,
                campaign_id=None,
                tags=None):
        return MailMessage(
            self,
            from_email,
            to,
            cc=cc,
            bcc=bcc,
            subject=subject,
            text=text,
            html=html,
            user_variables=user_variables,
            reply_to=reply_to,
            headers=headers,
            inlines=inlines,
            attachments=attachments,
            campaign_id=campaign_id,
            tags=tags
        )


class APIResponse(object):
    def __init__(self):
        self.status_code = 200
        self.status_msg = 'OK'
        self.text = ''
        self.json = ''

    def _set_error(self, status_code, status_msg):
        self.status_code = status_code
        self.status_msg = status_msg

    def _has_error(self):
        return self.status_code != 200

    def __repr__(self):
        return repr({
            'status_code': self.status_code,
            'status_msg': self.status_msg,
            'text': self.text,
            'json': self.json,
        })

    def _copy_state(self, api_response):
        self.status_code = api_response.status_code
        self.status_msg = api_response.status_msg
        self.text = api_response.text
        self.json = api_response.json


class MailMessage(APIResponse):
    def __init__(self,
                 mailgun,
                 from_email,
                 to,
                 cc=None,
                 bcc=None,
                 subject=None,
                 text=None,
                 html=None,
                 user_variables=None,
                 reply_to=None,
                 headers=None,
                 inlines=None,
                 attachments=None,
                 campaign_id=None,
                 tags=None):
        super().__init__()
        self.mailgun = mailgun
        self.from_email = from_email
        self.to = to
        self.cc = cc or []
        self.bcc = bcc or []
        self.subject = subject or ''
        self.text = text
        self.html = html
        self.user_variables = user_variables
        self.reply_to = reply_to
        self.headers = headers
        self.inlines = inlines
        self.attachments = attachments
        self.campaign_id = campaign_id
        self.tags = tags

    def send(self):
                # sanity checks
        assert (self.text or self.html)

        data = {
            'from': self.from_email,
            'to': self.to,
            'cc': self.cc,
            'bcc': self.bcc,
            'subject': self.subject,
            'text': self.text,
            'html': self.html,
        }

        if self.reply_to:
            data['h:Reply-To'] = self.reply_to

        if self.headers:
            for k, v in self.headers.items():
                data["h:%s" % k] = v

        if self.campaign_id:
            data['o:campaign'] = self.campaign_id

        if self.tags:
            data['o:tag'] = self.tags

        if self.user_variables:
            for k, v in self.user_variables.items():
                data['v:%s' % k] = v

        files = []

        if self.inlines:
            for filename in self.inlines:
                files.append(('inline', open(filename)))

        if self.attachments:
            for filename, content_type, content in self.attachments:
                files.append(('attachment', (filename, content, content_type)))

        res = self.mailgun._post(
            BASE_URL + '/' + self.mailgun.domain + '/messages',
            data,
            files=files
        )
        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during sending e-mail to {}.'.format(self.to),
            )
        return self

    def get(self):
        if self._has_error():
            return self

        res = self.mailgun._get(BASE_URL + '/lists/' +
                                self.address)
        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during mailing list {} retrieval.'.format(self.address),
            )
        return self


# https://documentation.mailgun.com/api-mailinglists.html#mailing-lists


class MailingList(APIResponse):
    def __init__(self, mailgun, address):
        super().__init__()
        self.mailgun = mailgun
        self.address = address

    def get(self):
        if self._has_error():
            return self

        res = self.mailgun._get(BASE_URL + '/lists/' +
                                self.address)
        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during mailing list {} retrieval.'.format(self.address),
            )
        return self

    def delete(self):
        if self._has_error():
            return self

        res = self.mailgun._delete(BASE_URL + '/lists/' +
                                   self.address)

        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during mailing list {} deletion.'.format(self.address),
            )
        return self

    def create(self, name=None, description=None, access_level=None):
        if self._has_error():
            return self

        data = {'address': self.address}
        if name:
            data['name'] = name

        if description:
            data['description'] = description

        if access_level and access_level in ['readonly', 'members', 'everyone']:
            data['access_level'] = access_level

        res = self.mailgun._post(BASE_URL + '/lists', data)
        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during mailing list {} creation.'.format(self.address),
            )
        return self

    def update(self, name=None, description=None, access_level=None):
        if self._has_error():
            return self

        data = {'address': self.address}
        if name:
            data['name'] = name

        if description:
            data['description'] = description

        if access_level and access_level in ['readonly', 'members', 'everyone']:
            data['access_level'] = access_level

        res = self.mailgun._put(BASE_URL + '/lists/' + self.address, data)
        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during mailing list {} update.'.format(self.address),
            )
        return self

    def members(self):
        if self._has_error():
            return self

        res = self.mailgun._get(BASE_URL + '/lists/' +
                                self.address + '/members/pages')
        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during mailing list {} members.'.format(self.address),
            )
        return self

    def member(self, address):
        return MailingListMember(self.mailgun, self, address)


class MailingListMember(APIResponse):
    def __init__(self, mailgun, mailinglist, address):
        super().__init__()
        self.mailgun = mailgun
        self.mailinglist = mailinglist
        self.address = address
        self._copy_state(mailinglist)

    def create(self, name=None, params=None, subscribed=True, upsert=False):
        if self._has_error():
            return self

        data = {'address': self.address}
        if name:
            data['name'] = name

        if params:
            data['vars'] = json.dumps(params) if isinstance(
                params, dict) else params

        if not subscribed:
            data['subscribed'] = 'no'

        if upsert:
            data['upsert'] = 'yes'

        res = self.mailgun._post(BASE_URL + '/lists/' +
                                 self.mailinglist.address + '/members', data)
        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during adding member {} into mailing list.'.format(
                    self.address,
                    self.mailinglist.address,
                ),
            )
        return self

    def update(self, name=None, params=None, subscribed=True):
        if self._has_error():
            return self

        data = {}
        if name:
            data['name'] = name

        if params:
            data['vars'] = json.dumps(params) if isinstance(
                params, dict) else params

        if not subscribed:
            data['subscribed'] = 'no'

        res = self.mailgun._put(BASE_URL + '/lists/' +
                                self.mailinglist.address + '/members/' + self.address, data)
        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during updating member {} from mailing list.'.format(
                    self.address,
                    self.mailinglist.address,
                ),
            )
        return self

    def get(self):
        if self._has_error():
            return self

        res = self.mailgun._get(BASE_URL + '/lists/' +
                                self.mailinglist.address + '/members/' + self.address)
        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during retrieving member {} from mailing list.'.format(
                    self.address,
                    self.mailinglist.address,
                ),
            )
        return self

    def delete(self):
        if self._has_error():
            return self

        res = self.mailgun._delete(BASE_URL + '/lists/' +
                                   self.mailinglist.address + '/members/' + self.address)
        self.text = res.text
        self.json = res.json
        if (res.status_code != 200):
            self._set_error(
                res.status_code,
                'Error during deleting member {} from mailing list.'.format(
                    self.address,
                    self.mailinglist.address,
                ),
            )
        return self
