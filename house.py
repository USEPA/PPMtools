# -*- coding: utf-8 -*-
"""
PPMtools household class and associated functions.

Helps PPMtools to establish the household, to which residents, fixture, and 
water usage events are added


"""

import fixtures
import copy

class Household:
    """
    Household class for storing residents, fixtures, and water usage events
    """
    def __init__(self, name, model):
        """
        Initialize the household, populate with fixtures and residents
        name: name of the household
        model: list of fixtures containing fixture type, name, and max rate
        """
        # TODO: convert name to str at init?
        # TODO: store model object in the household object (i.e. self.model)? 
        self.name = name
        self.fixtures = []
        self.residents = []
        self.events = []
        self.init_fixture_lists(model)
        self.event_list = []
        
    def _deepcopy_(self):
        """
        Create a distinct copy of the household class object.
        """
        home2 = copy.deepcopy(self)
        
        return home2
    
    def init_fixture_lists(self, model):
        """
        Initialize the fixture objects in the household 
        model: list of fixtures containing fixture type, name, and max rate
        """
        self.faucets = []
        self.showers = []
        self.toilets = []
        self.spigots = []
        self.fridges = []
        self.dishwashers = []
        self.washers = []
        self.humidifiers = []
        self.sampleports = []
        self.source = []
        for fix in model:
            fix_type = fix[0].lower()       # should be a string, makes it lower case
            fix_name = str(fix[1])          # Fixture name
                                            # should be related to node name 
                                            # Example:
                                            # nodes F2C and F2H are associated 
                                            # with fixture F2 
            fix_max_rate = fix[2]           # max flow rate, currently gal/min
            
            if fix_type == 'faucet':
                fix_add = fixtures.Faucet(fix_name, fix_max_rate)
                self.faucets.append(fix_add)
            elif fix_type == 'shower':
                fix_add = fixtures.Shower(fix_name, fix_max_rate)
                self.showers.append(fix_add)
            elif fix_type == 'toilet':
                fix_add = fixtures.Toilet(fix_name, fix_max_rate)
                self.toilets.append(fix_add)
            elif fix_type == 'spigot':
                fix_add = fixtures.Spigot(fix_name, fix_max_rate)
                self.spigots.append(fix_add)
            elif fix_type == 'fridge':
                fix_add = fixtures.Fridge(fix_name, fix_max_rate)
                self.fridges.append(fix_add)
            elif fix_type == 'dishwasher':
                fix_add = fixtures.Dishwasher(fix_name, fix_max_rate)
                self.dishwashers.append(fix_add)
            elif fix_type == 'washer':
                fix_add = fixtures.Washer(fix_name, fix_max_rate)
                self.washers.append(fix_add)
            elif fix_type == 'humidifier':
                fix_add = fixtures.Humidifier(fix_name, fix_max_rate)
                self.humidifiers.append(fix_add)
            elif fix_type == 'sampleport' or fix_type == 'hws':
                # these are special class sample ports, for experimental use only
                fix_add = fixtures.SamplePort(fix_name, fix_max_rate)
                self.sampleports.append(fix_add)
            else:
                print('Error processing fixture type: Empty fixture added')
                fix_add = []
    
            self.fixtures.append(fix_add)

        # add a water source with large flow rate to supply water to the house 
        fix_add = fixtures.Source('Source', 1000.)
        self.source.append(fix_add)
        self.fixtures.append(fix_add)


    def simulate_usage(self, week_long):
        """
        Simulate water usage for each resident over the defined schedule(week_long)
        week_long: the schedule of days to simulate water usage
        """
        for day_of_week, day in enumerate(week_long):
            for person in self.residents:
                person.do_routine(day_of_week)
        self.build_event_list()


    def build_event_list(self):
        """
        Add all events stored in the fixture schedules to the household event list
        """
        # TODO: Should this be a user-accessible method or hidden (_build_event_list)?
        # TODO: Consider populating this structure at simulation time instead
        # TODO: Does the event need to be stored in two places (houehold.events and fixture.schedule)?
        # TODO: Have this create and store the object that PPMtools extract_event_list() already does
        # TODO: Can event_list replace events, they seem redundant?
        for fix in self.fixtures:
            if fix.schedule:
                self.events.extend(fix.schedule)
        
        # moving PPMtools.extract_events_list here
        
        for event in self.events:
            # creates more human readable list, used elsewhere
            # TODO: False is currently placeholder. Could be removed, TODO
            if type(event.person) == str:
                name = event.person
            else:
                name = event.person.name
            self.event_list.append([event.times,
                                    event.fixture.name,
                                    name,
                                    event.hot_rate,
                                    event.cold_rate,
                                    event.note,
                                    ])
        
                