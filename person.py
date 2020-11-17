# -*- coding: utf-8 -*-
"""
PPMtools: 
    Class and Functions associated with people and their activities
"""

import random
from PPMtools_units import *


def schedule_setup(schedules={}):
    """
    Convert time periods during a day from hours to lists of timesteps
    schedules: a dictionary of the time periods during a day in hours
    """
    # TODO: rename schedules to something more indicative of what it represents
    # TODO: calc steps_per_min directly from tss
    # TODO: add as a class method under house or resident?
    # TODO: the schedules dictionary could be put into the input file
    # TODO: each resident could have their own schedules dictionary for when they are home
    
    schedules = {'all_day': [[0, 24]],
                 'day':     [[8, 16]],
                 'day2':    [[6, 22]],
                 'AM':      [[6, 8]],
                 'PM':      [[17, 22]],
                 'AM_PM':   [[6, 8], [17, 22]]}
    
    schedules_steps = dict.fromkeys(schedules,[])
    for key in schedules.keys():
        steps = []
        for period in schedules[key]:
            steps_start = period[0] * min_per_hr * steps_per_min
            steps_end   = period[1] * min_per_hr * steps_per_min
            steps.extend([x for x in range(steps_start, steps_end)])
        
        schedules_steps[key]= steps

    return schedules_steps
   

class Resident:
    """
    Class for residents of the household
    """
    # TODO: consider linking activities together
    def __init__(self, name, household, routine):
        """
        Initialize a person
        name: name of resident
        household: flow rate of fixture
        routine: the name, schedule, frequency and duration of each action a person
                performs each day of the week
        intitialize the exposure list and action dictionary
        """
        self.name = name
        self.myHouse = household
        self.routine = routine    
        self.exposure_list = []
        self.action_dict = {'shower':  self.take_shower,
                           'drink':    self.drink_water,
                           'teeth':    self.brush_teeth,
                           'hands':    self.wash_hands,
                           'toilet':   self.use_toilet,
                           'food':     self.make_food,
                           'sample':   self.take_sample,
                           'laundry':  self.wash_clothes,
                           'lawn':     self.water_lawn,
                           'dishes':   self.wash_dishes,
                           'ice':      self.make_ice,
                           'humidify': self.humidify}
                            

    def drink_water(self, times):
        # TODO: Remove "busy" fixtures rather than delaying the use of the fixture?
        if not self.myHouse.faucets:
            print(self.name + " wants to take a drink, but there aren't any faucets!")        
        fixture = random.choice(self.myHouse.faucets)
        times = fixture.available_times(times)
        fixture.run_water('Drinking', self, times, 1, 0)
        
        
    def take_shower(self, times):
        if not self.myHouse.showers:
            print(self.name + " wants to take a shower, but there aren't any!")
        fixture = random.choice(self.myHouse.showers)
        times = fixture.available_times(times)
        fixture.run_water('Shower', self, times, 0.2, 0.8)

    
    def brush_teeth(self, times):
        if not self.myHouse.faucets:
            print(self.name + " wants to take a brush some teeth, but there aren't any faucets!")           
        fixture = random.choice(self.myHouse.faucets)
        times = fixture.available_times(times)
        fixture.run_water('Brush Teeth', self, times, 1, 0)
    
    
    def use_toilet(self, times):
        if not self.myHouse.toilets:
            print(self.name + " has to go, but there aren't any toilets!")   
        fixture = random.choice(self.myHouse.toilets)
        times = fixture.available_times(times)
        fixture.flush_toilet(self, times)
    
    
    def wash_hands(self, times):
        if not self.myHouse.faucets:
            print(self.name + " wants to wash hands, but there aren't any faucets!")         
        fixture = random.choice(self.myHouse.faucets)
        times = fixture.available_times(times)
        fixture.run_water('Wash Hands', self, times, 0.5, 0.5)
        

    def wash_clothes(self, times):
        if not self.myHouse.washers:
            print(self.name+" wants to wash clothes, but washer is in use.")
        fixture = random.choice(self.myHouse.washers)
        times = fixture.available_times(times)
        fixture.run_washer('Wash Clothes',self, times, 0.5, 0.5)
        
        
    def water_lawn(self, times):
        if not self.myHouse.spigots:
            print(self.name+" already watering lawn.")
        fixture = random.choice(self.myHouse.spigots)
        times = fixture.available_times(times)
        fixture.run_water('Water Lawn', self, times, 1., 0.)
        
        
    def wash_dishes(self, times):
        if not self.myHouse.dishwashers:
            print(self.name+" already washing dishes.")
        fixture = random.choice(self.myHouse.dishwashers)
        times = fixture.available_times(times)
        fixture.run_dishwasher('Dishes', self, times)


    def make_ice(self, times):
        if not self.myHouse.fridges:
            print(self.name+" Fridge in use.")
        fixture = random.choice(self.myHouse.fridges)
        times = fixture.available_times(times)
        fixture.run_water('Ice', self, times,1.,0., True)
        
        
    def humidify(self, times):
        if not self.myHouse.humidifiers:
            print(self.name+" Humidifier is already in use.")
        fixture = random.choice(self.myHouse.humidifiers)
        times = fixture.available_times(times)
        fixture.run_water('Humidify', self, times, 1., 0.)


    def flush_fixture(self, times, fixture, node):
        '''
        Flush a fixture following a contamination incident
        '''
        # TODO: is this method needed under Resident?
        if not self.myHouse.fixtures:
            print(self.name + ' could not find a fixture.')
        times = fixture.available_times(times)
        fixture.rinse_pipes(times[0], times[-1]-times[0], node)


    def make_food(self, times):   
        """
        Consider making the first sink always the kitchen sink
        also, let's include any hand washing as part of making food here. ???
        """
        # TODO: Not implemented
        print('make food not implemented, yet')


    def do_dishes(self, times):
        """
        TBA
        """
        # TODO: Not implemented
        pass
        
        
    def do_laundry(self, times):
        """
        TBA
        """
        # TODO: Not implemented
        pass  


    def take_sample(self, times):
        """
        TBA
        """
        # TODO: Not implemented
        pass


    def do_routine(self, day_of_week):
        """
        Perform the actions in the person's routine for the given day of the week
        day_of_week: the day of the week for the routine
        """
        queue = self.build_queue(day_of_week)
        for action, times in queue:
            self.action_dict[action](times)


    def build_queue(self, day_of_week):
        """
        Build a list of actions from the routine and assign the start/end times
        day_of_week: the day of the week for the routine
        """
        queue = []
        schedules = schedule_setup()
        for task in self.routine[day_of_week]:
            name = task[0]
            sched = task[1]
            frequency = task[2]
            duration = task[3]
            for n in range(frequency):
                # ensure the event ends within the scheduled time period of the day
                end_time = schedules[sched][0] + \
                           day_of_week * steps_per_day - 1
                while end_time - day_of_week * steps_per_day not in schedules[sched]:
                    start_time = random.choice(schedules[sched]) + day_of_week * steps_per_day
                    end_time = start_time + duration - 1
                queue.append((name, [start_time, end_time]))
        return queue