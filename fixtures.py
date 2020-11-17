    # -*- coding: utf-8 -*-
"""
PPMtools fixtures class and associated functions.

Helps PPMtools to establish what different fixtures do, and their associated 
features or limiations.


"""

from PPMtools_units import *

class Event:
    """
    Water usage event class to add to the schedule for each fixture
    note: a note saying what happened, e.g., 'brushed teeth'
    fixture: the fixture for the water usage
    person: individual using the fixture
    times: array representing window of time active (inclusive)
    cold_rate/hot_rate: flow rates for cold and hot water lines
    """
    # TODO: Can this be placed into either the Fixture/Household classes?
    # TODO: Create separate .py file for this class? usage.py/event.py/usage_events.py
    # TODO: Currently appended to the fixture schedule upon generation
    # TODO: Consider storing the fixture name rather than the fixture object
    # TODO: Consider storing the person name rather than the person object
    def __init__(self, note, fixture, person, times, cold_rate, hot_rate):
        self.note = note     
        self.fixture = fixture
        self.person = person
        self.times = times
        self.cold_rate = cold_rate
        self.hot_rate = hot_rate
        

class Fixture:
    """
    Parent class for household fixtures
    """
    def __init__(self, name, max_rate):
        """
        Initialize a fixture
        name: name of Fixture
        max_rate: flow rate of fixture
        initialize schedule, nodes, labels, and flushability
        """
        # TODO: set default max rates for each fixture type?
        self.name = name
        self.max_rate = max_rate
        self.schedule = []
        self.nodes = ['cold', 'hot']
        self.node_labels = [name + 'C', name + 'H']
        self.continuous_flushability = True


    def reset_schedule(self):
        """
        Clear all water usage events for the fixture
        """
        self.schedule = []


    def run_water(self, note, person, times, cold_rel, hot_rel):
        """
        Add a water usage event for the fixture to the fixture schedule
        note: a note saying what happened 'brushed teeth?'
        person: individual using the fixture
        times: array representing window of time active (inclusive)
        hot_rel/cold_rel: percentage of max rate to use
        """
        # TODO: Would this be better by asking for % of max_rate and hot_rel values
        #    instead of cold_rel and hot_rel. It would eliminate the chance of the
        #    user accidentally entering a flow above the max_rate
        if cold_rel + hot_rel > 1:
            print('WARNING: cold + hot rates exceed max rate for ' + self.name)
        cold_rate = cold_rel * self.max_rate
        hot_rate = hot_rel * self.max_rate
        event = Event(note, self, person, times, cold_rate, hot_rate)
        self.schedule.append(event)


    def rinse_pipes(self, start_time, duration, node):
        """
        Add a flushing event for the fixture to the fixture schedule
        start_time: the clock time for the start of flushing
        duration: the length of flushing
        node: the node (hot or cold) to flush
        """
        # TODO: need a method that handles fixtures that cannot be continuously 
        #       flushed or have cycles
        note = 'Flush ' + self.name
        person = 'Flusher'
        if node == 'cold':
            hot_rate = 0
            if self.continuous_flushability == True:
                cold_rate = self.max_rate
            else:
                cold_rate = self.max_rate
        elif node == 'hot':
            cold_rate = 0
            if self.continuous_flushability == True:
                hot_rate = self.max_rate
            else:
                hot_rate = self.max_rate
        times = [start_time, start_time + duration]

        event = Event(note, self, person, times, cold_rate, hot_rate)
        self.schedule.append(event)


    def available_times(self, times):
        """
        Check if the proposed times for the action conflict with the current
            schedule of the fixture. If conflict is found, increment proposed times
            by 1 minute/timestep?? and recheck times.
        """
        # TODO: do we increment one step or one minute (6 steps)
        # TODO: currently returns time immediately prior to another event, okay?
        busy = True
        while busy == True:
            busy = False
            for event in self.schedule:
                # fix_times = event.times
                # if times[0] <= fix_times[-1] and times[-1] >= fix_times[0]:
                start_time, end_time = event.times
                if times[0] <= end_time and times[-1] >= start_time:
                    times = [x + 1 for x in times]
                    busy = True
                    break
        return times



class Dishwasher(Fixture):
    """
    A dishwasher fixture with a single hot node. 
    Default cycle: 2 fill steps (wash and rinse). A fill step takes 1 minutes (60 seconds) 
        to complete. The cycle_volume is split between the two fill steps and then 
        divided by 1 minutes to determine the max_rate
    """
    # TODO: Energy Star assumes a capacity greater than or equal to 8 place settings 
    #       and 6 serving pieces. Use these values to assign run frequency?
    # TODO: add volume at init from input file instead of hard code?
    # TODO: Add method for doing dishes without a dishwasher? not as part of dishwasher?
    def __init__(self, name, cycle_volume):
        super().__init__(name, cycle_volume)
        self.nodes = ['hot']
        self.node_labels = [name +'H']
        self.continuous_flushability = False
        self.cycles = []
        self.volume = cycle_volume
        self.max_rate = self.volume / (2 * 2) # 2: # of fill steps, 1: fill duration


    def run_dishwasher(self, note, person, times):
        """
        Add a dishwasher water usage event for each tub fill in the fixture 
            cycle to the fixture schedule
        note: a note saying what happened 'brushed teeth?'
        person: individual using the fixture
        times: array representing window of time active (inclusive)
        """
        # TODO: remove all other methods (normal_wash, etc.)
        # TODO: remove cycle defintion once it is passed from input file
        # TODO: the cycle should define the duration, not the times object
        duration = times[1] - times[0]
        fill_time = 2 * steps_per_min - 1 
        wait_time = int(duration / 2 - fill_time) + 1
        cycle_steps = [['wash-fill'  , fill_time, self.max_rate],
                        ['wash'      , wait_time, 0],
                        ['rinse-fill', fill_time, self.max_rate],
                        ['rinse'     , wait_time, 0]]
        cold_rate = 0 # dishwasher is hot only
        start_time = times[0]
        for step in cycle_steps:
            step_name = step[0]
            duration_step = step[1]
            hot_rate = step[2]
            end_time = start_time + duration_step
            if end_time > times[1]: end_time = times[1]
            times_step = [start_time, end_time]
            note_step = note + '-' + step_name
            event_step = Event(note_step, self, person, times_step, cold_rate, hot_rate)
            self.schedule.append(event_step)
            start_time = end_time


    def rinse_pipes(self, start_time, duration, node):
        """
        Add a flushing event for the Dishwasher to the fixture schedule.  Runs a 
            dishwasher cycle using hot water.
        start_time: the clock time for the start of flushing
        duration: the length of flushing
        node: the node (hot only) to flush, passed but unused since Dishwasher are 
            hot only
        """
        # TODO: need a method that handles fixtures that cannot be continuously 
        #       flushed or have cycles
        note = 'Flush ' + self.name
        person = 'Flusher'
        times = [start_time, start_time + duration]
        self.run_dishwasher(note, person, times)


    def normal_cycle(self, note, person, times):
        # TODO: Experimental
        """
        Add a dishwasher water usage event for each tub fill in the fixture 
            cycle to the fixture schedule
        normal wash cycle: 2 fills of hot water(wash/rinse), fill volume is 3 gallons
        note: a note saying what happened 'brushed teeth?'
        person: individual using the fixture
        times: array representing window of time active (inclusive)
        """
        cold_rate = 0
        hot_rate = self.max_rate
        duration_fill = self.volume / hot_rate * steps_per_min # fill tub at max rate
        duration_cycle = times[1] - times[0]
        
        # wash use event at start of cycle
        times_wash = [times[0], 
                      times[0] + duration_fill]
        event_wash = Event(note + '-wash', self, person, times_wash, cold_rate, hot_rate)
        self.schedule.append(event_wash)
        
        # rinse use event at halfway point of cycle
        times_rinse = [times[0] + duration_cycle / 2, 
                       times[0] + duration_cycle / 2 + duration_fill]
        event_rinse = Event(note + '-rinse', self, person, times_rinse, cold_rate, hot_rate)
        self.schedule.append(event_rinse)


    def add_cycle(self, cycle_name, steps=[]):
        # TODO: Experimental
        """
        adds a cycle object to the dishwasher, defined in a premise input file
        cycle_name: the name of the cycle 
        steps: a list of steps (name, duration) to add to the cycle, default is empty
        """
        self.cycles.append([cycle_name, steps])


    def add_cycle_step(self, cycle_name, step_name, duration):
        # TODO: Experimental
        """
        adds a step as a list to the dishwasher cycle object, defined in a premise input file
        cycle_name: the name of the cycle to add the step
        step_name: the name of the step
        duration: the duration of the step
        step list: a step name and the step duration in minutes.
        """
        steps = self.cycles[cycle_name][1]
        steps.append([step_name, duration])
        self.cycles[cycle_name][1] = steps


    def run_dishwasher_cycle(self, note, person, times, cycle):
        # TODO: Experimental
        """
        Add a dishwasher water usage event for each tub fill in the fixture 
            cycle to the fixture schedule
        note: a note saying what happened 'brushed teeth?'
        person: individual using the fixture
        times: array representing window of time active (inclusive)
        cycle: the water use cycle from the dishwasher cycle object
        """
        # TODO: remove all other methods (normal_wash, etc.)
        # TODO: remove cycle defintion once it is passed from input file
        # TODO: the cycle should define the duration, not the times object
        cycle = ['normal',[['wash' , 30*steps_per_min],
                           ['rinse', 30*steps_per_min]]]
        cold_rate = 0 # dishwasher is hot only
        hot_rate = self.max_rate
        duration_flow = self.volume / hot_rate
        times_start = times[0]
        steps = cycle[1]
        for step in steps:
            step_name = step[0]
            duration_step = step[1]
            times_step_flow = [times_start, times_start + duration_flow]
            note_step = note + '-' + step_name
            event_step = Event(note_step, self, person, times_step_flow, cold_rate, hot_rate)
            self.schedule.append(event_step)
            times_start += duration_step

        if times_start != times[1]:
            print('The dishwasher cycle length does not match the specified run time.')


class Faucet(Fixture):
    """
    A fixture at a sink with both cold and hot nodes.
    Default max_rate is XXX.
    """
    def __init__(self, name, max_rate):
        super().__init__(name, max_rate)


class Fridge(Fixture):
    """
    A refrigerator fixture with a single cold node that can be used to dispense
        water or make ice with an internal icemaker.
    Default max_rate is XXX.
    Default cycle_volume for making ice is XXX, which takes XXX minutes to complete.
    """
    # TODO: create a make_ice method with a cycle for the icemaker
    # TODO: Add fridge water for drinking water, default or selectable
    def __init__(self, name, max_rate):
        super().__init__(name, max_rate)
        self.nodes = ['cold']
        self.node_labels = [name +'C']

    def make_ice(self):
#        A cycle that includes the water flow period plus the time for the ice
#        to freeze before it can be performed again. Important for the flushing?
        pass


class Humidifier(Fixture):
    """
    A household humidifier fixture with a single cold node.
    Default cycle_volume is XXX (humidifying?), which takes XXX minutes to complete.
    """
    # TODO: Is this a cycle or a continuous flow?
    # TODO: Is this tied to the furnace/fan cycle?
    def __init__(self, name, max_rate):
        super().__init__(name, max_rate)
        self.nodes = ['cold']
        self.node_labels = [name + 'C']
        self.continuous_flushability = False


class SamplePort(Fixture):
    """
    A sampling port fixture with a single cold node for sampling.
    Default cycle_volume is XXX (humidifying?), which takes XXX minutes to complete.
    """
    # TODO: why does this have a special node name?
    def __init__(self, name, max_rate):
        super().__init__(name,max_rate)
        self.nodes = ['samp']
        self.node_labels = [name + '_samp']
        self.continuous_flushability = False


class Shower(Fixture):
    """
    A shower fixture with both cold and hot nodes.
    Default max_rate is XXX.
    """
    def __init__(self, name, max_rate):
        super().__init__(name, max_rate)


class Source(Fixture):
    """
    A special fixture that acts as the source, or water supply, to the home. 
        Has a negative demand in the input file
    Default max_rate is XXX.
    """
    def __init__(self, name, max_rate):
        super().__init__(name, max_rate)
        self.nodes = ['cold']
        self.node_labels = [name + 'C']
        self.continuous_flushability = False


class Spigot(Fixture):
    """
    A hose bib/spigot fixture with a single cold node.
    Default max_rate is XXX.
    """
    def __init__(self, name, max_rate):
        super().__init__(name, max_rate)
        self.nodes = ['cold']
        self.node_labels = [name + 'C']


class Toilet(Fixture):
    """
    A toilet fixture with a single cold node and a single use cycle.
    Default cycle_volume is 1.6 gallon (flush), which takes 1 minute to complete.
    """
    # TODO: add volume at init from input file instead of hard code and use to determine times?
    def __init__(self, name, max_rate):
        super().__init__(name, max_rate)
        self.nodes = ['cold']
        self.node_labels = [name + 'C']
        self.continuous_flushability = False
        self.volume = 1.6 # flush volume
        self.rinse_flush_count = 3


    def flush_toilet(self, person, times):
        """
        Add a toilet flush cycle event for the fixture to the fixture schedule
        person: individual using the fixture
        times: array representing window of time active (inclusive)
        """
        # TODO: always assume the flush takes 1 minute to fill, regardless of size?
        note = 'Toilet Flush ' + self.name
#        duration_fill = self.volume / self.max_rate        # code for fill time based on flush volume
#        times_fill = [times[0], times[0]+duration_fill]    # code for fill time based on flush volume
        times_fill = times
        hot_rate = 0
        cold_rate = self.max_rate
        event = Event(note, self, person, times_fill, cold_rate, hot_rate)
        self.schedule.append(event)


    def rinse_pipes(self, start_time, duration, node):
        """
        Add a flush_toilet event to rinse the pipes going to the Toilet to the 
            fixture schedule. Splits the duration into the number of times the 
            toilet can be flushed, with a maximum of 3 events.
        start_time: the clock time for the start of flushing
        duration: the length of flushing
        node: the node to flush, passed but unused since toilets are cold only
        """
        flush_count = min(self.rinse_flush_count, int(duration / (60/10))) # 60/10 is tss
        duration_flush = int(60 / 10) # 60/10 is tss
        for i in range(1, flush_count+1):
            person = 'Flusher-' + str(i)
            times = [start_time + duration_flush * (i - 1), start_time + duration_flush * i - 1]
            self.flush_toilet(person, times)


class Washer(Fixture):
    """
    A washing machine fixture with both cold and hot nodes. 
    Default cycle: 3 fill steps (wash, rinse, and spin). A step takes 5 minutes to 
        complete. The cycle_volume is split between the three steps and then divided 
        by 5 minutes to determine the max_rate. The wash and rinse steps fill the 
        tub and the spin step is a continuous spray of water. The wash cycle uses 
        the cold/hot settings while the rinse and spin cycles only use cold water.
    """
    # TODO: Energy Star says that a certified washer uses 13 gal per load while a
    #    normal washer uses 23. However, it does not describe how that volume is
    #    split across the cycle steps.
    # TODO: Are cold and hot water flow rates independent?
    # TODO: A washing machine fills slowly compared to its volume. Does the cycle timer start
    #    after the fill finishes?
    # TODO: add water temp settings for cycle steps (cold-cold, warm-cold, hot-cold)
    # TODO: add volumne at init from input file
    def __init__(self, name, cycle_volume):
        super().__init__(name, cycle_volume)
        self.continuous_flushability = False
        self.cycles = []
        self.loadsizes = [['small', 0.333],
                         ['medium', 0.5],
                         ['large', 0.75],
                         ['extra large', 1]]
        self.volume = cycle_volume
        self.max_rate = self.volume / (3 * 5) # 2: # of steps, 1: duration
        

    def run_washer(self, note, person, times, cold_rel, hot_rel):
        """
        Add a washer water usage event for each tub fill in the fixture 
            cycle to the fixture schedule
        note: a note saying what happened 'brushed teeth?'
        person: individual using the fixture
        times: array representing window of time active (inclusive)
        """
        # TODO: remove all other methods (normal_wash, etc.)
        # TODO: remove cycle defintion once it is passed from input file
        # TODO: the cycle should define the duration, not the times object
        duration = times[1]-times[0]
        fill_time = 5 * steps_per_min - 1     # 5 minute fill assumed/cycle
        wait_time = round(duration/3 - fill_time) + 1
        cycle_steps = [['wash-fill'  , fill_time, cold_rel, hot_rel],
                        ['wash'      , wait_time, 0       , 0],
                        ['rinse-fill', fill_time, 1       , 0],
                        ['rinse'     , wait_time, 0       , 0],
                        ['spin-spray', fill_time, 1       , 0],
                        ['spin'      , wait_time, 0       , 0]]
        start_time = times[0]
        for step in cycle_steps:
            step_name = step[0]
            duration_step = step[1]
            cold_rate = step[2] * self.max_rate
            hot_rate = step[3] * self.max_rate
            end_time = start_time + duration_step
            if end_time > times[1]: end_time = times[1]
            times_step = [start_time, end_time]
            note_step = note + '-' + step_name
            event_step = Event(note_step, self, person, times_step, cold_rate, hot_rate)
            self.schedule.append(event_step)
            start_time = end_time


    def rinse_pipes(self, start_time, duration, node):
        """
        Add run_washer events to rinse the pipes going to the Washer to the 
            fixture schedule. Runs a washer cycle using both hot and cold water 
            to clear both pipes in a single event.
        start_time: the clock time for the start of flushing
        duration: the length of flushing
        node: the node (hot or cold) to flush, passed but unused since both nodes are 
            included in this event. The nodes are combined in the flush procedure.
        """
        note = 'Flush ' + self.name
        person = 'Flusher'
        times = [start_time, start_time + duration]
        cold_rel = 0.5
        hot_rel = 0.5
        self.run_washer(note, person, times, cold_rel, hot_rel)


    def add_cycle(self, cycle_name, steps=[]):
        # TODO: Experimental
        """
        adds a washer cycle object, defined in a premise input file
        cycle object: a cycle name and a list of the steps in the cycle,
        """
        self.cycles.append([cycle_name, steps])

    def add_cycle_step(self, cycle_name, step_name, fill_cont, temp, duration):
        # TODO: Experimental
        """
        adds a step as a list to a washer cycle object, defined in a premise input file
        step list: a step name, whether the step is a single fill or continuous 
            flow, the temperature of the water (hot, warm, cold), and the step 
            duration in minutes.
        """
        steps = self.cycles[cycle_name][1]
        steps.append([step_name, fill_cont, temp, duration])
        self.cycles[cycle_name][1] = steps


    def run_washer_cycle(self, note, person, times, cycle, loadsize):
        # TODO: Experimental
        """
        Add a washer water usage event for each tub fill in the fixture 
            cycle to the fixture schedule
        note: a note saying what happened 'brushed teeth?'
        person: individual using the fixture
        times: array representing window of time active (inclusive)
        cycle: a list of steps describing flow during the cycle
        loadsize: the size of the load to run, determines fill percentage of tub
        """
        #TODO: Assumes maxrate during continuous flow. correct?
        cycle = ['normal', [['wash', 'fill', 'hot', 15*steps_per_min],
                            ['rinse-fill', 'fill', 'cold', 10*steps_per_min],
                            ['rinse-spin', 'continuous', 'cold', 10*steps_per_min]]] 
                            # passed from the premise input file
        self.cycles.append(cycle)
        times_start = times[0]
        for size, fill_precent in self.loadsizes:
            if size == loadsize:
                load_volume = self.volume * fill_precent
        steps = self.cycles[0]
        for step in steps:
            note_step = note + '-' + step[0]
            if step[1] == 'fill':
                duration_flow = round(load_volume / self.max_rate)
            elif step[1] == 'continuous':
                duration_flow = step[3] 
            times_step = [times_start, times_start + duration_flow]

            if step[2] == 'cold':
                cold_rate = self.max_rate
                hot_rate = 0
            elif step[2] == 'warm':
                cold_rate = self.max_rate / 2
                hot_rate = self.max_rate / 2
            elif step[2] == 'hot':
                cold_rate = 0
                hot_rate = self.max_rate

            event_step = Event(note_step, self, person, times_step, cold_rate, hot_rate)
            self.schedule.append(event_step)
            times_start += step[3] # move the start time to the end of the current step