# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

from re import sub
from time import time
from os.path import dirname, join
import requests

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

__author__ = 'chults'

LOGGER = getLogger(__name__)


class TrafficSkill(MycroftSkill):

    def __init__(self):
        super(TrafficSkill, self).__init__("TrafficSkill")
        self.api_key = self.config.get('api_key')
        self.debug = True

    def initialize(self):
        self.load_data_files(dirname(__file__))
        self.load_vocab_files(join(dirname(__file__), 'vocab', self.lang))
        self.load_regex_files(join(dirname(__file__), 'regex', self.lang))
        self.__build_traffic_intent()

    def __build_traffic_intent(self):
        intent = IntentBuilder("TrafficNowIntent").require("TrafficKeyword")\
                   .require("Destination").optionally("Origin").build()
        self.register_intent(intent, self.handle_traffic_now_intent)

    def handle_traffic_now_intent(self, message):
        try:
            LOGGER.debug("Config Data: %s" % self.config)
            self.get_drive_time_now(message)
        except Exception as err:
            LOGGER.error("Error: {0}".format(err))

    def get_drive_time_now(self, message):
        depart_time_now = str(int(time()))
        self.request_drive_time(message, depart_time_now, self.api_key)

    def get_drive_time_at(self, message):
        depart_time = str(int(time())) # Figure out requested time
        self.request_drive_time(message, depart_time, self.api_key)

    def request_drive_time(self, message, depart_time, api_key):
        poi_dict = self.config.get('pois')
        LOGGER.debug("POI: %s" % poi_dict)
        #destination = message.metadata.get("destination")
        #origin = message.metadata.get("origin")
        if self.debug:
            destination = "1339 Broad St, Clifton, NJ, 07013"
            origin = "13 Hague St, Jersey City, NJ 07307"
        LOGGER.debug("Origin: %s" % origin)
        LOGGER.debug("Destination: %s" % destination)
        self.speak_dialog("welcome", data={'destination': destination})
        orig_enc = self.__convert_address(origin)
        dest_enc = self.__convert_address(destination)
        api_root = 'https://maps.googleapis.com/maps/api/directions/json'
        api_params = '?origin=' + orig_enc +\
                     '&destination=' + dest_enc +\
                     '&departure_time=' + depart_time +\
                     '&traffic_model=best_guess' +\
                     '&key=' + api_key
        api_url = api_root + api_params
        LOGGER.debug("API Request: %s" % api_url)
        response = requests.get(api_url)

        if response.status_code != 200:
            LOGGER.error(response.json())

        else:
            LOGGER.debug("API Respose: %s" % response.json())
            routes = response.json()['routes'][0]
            legs = routes['legs'][0]
            duration_norm = int(legs['duration']['value']/60) # In minutes
            duration_traffic = int(legs['duration_in_traffic']['value']/60) # In minutes
            traffic_time = duration_traffic - duration_norm
            if traffic_time >= 30:
                LOGGER.debug("Traffic = Heavy")
                self.speak_dialog('traffic.heavy', data={'destination': destination,
                                                         'trip_time': duration_norm,
                                                         'traffic_time': traffic_time})
            elif traffic_time >= 10:
                LOGGER.debug("Traffic = Delay")
                self.speak_dialog('traffic.delay', data={'destination': destination,
                                                         'trip_time': duration_norm,
                                                         'traffic_time': traffic_time})
            else:
                LOGGER.debug("Traffic = Clear")
                self.speak_dialog('traffic.clear', data={'destination': destination,
                                                         'trip_time': duration_norm})

    def __convert_address(self, address):
        address_converted = sub(' ', '+', address)
        return address_converted

    def stop(self):
        self.speak_dialog('traffic.module.halting')
        self.process.terminate()
        self.process.wait()



def create_skill():
    return TrafficSkill()
