#!/usr/bin/env python
#
# OTX_Siphon
# Pulls pulses from Alien Vault subscription list
#
# Create an account and curate your subscriptions
# https://otx.alienvault.com
#
# AUTHOR Karma: https://github.com/KarmaIncarnate
# Adapted from OTX 2 CRITS by lolnate @ https://github.com/lolnate/otx2crits
# Using AlienVault SDK for OTXv2 https://github.com/AlienVault-OTX/OTX-Python-SDK


import argparse
import os
import requests
import json
import datetime
import csv

from configparser import ConfigParser


class OTX_Siphon(object):
    def __init__(self, dev=False, config=None, days=None):
        self.config = self.load_config(config)  # Load configuration

        self.otx_api_key = self.config.get('otx', 'otx_api_key')  # Set AlienVault API key
        self.otx_url = self.config.get('otx', 'otx_url')  # Set AlienVault URL

        self.proxies = {
            'http': self.config.get('proxy', 'http'),  # Set HTTP proxy if present in config file
            'https': self.config.get('proxy', 'https')  # Set HTTPS proxy if present in config file
        }

        if dev:
            print('Developer options not yet programmed.')  # Need to program developer parameters

        self.modified_since = None  # Set pulse range to those modified in last x days
        if days:
            print('Searching for pulses modified in last {}'
                  ' days'.format(days))
            self.modified_since = datetime.datetime.now() - datetime.timedelta(days=days)

    def execute(self):
        for pulse in self.get_pulse_generator(modified_since=self.modified_since,
                                              proxies=self.proxies):
            print('Found pulse with id {} and title {}'.format(pulse['id'],
                                                               pulse['name'].encode("utf-8")))

            indicator_data = pulse['indicators']  # Pull indicators from pulse
            event_title = pulse['name']  # Pull title from pulse
            created = pulse['created']  # Pull date/time from pulse
            reference = ''  # Pull reference from pulse if available
            if not reference:
                reference = 'No reference documented'
            else:
                reference = pulse['reference'][0]

            print('Pulse name: ' + event_title)
            print('Created: ' + created)

            with open("output.csv", 'w', newline='', encoding='utf-8') as resultFile:
                for i in pulse['indicators']:
                    # Probably want to break this out so you can use add
                    # and/or write methods. Need to parse the indicator_data
                    # Probably use some sort of mapping
                    result = [event_title, created, i['type'], i['indicator'], reference]
                    print('Indicator data: ' + str(indicator_data))
                    print('--------------------------------------')
                    print(result)
                    wr = csv.writer(resultFile, dialect='excel')
                    wr.writerow(result)

    def parse_config(self, location):
        """Parses the OTX config file from the given location."""
        try:
            config = ConfigParser()
            config.read(location)
        except Exception as e:
            print('Error parsing config: {}'.format(e))
            return False
        if len(config.sections()) == 0:
            print('Configuration file not found: {}'.format(location))
            return False
        return config

    def load_config(self, given_location=None):
        """"Search for config and return parsed config file."""
        if given_location:  # Check location provided by user
            print('Config found at given_location')
            return self.parse_config(given_location)
        config_file = os.getenv('OTX_CONFIG_FILE', None)  # Check env
        if config_file:
            print('Config file found automatically')
            return self.parse_config(config_file)
        config_file = os.path.join(os.path.expanduser('~'), '.otx_config')  # Check path for .otx_config file
        # Walk or?
        # for root, dirs, files in os.walk(os.path.expanduser('~'))
        #     for file in files:
        #         if file.endswith(.otx_config):
        #             return self.parse_config(config_file)
        return self.parse_config(config_file)

    def otx_get(self, url, proxies=None, verify=True):
        """Build headers and issue a get request to AlienVault and return response data."""
        headers = {
            'X-OTX-API-KEY': self.otx_api_key,
        }

        r = requests.get(url, headers=headers, proxies=proxies, verify=verify)
        if r.status_code == 200:
            return r.text
        else:
            print('Error retrieving AlienVault OTX data.')
            print('Status code was: {}'.format(r.status_code))
            return False

    def get_pulse_generator(self, modified_since=None,
                            proxies=None, verify=True):
        """Accept, loop/parse, and store pulse data.

        # Yields pulse and its data while it can obtain more data(recursive).
        # If no limit specified the API will only return 5 pulses total. (lol)
        """

        args = []

        if modified_since:
            args.append('modified_since={}'.format(
                modified_since.strftime('%Y-%m-%d %H:%M:%S.%f')))

        args.append('limit=10')
        args.append('page=1')
        request_args = '&'.join(args)
        request_args = '?{}'.format(request_args)

        response_data = self.otx_get('{}/pulses/subscribed{}'
                                     .format(self.otx_url, request_args),
                                     proxies=proxies, verify=verify)
        while response_data:  # Loop through pulse data
            all_pulses = json.loads(response_data)
            if 'results' in all_pulses:
                for pulse in all_pulses['results']:
                    yield pulse
            response_data = None
            if 'next' in all_pulses:
                if all_pulses['next']:
                    response_data = self.otx_get(all_pulses['next'],
                                                 proxies=proxies,
                                                 verify=verify)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', dest='config', default=None, help='Provide '
                                                                   'a specific configuration file path.')
    argparser.add_argument('-d', dest='days', default=None, type=int,
                           help='Specify the max range of pulses grabbed '
                                'in days. (days old)')
    argparser.add_argument('--dev', dest='dev', action='store_true',
                           default=False, help='Use dev options.')
    args = argparser.parse_args()

    siphon = OTX_Siphon(dev=args.dev, config=args.config, days=args.days)
    siphon.execute()


if __name__ == '__main__':
    main()
