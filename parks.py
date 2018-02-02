import requests
import json
import sys
from datetime import datetime, timedelta
from auth import getHeaders


park_ids = json.loads(requests.get("https://scaratozzolo.github.io/MouseTools/park_ids.json").content)

class Park(object):

    def __init__(self, id = None, park_name = None):
        """
        Constructor Function
        Gets all park data available and stores various elements into variables.
        id and park_value are both optional, but you must pass at least one of them. The argument must be a string.
        """

        try:
            """Making sure id and park_name are not null, are strings, and exist"""
            if id == None and park_name == None:
                raise ValueError
            elif id != None and type(id) != str:
                raise TypeError
            elif park_name != None and type(park_name) != str:
                raise TypeError


            if park_name != None:
                id = park_ids[park_name] #raises KeyError if park_name doesn't exist

            found = False
            for park in park_ids:
                if id == park_ids[park]:
                    self.__park_name = park
                    found = True
                    break
            if found == False:
                raise KeyError


        except KeyError:
            print('That park or ID is not available. Current options are:')
            for park in park_ids:
                print('{}:{}'.format(park, park_ids[park]))
            sys.exit()
        except ValueError:
            print('Park object expects an id value or park_name value. Must be passed as string.\n Usage: Park(id = None, park_name = None)')
            sys.exit()
        except TypeError:
            print('Park object expects a string argument.')
            sys.exit()

        self.__id = id

        s = requests.get("https://api.wdpro.disney.go.com/facility-service/theme-parks/{}".format(self.__id), headers=getHeaders())
        self.__data = json.loads(s.content)

        links = {}
        for link in self.__data['links']:
            links[link] = self.__data['links'][link]['href']
        self.__links = json.dumps(links)

        self.__long_id = self.__data['id']      #id;entityType=
        self.__type = self.__data['type']
        self.__content_type = self.__data['contentType']
        self.__sub_type = self.__data['subType']
        #advisories may update even when everything else doesn't. maybe create a seperate request to the data to get updated advisories
        self.__advisories = self.__data['advisories']
        self.__weblink = self.__data['webLinks']['wdwDetail']['href']  #check if other parks have multiple. If they do create array or json

    def getParkIDS(self):
        return park_ids

    def getLinks(self):
        """
        Gets all the available links that reference other park data. Returns the links in json {name:link}.

        Links gathered:
        - busStops
        - waitTimes
        - characterAppearances
        - standardTicketProduct
        - entertainments
        - scheduleMax
        - trainStations
        - schedule
        - ancestorResortArea
        - ancestorThemePark
        - self
        - boatLaunches
        - ancestorDestination
        - monorailStations
        """

        return self.__links

    def getTodayParkHours(self):
        """
        Gets the park hours and returns them as a datetime object.
        Returns the park hours in the following order: operating open, operating close, Extra Magic open, Extra Magic close.
        Extra Magic hours will return None if there are none for today.
        """

        s = requests.get("https://api.wdpro.disney.go.com/facility-service/schedules/{}?days=1".format(self.__id), headers=getHeaders())
        data = json.loads(s.content)

        YEAR = str(datetime.today().year)
        MONTH, DAY = self.__formatDate(str(datetime.today().month), str(datetime.today().day))

        operating_hours_start = None
        operating_hours_end = None
        extra_hours_start = None
        extra_hours_end = None

        for i in range(len(data['schedules'])):
            if data['schedules'][i]['date'] == '{}-{}-{}'.format(YEAR, MONTH, DAY):
                if data['schedules'][i]['type'] == 'Operating':
                    operating_hours_start = datetime(int(YEAR), int(MONTH), int(DAY), int(data['schedules'][i]['startTime'][0:2]), int(data['schedules'][i]['startTime'][3:5]))
                    operating_hours_end = datetime(int(YEAR), int(MONTH), int(DAY), int(data['schedules'][i]['endTime'][0:2]), int(data['schedules'][i]['endTime'][3:5]))

                if data['schedules'][i]['type'] == 'Extra Magic Hours':
                    extra_hours_start = datetime(int(YEAR), int(MONTH), int(DAY), int(data['schedules'][i]['startTime'][0:2]), int(data['schedules'][i]['startTime'][3:5]))
                    extra_hours_end = datetime(int(YEAR), int(MONTH), int(DAY), int(data['schedules'][i]['endTime'][0:2]), int(data['schedules'][i]['endTime'][3:5]))

        return operating_hours_start, operating_hours_end, extra_hours_start, extra_hours_end

    def getParkAdvisories(self):
        """
        Gets all the advisories for the park and returns them in json: {id:advisory}.
        May take some time because it has to go to every link for each advisory.
        """

        print('May take some time. {} advisories to parse.'.format(len(self.__advisories)))
        advisories = {}

        for i in range(len(self.__advisories)):
            s = requests.get(self.__advisories[i]['links']['self']['href'], headers=getHeaders())
            data = json.loads(s.content)
            advisories[data['id']] = data['name'].replace(u"\u2019", "'").replace(u"\u2013", "-")

        advisories = json.dumps(advisories)

        return advisories

    def getCurrentWaitTimes(self):
        """
        Gets all current wait times for the park. Returns them in json {park:time in minutes}. May take some time as it goes through all attractions.
        """

        s = requests.get("https://api.wdpro.disney.go.com/facility-service/theme-parks/{}/wait-times".format(self.__id), headers=getHeaders())
        loaded_times = json.loads(s.content)

        times = {}
        for i in range(len(loaded_times['entries'])):
            if 'postedWaitMinutes' in loaded_times['entries'][i]['waitTime']:
                times[loaded_times['entries'][i]['name']] = loaded_times['entries'][i]['waitTime']['postedWaitMinutes']

        json_times = json.dumps(times)
        return json_times


    def __formatDate(self, month, day):
        """
        Formats month and day into proper format
        """
        if len(month) < 2:
            month = '0'+month
        if len(day) < 2:
            day = '0'+day
        return month, day


    def __str__(self):
        return 'Park object for {}'.format(self.park_name)