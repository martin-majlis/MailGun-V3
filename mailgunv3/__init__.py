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

    def post(self, url, data, auth=None, files=None, include_domain=True):
        print(repr(url))
        return requests.post(url, auth=auth or self.auth, data=data, files=files)

    def get(self, url, params=None, auth=None, include_domain=True):
        return requests.get(url, auth=auth or self.auth, params=params)

    def put(self, url, params=None, auth=None, include_domain=True):
        return requests.put(url, auth=auth or self.auth, params=params)

    def delete(self, url, params=None, auth=None, include_domain=True):
        return requests.delete(url, auth=auth or self.auth, params=params)

    def mailinglist(self, email):
        return MailingList(self, email)

    def send_message(self, from_email, to, cc=None, bcc=None,
                     subject=None, text=None, html=None, user_variables=None,
                     reply_to=None, headers=None, inlines=None, attachments=None, campaign_id=None,
                     tags=None):
        # sanity checks
        assert (text or html)

        data = {
            'from': from_email,
            'to': to,
            'cc': cc or [],
            'bcc': bcc or [],
            'subject': subject or '',
            'text': text or '',
            'html': html or '',
        }

        if reply_to:
            data['h:Reply-To'] = reply_to

        if headers:
            for k, v in headers.items():
                data["h:%s" % k] = v

        if campaign_id:
            data['o:campaign'] = campaign_id

        if tags:
            data['o:tag'] = tags

        if user_variables:
            for k, v in user_variables.items():
                data['v:%s' % k] = v

        files = []

        if inlines:
            for filename in inlines:
                files.append(('inline', open(filename)))

        if attachments:
            for filename, content_type, content in attachments:
                files.append(('attachment', (filename, content, content_type)))

        return self.post(BASE_URL + '/' + self.domain + '/messages', data, files=files)


class Mailgun(object):
    def __init__(self, domain, private_key, public_key):
        self.private_key = private_key
        self.public_key = public_key
        self.auth = ('api', private_key)
        self.base_url = '{0}/{1}'.format(BASE_URL, domain)

    def post(self, path, data, auth=None, files=None, include_domain=True):
        url = self.base_url if include_domain else BASE_URL
        return requests.post(url + path, auth=auth or self.auth, data=data, files=files)

    def get(self, path, params=None, auth=None, include_domain=True):
        url = self.base_url if include_domain else BASE_URL
        return requests.get(url + path, auth=auth or self.auth, params=params)

    def send_message(self, from_email, to, cc=None, bcc=None,
                     subject=None, text=None, html=None, user_variables=None,
                     reply_to=None, headers=None, inlines=None, attachments=None, campaign_id=None,
                     tags=None):
        # sanity checks
        assert (text or html)

        data = {
            'from': from_email,
            'to': to,
            'cc': cc or [],
            'bcc': bcc or [],
            'subject': subject or '',
            'text': text or '',
            'html': html or '',
        }

        if reply_to:
            data['h:Reply-To'] = reply_to

        if headers:
            for k, v in headers.items():
                data["h:%s" % k] = v

        if campaign_id:
            data['o:campaign'] = campaign_id

        if tags:
            data['o:tag'] = tags

        if user_variables:
            for k, v in user_variables.items():
                data['v:%s' % k] = v

        files = []

        if inlines:
            for filename in inlines:
                files.append(('inline', open(filename)))

        if attachments:
            for filename, content_type, content in attachments:
                files.append(('attachment', (filename, content, content_type)))

        return self.post('/messages', data, files=files)

    def get_events(self, begin=None, end=None, ascending=None, limit=None, filters=None):
        params = dict()

        if begin:
            params['begin'] = begin

        if end:
            params['end'] = end

        if ascending:
            params['ascending'] = ascending

        if limit:
            params['limit'] = limit

        if filters is None:
            filters = dict()

        params.update(filters)

        return self.get('/events', params=params)

    def create_list(self, address, name=None, description=None, access_level=None):
        data = {'address': address}
        if name:
            data['name'] = name

        if description:
            data['description'] = description

        if access_level and access_level in ['readonly', 'members', 'everyone']:
            data['access_level'] = access_level

        return self.post('/lists', data, include_domain=False)

    def add_list_member(self, list_name, address, name=None, params=None,
                        subscribed=True, upsert=False):
        data = {'address': address}
        if name:
            data['name'] = name

        if params:
            data['vars'] = json.dumps(params) if isinstance(
                params, dict) else params

        if not subscribed:
            data['subscribed'] = 'no'

        if upsert:
            data['upsert'] = 'yes'

        return self.post('/lists/%s/members' % list_name, data, include_domain=False)

    def verify_authenticity(self, token, timestamp, signature):
        return signature == hmac.new(
            key=self.private_key, msg='{}{}'.format(timestamp, token),
            digestmod=hashlib.sha256).hexdigest()

    def validate(self, address):
        params = dict(address=address)
        auth = ('api', self.public_key)
        return self.get('/address/validate', params=params, auth=auth, include_domain=False)


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

# https://documentation.mailgun.com/api-mailinglists.html#mailing-lists


class MailingList(APIResponse):
    def __init__(self, mailgun, address):
        super().__init__()
        self.mailgun = mailgun
        self.address = address

    def get(self):
        if self._has_error():
            return self

        res = self.mailgun.get(BASE_URL + '/lists/' +
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

        res = self.mailgun.delete(BASE_URL + '/lists/' +
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

        res = self.mailgun.post(BASE_URL + '/lists', data)
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

        res = self.mailgun.put(BASE_URL + '/lists/' + self.address, data)
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

        res = self.mailgun.get(BASE_URL + '/lists/' +
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

        res = self.mailgun.post(BASE_URL + '/lists/' +
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

        res = self.mailgun.put(BASE_URL + '/lists/' +
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

        res = self.mailgun.get(BASE_URL + '/lists/' +
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

        res = self.mailgun.get(BASE_URL + '/lists/' +
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


