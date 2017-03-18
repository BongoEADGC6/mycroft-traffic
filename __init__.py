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
        self.__init_traffic()
        self.debug = False

    def __init_traffic(self):
        self.api_key = self.config.get('api_key')
        self.poi_dict = self.config.get('pois')

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
        depart_time = str(int(time())) # TODO - Figure out requested time
        self.request_drive_time(message, depart_time, self.api_key)

    def build_itinerary(self, message):
        LOGGER.debug("POIs: %s" % self.poi_dict)
        spoken_dest = message.data.get("Destination")
        spoken_origin = message.data.get("Origin")
        if spoken_origin == None:
            spoken_origin = 'home'
        poi_users = self.poi_dict.keys()
        LOGGER.debug("POI Users: %s" % poi_users)
        for user in poi_users:
            if user in spoken_origin:
                origin_profile = user
            else:
                origin_profile = 'default'
            if user in spoken_dest:
                dest_profile = user
            else:
                dest_profile = 'default'
        LOGGER.debug("Loading origin from profile...")
        try:
            origin_addr = self.poi_dict[origin_profile]['origins'][spoken_origin]
        except Exception as err:
            LOGGER.error("Falling back to home as origin... Error Message: %s" % err)
            spoken_origin = "home"
            origin_addr = self.poi_dict[origin_profile]['origins']['home']
        LOGGER.debug("Origin Profile: %s" % origin_profile)
        LOGGER.debug("Origin Name: %s" % spoken_origin)
        LOGGER.debug("Origin Address: %s" % origin_addr)
        LOGGER.debug("Loading destination from profile...")

        dest_addr = self.poi_dict[dest_profile]['destinations'][spoken_dest]
        LOGGER.debug("Destination Profile: %s" % dest_profile)
        LOGGER.debug("Destination Name: %s" % spoken_dest)
        LOGGER.debug("Destination Address: %s" % dest_addr)
        spoken_depart_time = message.data.get("Depart")
        itinerary_dict = {
                'origin_name': spoken_origin,
                'origin': origin_addr,
                'dest_name': spoken_dest,
                'destination': dest_addr,
                }
        LOGGER.debug("Itinerary:: %s" % itinerary_dict)
        return itinerary_dict

    def __get_address_from_pois(self, profile, poi_type, poi_name):
        address = self.poi_dict[profile][poi_type][poi_name]

    def request_drive_time(self, message, depart_time, api_key):
        poi_dict = self.config.get('pois')
        itinerary = self.build_itinerary(message)
        self.speak_dialog("welcome", data={'destination': itinerary['dest_name'], 'origin': itinerary['origin_name']})
        orig_enc = self.__convert_address(itinerary['origin'])
        dest_enc = self.__convert_address(itinerary['destination'])
        api_root = 'https://maps.googleapis.com/maps/api/directions/json'
        api_params = '?origin=' + orig_enc +\
                     '&destination=' + dest_enc +\
                     '&departure_time=' + depart_time +\
                     '&traffic_model=best_guess' +\
                     '&key=' + api_key
        api_url = api_root + api_params
        LOGGER.debug("API Request: %s" % api_url)
        response = requests.get(api_url)

        if response.status_code == requests.codes.ok and response.json()['status'] == "REQUEST_DENIED":
            LOGGER.error(response.json())
            self.speak_dialog('traffic.error.api')

        elif response.status_code == requests.codes.ok:
            LOGGER.debug("API Response: %s" % response)
            routes = response.json()['routes'][0]
            legs = routes['legs'][0]
            duration_norm = int(legs['duration']['value']/60) # In minutes
            duration_traffic = int(legs['duration_in_traffic']['value']/60) # In minutes
            traffic_time = duration_traffic - duration_norm
            if traffic_time >= 30:
                LOGGER.debug("Traffic = Heavy")
                self.speak_dialog('traffic.heavy', data={'destination': itinerary['dest_name'],
                                                         'trip_time': duration_norm,
                                                         'traffic_time': traffic_time})
            elif traffic_time >= 10:
                LOGGER.debug("Traffic = Delay")
                self.speak_dialog('traffic.delay', data={'destination': itinerary['dest_name'],
                                                         'trip_time': duration_norm,
                                                         'traffic_time': traffic_time})
            else:
                LOGGER.debug("Traffic = Clear")
                self.speak_dialog('traffic.clear', data={'destination': itinerary['dest_name'],
                                                        'trip_time': duration_norm})

        else:
            LOGGER.error(response.json())

    def __convert_address(self, address):
        address_converted = sub(' ', '+', address)
        return address_converted

    def stop(self):
        self.speak_dialog('traffic.module.halting')
        #self.process.terminate()
        #self.process.wait()
        pass


def create_skill():
    return TrafficSkill()

