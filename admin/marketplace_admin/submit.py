# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

import re
import yaml
import logging
import requests


LOGGER = logging.getLogger(__name__)


def init_subparser(subparsers):
    parser = subparsers.add_parser('submit',
                                   help='Submits data to the REST API')
    parser.add_argument('-u', '--url',
                        help='The url of the REST API to submit to',
                        default='http://localhost:8000')
    parser.add_argument('-d', '--data',
                        help='The path to the YAML data file',
                        required=True)
    return parser



def _api_submit(api_url, path, body, auth=None):
    url = '{}/{}'.format(api_url, path)
    headers = {'Authorization': auth} if auth else None

    response = requests.post(url, json=body, headers=headers)
    body = response.json()

    if response.status_code > 299:
        LOGGER.warn('Submit failed to URL: %s', path)
        LOGGER.warn('%s %s: %s',
                    response.status_code,
                    response.reason,
                    body.get('error'))

    return body


def do_submit(opts):
    if not opts.data:
        raise RuntimeError('No data file specified, use -d or --data')

    LOGGER.info('Reading data: %s', opts.data)
    data = yaml.load(open(opts.data, 'r'))

    url = opts.url if re.match('://', opts.url) else 'http://' + opts.url
    submit = lambda p, b, a=None: _api_submit(url, p, b, a)
    LOGGER.info('Submitting data to URL: %s', url)

    for account in data['ACCOUNTS']:
        LOGGER.info('Submitting Account: %s', account['label'])
        auth = submit('accounts', account).get('authorization')

        if not auth:
            credentials = {
                'email': account['email'],
                'password': account['password']
            }
            auth = submit('authorization', credentials).get('authorization')

            if not auth:
                LOGGER.warn('No auth token for %s, skipping dependent data',
                            account['label'])
                continue

        for asset in account['ASSETS']:
            LOGGER.debug('Submitting Asset: %s', asset['name'])
            submit('assets', asset, auth)

        for holding in account['HOLDINGS']:
            LOGGER.debug('Submitting Holding: %s', holding['label'])
            submit('holdings', holding, auth)

        for offer in account['OFFERS']:
            LOGGER.debug('Submitting Offer: %s', offer['label'])
            submit('offers', offer, auth)

    LOGGER.info('Data submission complete.')
