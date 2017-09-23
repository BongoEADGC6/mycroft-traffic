from re import sub
from time import time
from os.path import dirname, join
import requests
import json

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

__author__ = 'BONGEADGC6'

LOGGER = getLogger(__name__)


class GoogleMapsClient(object):

    def __init__(self, api_key=None):
        import googlemaps
        self.gmaps = googlemaps.Client(key=api_key)
        LOGGER.debug("Connected to Google API: %s" % self.gmaps)

    def traffic(self, **traffic_args):
        LOGGER.debug('Google API - Traffic')
        response = self.gmaps.directions(**traffic_args)[0]
        # if response.status_code == requests.codes.ok and \
        #        response.json()['status'] == "REQUEST_DENIED":
        #    LOGGER.error(response.json())
        #    self.speak_dialog('traffic.error.api')

        # elif response.status_code == requests.codes.ok:
        LOGGER.debug("API Response: %s" % json.dumps(response))
        legs = response['legs'][0]
        # convert time to minutes
        duration_norm = int(legs['duration']['value']/60)
        if legs['duration_in_traffic']:
            duration_traffic = int(legs['duration_in_traffic']['value']/60)
        else:
            duration_traffic = duration_norm
        traffic_time = duration_traffic - duration_norm
        route_summ = routes['summary']
        return duration_norm, duration_traffic, traffic_time, route_summ

    def distance(self, **dist_args):
        LOGGER.debug('Google API - Distance Matrix')
        response = self.gmaps.distance_matrix(**dist_args)
        LOGGER.debug("API Response: %s" % json.dumps(response))
        rows = response['rows']
        # convert time to minutes
        element = rows[0]['elements'][0]
        duration_norm = int(element['duration']['value']/60)
        if legs['duration_in_traffic']:
            duration_traffic = int(element['duration_in_traffic']['value']/60)
        else:
            duration_traffic = duration_norm
        traffic_time = duration_traffic - duration_norm
        return duration_norm, duration_traffic, traffic_time

    def places(self, **places_args):
        LOGGER.debug('Google API - Places')
        response = self.gmaps.places(**places_args)
        LOGGER.debug("API Response: %s" % json.dumps(response))
        with open('/tmp/api_response.json', "w") as output:
            output.write(json.dumps(response))
        results = response['results']
        result = results[0]
        location = result['geometry']['location']
        geo_loc = [location['lat'], location['lng']]
        return geo_loc

    def places_nearby(self, **places_nearby_args):
        LOGGER.debug('Google API - Places Nearby')
        response = self.gmaps.places_nearby(**places_nearby_args)
        LOGGER.debug("API Response: %s" % json.dumps(response))
        with open('/tmp/api_response.json', "w") as output:
            output.write(json.dumps(response))
        results = response['results']
        result = results[0]
        location = result['geometry']['location']
        geo_loc = [location['lat'], location['lng']]
        return geo_loc


class TrafficSkill(MycroftSkill):

    def __init__(self):
        super(TrafficSkill, self).__init__("TrafficSkill")
        # TODO - Allow more providers (i.e. Google, OpenStreetMap, etc.)
        provider = self.config.get('provider', 'google')
        LOGGER.debug("Configured Provider: %s" % provider)
        self.dist_units = self.config.get("system_unit")
        if self.dist_units == 'english':
            self.dist_units = 'imperial'
        if provider == 'google':
            api_key = self.config.get('api_key', None)
            self.maps = GoogleMapsClient(api_key)
            LOGGER.debug("Connected to Google API: %s" % self.maps)
        self.poi_dict = self.config.get('pois')

    def initialize(self):
        self.language = self.config_core.get('lang')
        self.load_data_files(dirname(__file__))
        self.load_vocab_files(join(dirname(__file__), 'vocab', self.lang))
        self.load_regex_files(join(dirname(__file__), 'regex', self.lang))
        self.__build_traffic_now_intent()
        self.__build_traffic_later_intent()
        self.__build_proximity_intent()

    def __build_traffic_now_intent(self):
        intent = IntentBuilder("TrafficNowIntent").require("TrafficKeyword")\
            .require("Destination").optionally("Origin").build()
        self.register_intent(intent, self.handle_traffic_now_intent)

    def __build_traffic_later_intent(self):
        intent = IntentBuilder("TrafficLaterIntent").require("TrafficKeyword")\
            .require("Destination").optionally("Origin").build()
        self.register_intent(intent, self.handle_traffic_later_intent)

    def __build_proximity_intent(self):
        intent = IntentBuilder("ProximityIntent").require("ProximityKeyword")\
            .require("Destination").optionally("Origin").build()
        self.register_intent(intent, self.handle_proximity_intent)

    def handle_traffic_now_intent(self, message):
        try:
            LOGGER.debug("Config Data: %s" % self.config)
            depart_time_now = str(int(time()))
            self.request_drive_time(message, depart_time_now)
        except Exception as err:
            LOGGER.error("Error: {0}".format(err))

    def handle_traffic_later_intent(self, message):
        try:
            depart_time_now = str(int(time()))
            self.request_drive_time(message, depart_time_now)
        except Exception as err:
            LOGGER.error("Error: {0}".format(err))

    def handle_proximity_intent(self, message):
        try:
            depart_time_now = str(int(time()))
            self.request_distance(message)
        except Exception as err:
            LOGGER.error("Error: {0}".format(err))

    def build_itinerary(self, message):
        LOGGER.debug("POIs: %s" % self.poi_dict)
        spoken_dest = message.data.get("Destination")
        spkn_origin = message.data.get("Origin")
        if spkn_origin is None:
            spkn_origin = 'home'
        poi_users = self.poi_dict.keys()
        LOGGER.debug("POI Users: %s" % poi_users)
        for user in poi_users:
            if user in spkn_origin:
                origin_profile = user
            else:
                origin_profile = 'default'
            if user in spoken_dest:
                dest_profile = user
            else:
                dest_profile = 'default'
        LOGGER.debug("Loading origin from profile...")
        try:
            origin_addr = self.poi_dict[origin_profile]['origins'][spkn_origin]
        except KeyError:
            LOGGER.error("Falling back to home as origin.")
            spkn_origin = "home"
            origin_addr = self.poi_dict[origin_profile]['origins']['home']
        LOGGER.debug("Origin Profile: %s" % origin_profile)
        LOGGER.debug("Origin Name: %s" % spkn_origin)
        LOGGER.debug("Origin Address: %s" % origin_addr)
        LOGGER.debug("Loading destination from profile...")
        try:
            dest_prof_info = self.poi_dict[dest_profile]
            dest_addr = dest_prof_info['destinations'][spoken_dest]
        except KeyError:
            LOGGER.error("Destination not registered. Looking up Destination")
            dest_addr = spoken_dest
        LOGGER.debug("Destination Profile: %s" % dest_profile)
        LOGGER.debug("Destination Name: %s" % spoken_dest)
        LOGGER.debug("Destination Address: %s" % dest_addr)
        try:
            spoken_depart_time = message.data.get("Depart")
        except KeyError:
            spoken_depart_time = 'now'
        itinerary_dict = {
            'origin_name': spkn_origin,
            'origin': origin_addr,
            'dest_name': spoken_dest,
            'destination': dest_addr,
            }
        LOGGER.debug("Itinerary:: %s" % itinerary_dict)
        return itinerary_dict

    def __get_address_from_pois(self, profile, poi_type, poi_name):
        address = self.poi_dict[profile][poi_type][poi_name]

    def request_drive_time(self, message, depart_time):
        itinerary = self.build_itinerary(message)
        self.speak_dialog("welcome",
                          data={'destination': itinerary['dest_name'],
                                'origin': itinerary['origin_name']})
        traffic_args = {
            'origin': itinerary['origin'],
            'destination': itinerary['destination'],
            'mode': 'driving',
            'units': self.dist_units
            }
        drive_details = self.maps.traffic(**traffic_args)
        duration_norm = drive_details[0]
        duration_traffic = drive_details[1]
        traffic_time = drive_details[2]
        route_summ = drive_details[3]
        # If traffic greater than 20 minutes, consider traffic heavy
        if traffic_time >= 20:
            LOGGER.debug("Traffic = Heavy")
            self.speak_dialog('traffic.heavy',
                              data={'destination': itinerary['dest_name'],
                                    'trip_time': duration_norm,
                                    'traffic_time': traffic_time})
        # If traffic between 5 and 20 minutes, consider traffic a delay
        elif traffic_time >= 5:
            LOGGER.debug("Traffic = Delay")
            self.speak_dialog('traffic.delay',
                              data={'destination': itinerary['dest_name'],
                                    'trip_time': duration_norm,
                                    'traffic_time': traffic_time})
        else:
            LOGGER.debug("Traffic = Clear")
            self.speak_dialog('traffic.clear',
                              data={'destination': itinerary['dest_name'],
                                    'trip_time': duration_norm})

    def request_drive_time_orig(self, message, depart_time, api_key):
        poi_dict = self.config.get('pois')
        itinerary = self.build_itinerary(message)
        self.speak_dialog("welcome",
                          data={'destination': itinerary['dest_name'],
                                'origin': itinerary['origin_name']})
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

        if response.status_code == requests.codes.ok and \
                response.json()['status'] == "REQUEST_DENIED":
            LOGGER.error(response.json())
            self.speak_dialog('traffic.error.api')

        elif response.status_code == requests.codes.ok:
            LOGGER.debug("API Response: %s" % response)
            routes = response.json()['routes'][0]
            legs = routes['legs'][0]
            # convert time to minutes
            duration_norm = int(legs['duration']['value']/60)
            duration_traffic = int(legs['duration_in_traffic']['value']/60)
            traffic_time = duration_traffic - duration_norm
            # If traffic greater than 20 minutes, consider traffic heavy
            if traffic_time >= 20:
                LOGGER.debug("Traffic = Heavy")
                self.speak_dialog('traffic.heavy',
                                  data={'destination': itinerary['dest_name'],
                                        'trip_time': duration_norm,
                                        'traffic_time': traffic_time})
            # If traffic between 5 and 20 minutes, consider traffic a delay
            elif traffic_time >= 5:
                LOGGER.debug("Traffic = Delay")
                self.speak_dialog('traffic.delay',
                                  data={'destination': itinerary['dest_name'],
                                        'trip_time': duration_norm,
                                        'traffic_time': traffic_time})
            else:
                LOGGER.debug("Traffic = Clear")
                self.speak_dialog('traffic.clear',
                                  data={'destination': itinerary['dest_name'],
                                        'trip_time': duration_norm})

        else:
            LOGGER.error(response.json())

    def request_distance(self, message):
        itinerary = self.build_itinerary(message)
        self.speak_dialog("welcome",
                          data={'destination': itinerary['dest_name'],
                                'origin': itinerary['origin_name']})
        # Places Nearby API
        places_nearby_args = {
            'name': itinerary['destination'],
            'location': itinerary['origin']
            }
        if "OpenNowKeyword" in message.data:
            places_nearby_args['open_now'] = True
        # nearby_places = self.maps.places_nearby(**places_nearby_args)
        # Places API
        places_args = {
            'query': itinerary['destination'],
            'location': itinerary['origin']
            }
        if "OpenNowKeyword" in message.data:
            places_args['open_now'] = True
        places = self.maps.places(**places_args)
        dist_args = {
            'origins': itinerary['origin'],
            'destinations': itinerary['destination'],
            'mode': 'driving',
            'units': self.dist_units
            }
        drive_details = self.maps.distance(**dist_args)
        duration_norm = drive_details[0]
        duration_traffic = drive_details[1]
        traffic_time = drive_details[2]
        # If traffic greater than 20 minutes, consider traffic heavy
        if traffic_time >= 20:
            LOGGER.debug("Traffic = Heavy")
            self.speak_dialog('distance.heavy',
                              data={'destination': itinerary['dest_name'],
                                    'trip_time': duration_norm,
                                    'traffic_time': traffic_time})
        # If traffic between 5 and 20 minutes, consider traffic a delay
        elif traffic_time >= 5:
            LOGGER.debug("Traffic = Delay")
            self.speak_dialog('distance.delay',
                              data={'destination': itinerary['dest_name'],
                                    'trip_time': duration_norm,
                                    'traffic_time': traffic_time})
        else:
            LOGGER.debug("Traffic = Clear")
            self.speak_dialog('distance.clear',
                              data={'destination': itinerary['dest_name'],
                                    'trip_time': duration_norm})

    def __convert_address(self, address):
        address_converted = sub(' ', '+', address)
        return address_converted

    def stop(self):
        # self.speak_dialog('traffic.module.halting')
        # self.process.terminate()
        # self.process.wait()
        pass


def create_skill():
    return TrafficSkill()
