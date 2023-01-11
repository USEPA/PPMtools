# -*- coding: utf-8 -*-
"""
PPMtools

Contains functions used for generating and analyzing Monte Carlo simulations
for Premise Pluming Models.

This tool relies on WNTR to maintain EPANET network models and handle input/output files.
*** To get WNTR refer to github.com/usepa/wntr or run 'pip install wntr'
    PPMtools has been tested with WNTR 0.2.3




"""
import warnings
warnings.simplefilter("ignore")

import wntr
import pandas as pd
import numpy as np

# import sys
# import subprocess
# import time
import multiprocessing as mp
import os
import _pickle as cPickle
import itertools

import house
import person
from PPMtools_units import *



# =============================================================================
# Monte Carlo Tools
# =============================================================================
def monte_carlo_setup(wn, fixture_info, routine, changes_obj, main_dir,
                      num_trials=1, PPM_name='PPM_runs', 
                      household_routine=False):
    available = []
  
    if type(fixture_info) == list:
        fixture_info = {'single case': fixture_info}
    
    if type(routine) == list:
        print('Assuming weekday routine, and repeating that for all days')
        routine = {'weekday': routine, 'weekend': routine, 
                   'modeled week': ['wd','wd','wd','wd','wd','we','we']}
    
    if 'modeled week' in routine.keys():
        days_in_week = routine['modeled week']
    else:
        print('No week information provided\Assuming 7 day week, beginning Monday')
        days_in_week = ['wd','wd','wd','wd','wd','we','we']
    
    weekdayroutine = routine['weekday'] # TODO: need error handling if this doesn't exist
    weekendroutine = routine['weekend'] # TODO: need error handling if this doesn't exist
    
    # Create changes matrix
    if 'num people' in changes_obj.keys():
        loop1 = changes_obj['num people']
    else:
        loop1 = [2]               # default to 2 person case, if not provided.
    loop2 = list(fixture_info.keys())   # loop over additional use cases
    # Set up any additional changes
    loop3 = list(itertools.product(changes_obj['hwh volume'],
                                   changes_obj['pipe diam'],
                                   changes_obj['pipe scaling']
                                   ))
    
    combo_folders = list(itertools.product (loop1,
                                            loop2,
                                            changes_obj['hwh volume'],
                                            changes_obj['pipe diam'],
                                            changes_obj['pipe scaling']
                                            ))
    
    # Creates necessary folder structure for file storage
    for item in combo_folders:
        house_base = PPM_name.replace(' ','_') + '/'
        num_people = repr(int(item[0])) + '_People/'
        flow_type  = item[1].replace(' ','_') + '/'
        hwh_size   = repr(round(item[2])) + '_gal/'
        pipe_diam  = repr(round(item[3],4)).replace('.','-') + '_in/'
        pipe_scale = repr(round(item[4],3)).replace('.','-') + 'x/'
        
        folder_string = house_base + num_people + flow_type + hwh_size + \
                        pipe_diam + pipe_scale
        
        full_folder_path = main_dir.replace('\\', '/') + '/' + folder_string
        os.makedirs(full_folder_path, exist_ok=True)
    
    # Store some network characteristics that don't change
    orig_lengths = {}
    for pipe in wn.link_name_list:
        orig_lengths[pipe] = wn.get_link(pipe).length
    hwh_name = wn.tank_name_list[0]
    xs_area = np.pi * (wn.get_node(hwh_name).diameter/2.)**2 # m**2, cross sectional area of tank
    
    # Setup Scaling Factors
    scaling = {}
    job_ref = loop2[0]     # stores which job 
    for item in loop2:
        scaling[item] = {}
        for fixID in range(len(fixture_info[item])):
            fixture_name = fixture_info[item][fixID][1]
            ref_fix = fixture_info[job_ref][fixID][2]
            curr_fix = fixture_info[item][fixID][2]
            scaling[item][fixture_name] = curr_fix / ref_fix
    
    root_folder = main_dir.replace('\\','/') + '/' + PPM_name.replace(' ','_') + '/'           
    
    for num_people in loop1:
        ref_available = False           # flag, will recalculate if False
        event_dict    = {}              # create storage objects
        patt_dict     = {}
        for flow_type in loop2:
            base_folder = root_folder +\
                          repr(int(num_people)) + '_People/' +\
                          flow_type.replace(' ','_') + '/'
            if not ref_available:
                fix_info = fixture_info[job_ref]
                home     = house.Household(PPM_name + '-P' + str(num_people), 
                                           fix_info)
                people = []
                for p in range(1, num_people+1):
                    resident = 'P'+str(p)   
                    routine_obj = week_routine_person(days_in_week, 
                                                      weekdayroutine, 
                                                      weekendroutine)
                    people.append(person.Resident(resident, home, routine_obj))
                if household_routine != False:
                    # house actions are a fictitous person named 'Home'
                    routine_obj = week_routine_home(days_in_week, 
                                                    household_routine)
                    people.append(person.Resident('Home', home, routine_obj))
                home.residents = people
                
                base_name = home.name + '_model'
                for trial in range(num_trials):
                    trial_ID = base_name + '-' + str(trial)
                    tmp_home = home._deepcopy_() # reset home for next trial
                    tmp_home.simulate_usage(days_in_week)
                    patt_dict[trial_ID] = build_pattern_dict(wn, tmp_home)
                    event_list = tmp_home.event_list  
                    event_dict[trial_ID] = event_list
                ref_available = True     # Flags that jobs have been stored
                
                patt_xref = {}
                pattern_list = list(patt_dict[trial_ID].keys())
                pattern_list.remove('SourceCP')
                for fixID in range(len(fixture_info[job_ref])):
                    fix_name = fixture_info[job_ref][fixID][1]
                    patt_xref[fix_name] = {}
                    # print(fix_name)
                    
                    patt_xref[fix_name]['hot'] = [i for i in pattern_list 
                                                  if (fix_name + 'H') in i ]
                    patt_xref[fix_name]['cold'] = [i for i in pattern_list 
                                                   if (fix_name + 'C') in i ]
                
            else:                        # use scaling to rework pattern
                for trial_ID in event_dict.keys():
                    for event in range(len(event_dict[trial_ID])):
                        fix_name = event_dict[trial_ID][event][1]
                        scale = scaling[flow_type][fix_name]
                        if scale != 1:
                            event_dict[trial_ID][event][3] *= scale
                            event_dict[trial_ID][event][4] *= scale
                    
                    for fix_name in patt_xref.keys():
                        scale = scaling[flow_type][fix_name]
                        if scale != 1:
                            pattC_name = patt_xref[fix_name]['cold']
                            pattH_name = patt_xref[fix_name]['hot']
                            if len(pattC_name) > 0:
                                coldP = patt_dict[trial_ID][pattC_name[0]]
                                coldP = list(np.array(coldP) * scale)
                                patt_dict[trial_ID][pattC_name[0]] = coldP
                            if len(pattH_name) > 0:
                                hotP = patt_dict[trial_ID][pattH_name[0]]
                                hotP = list(np.array(hotP) * scale)
                                patt_dict[trial_ID][pattH_name[0]] = hotP
                    
                    df = pd.DataFrame.from_dict(patt_dict[trial_ID])
                    cols = df.columns.drop('SourceCP')
                    source_demand = df[cols].sum(axis='columns').values
                    patt_dict[trial_ID]['SourceCP'] = list(source_demand)
            
            cPickle.dump(event_dict, open(base_folder + base_name + '.pickle',
                                          'wb'))
            
            
            for trial in loop3:
                sub_base = repr(round(trial[0])) + '_gal/' +\
                           repr(round(trial[1],4)).replace('.','-') + '_in/' +\
                           repr(round(trial[2],3)).replace('.','-') + 'x/'
                
                # Hot water heater resize if needed           
                hwh_vol = trial[0] * m3_per_gal              # m**3     
                hwh_height = hwh_vol / xs_area               # m
                wn.get_node(hwh_name).init_level = hwh_height * 1.
                wn.get_node(hwh_name).max_level = np.ceil(hwh_height * 1e6)/1e6
                # Pipe diameter reset if neede
                pipe_diam = trial[1] * m_per_inch            # m
                pipe_scaling = trial[2]                      # unitless
                for pipe in wn.link_name_list:
                    wn.get_link(pipe).length = orig_lengths[pipe] * pipe_scaling
                    wn.get_link(pipe).diameter = pipe_diam * 1.
                    
                for trial_ID in event_dict.keys():
                    inp_file = trial_ID + '.inp'
                    '''
                    Stores available files: Used for running/analyzing files
                    column1: Trial ID name
                    column2: Where the pickled event_list is stored
                    column3: Where the actual inp file is stored
                    column4: INP file name
                    '''
                    available.append([trial_ID, 
                                      base_folder + base_name + '.pickle',
                                      base_folder + sub_base, 
                                      inp_file])
                    
                    update_patterns(wn, 
                                    patt_dict[trial_ID], 
                                    base_folder+sub_base+inp_file)
                    print('Created: '+ base_folder + sub_base + inp_file)
                    
    cPickle.dump(available, open(root_folder+'available.pickle','wb'))
                    

    return available, patt_dict   

# =============================================================================
# Pattern functions
# =============================================================================
def build_pattern_dict(wn, household):
    '''
    Build the patterns for each node in the household for the .inp file 
    {'patname':[pattern]}
    wn: water network model
    household: household object
    '''
    # TODO: how to handle if a pattern does exist or an extra pattern exists
    # TODO: get rid of the events list in either the household or fixture objects?   
    TOT_LENGTH = wn.options.time.duration / wn.options.time.pattern_timestep
    patterns = wn.pattern_name_list

    # Check that all needed patterns exist
    for fix in household.fixtures:
        for node_name in fix.node_labels:
            if not node_name + 'P' in patterns:
                patterns.append(node_name + 'P')

    temp_patt = {}
    for i in patterns:
        temp_patt[i] = [0] * int(TOT_LENGTH)
    
    fix_source = household.source[0]
    patt_source_name = fix_source.name + 'CP'
    test = 0
    for fix in household.fixtures:
        if fix != fix_source:
            for event in fix.schedule:
                test+=1
                start = int(event.times[0])
                end = int(event.times[1])
                if end > TOT_LENGTH: end = TOT_LENGTH
                idx = range(int(start), int(end + 1))
                cold_rate = event.cold_rate
                hot_rate = event.hot_rate
                if cold_rate != 0:
                    patt_name = fix.name + 'CP'
                    for j in idx:
                        temp_patt[patt_name][j] = cold_rate
                        temp_patt[patt_source_name][j] += cold_rate
                if hot_rate != 0:
                    patt_name = fix.name + 'HP'
                    for j in idx:
                        temp_patt[patt_name][j] = hot_rate
                        temp_patt[patt_source_name][j] += hot_rate
    
    return temp_patt

def update_patterns(wntr_obj, patterns, outfile):
    '''
    Update the patterns in the water network
    wntr_obj: the wntr object updated with anything other than patterns
    patterns: pattern dictionary {'patname':[pattern]}
    outfile: name of the output file ('.inp')
    '''
    # TODO: any advantage/disadvantage to deleting all patterns and write new ones?
    # TODO: if an old pattern is left in, will it cause problems?
    curr_patt = wntr_obj.pattern_name_list
        
    for patt in patterns.keys():
        if patt in curr_patt:
            wntr_obj.patterns[patt].multipliers = np.array(patterns[patt])
        else:
            wntr_obj.add_pattern(patt, patterns[patt])
    
    wntr.network.io.write_inpfile(wntr_obj, outfile, units='GPM')
    # wntr_obj.write_inpfile(outfile, units='GPM')
    

# =============================================================================
# Data summary functions
# =============================================================================
def by_user_dataframe(summary_pd, qual_type='chem'):
    '''
    summary_pd: dataframe of summary results
    qual_type: 'chem' or 'age', designates what type of WQ simulation was run
    
    '''
    datastruct = ['MassCold','VolumeCold','AveConcCold','MassHot',
                  'VolumeHot','AveConcHot','UseType','Fixture']
    
    resname = list(set([summary_pd['patternInfo'][x][2] 
                        for x in range(len(summary_pd['patternInfo']))]))
    
    level1 = [x for x in resname for y in datastruct]
    level2 = datastruct*len(resname)
    
    tuples = list(zip(level1, level2))
    col_val = pd.MultiIndex.from_tuples(tuples, names=['User','Data'])
        
    tmp_store = []
    
    for i in range(len(summary_pd.index)):
        j = summary_pd.loc[i]
        k = j['patternInfo']
        res = k[2]
        res_idx = resname.index(res)
        fix = k[1]
        use = k[5]
        if 'Sample' in use or 'sample' in use:
            use = 'Sample'
        cMtmp = j['coldMass']
        cVtmp = j['coldVolume']
        hMtmp = j['hotMass']
        hVtmp = j['hotVolume']
        avCtmp = 0.
        avHtmp = 0.
        if qual_type.lower() == 'chem':
            if cVtmp > 0.:
                avCtmp = cMtmp / cVtmp
            if hVtmp > 0.:
                avHtmp = hMtmp / hVtmp
        elif qual_type.lower() == 'age': 
            # Age considers only average, not mass/volume
            # Age returned in hours, wntr returns as seconds
            if cVtmp > 0.:
                avCtmp = np.mean(j['coldConc'])/sec_per_hr
            if hVtmp > 0.:
                avHtmp = np.mean(j['hotConc'])/sec_per_hr
        else:
            print('Error: qual_type supplied does not match chem or age')
        
        line = res_idx*[0,0,0,0,0,0,0,0]+\
               [cMtmp, cVtmp, avCtmp, hMtmp, hVtmp, avHtmp, use, fix] +\
               (len(resname)-(res_idx+1))*[0,0,0,0,0,0,0,0]
        tmp_store.append(line)

    break_down = pd.DataFrame(tmp_store, 
                              index=range(len(summary_pd)), 
                              columns=col_val)
    
    return break_down

def generate_summary(use_list, conc_pd, timestep, shift=0, qual_type='chem'):
    '''
    use_list: provides a list of usages, categorized by type, flow, etc
    conc_pd:  dataframe that stores the concentrations by fixture/faucet
    timestep: length of pattern timestep
    shift:    number of days to shift analysis
    
    '''
    results_table = []

    for i in use_list:
        # shifts the analysis by 1 full day 
        start = i[0][0] + shift * sec_per_day/timestep 
        # shifts the analysis by 1 full day
        end = i[0][1] + shift * sec_per_day/timestep 
        #adjust for reporting timestep 
        st = start * timestep + 1           
        length = (end - start) + 1 #+1 makes the 
        en = st + length * timestep # + 1 #+1 here?
        rng = np.arange(st, en)
        # set the total mass variable, and concentration lists
        cold_sum = 0.0
        hot_sum = 0.0
        hot_temp = []
        cold_temp = []
       
        if i[4] != None:
            vol_c_used = i[4] * gpm_to_Lps*float(length)*float(timestep)*1.
            vol_c_rate = i[4] * gpm_to_Lps
        else:
            vol_c_used = 0.
            vol_c_rate = 0.
            
        if i[3] != None:
            vol_h_used = i[3] * gpm_to_Lps*float(length)*float(timestep)*1.
            vol_h_rate = i[3] * gpm_to_Lps
        else:
            vol_h_used = 0.
            vol_h_rate = 0.     
        if qual_type.lower() == 'age':
            vol_c_rate = 1.
            vol_h_rate = 1.
        
        if vol_h_used + vol_c_used > 0:             
            # Sample ports and Hot water Heater nodes  
            # These are special cases, used for experimental rig
            if i[1] == 'SPS' or i[1] == 'HWS':
                if i[1] == 'SPS':
                    usename = i[1]
                    cold_temp = list(conc_pd.loc[usename][rng]) #### revisit
                    cold_sum = (conc_pd.loc[usename][rng]*vol_c_rate).sum()                      
                if i[1] == 'HWS':
                    usename = i[1]
                    hot_temp = list(conc_pd.loc[usename][rng])
                    hot_sum = (conc_pd.loc[usename][rng]*vol_h_rate).sum()
               
            elif 'DW' in i[1]:
                usename = i[1]+'H' 
                        # per US standard, plumbed to hot, 
                        # may need to be changed for international use
                hot_temp = list(conc_pd.loc[usename][rng])
                hot_sum = (conc_pd.loc[usename][rng]*vol_h_rate).sum()
               
            #Cold water only nodes
            elif 'TOL'in i[1]:
                usename = i[1]+'C'
                cold_temp = list(conc_pd.loc[usename][rng])
                cold_sum = (conc_pd.loc[usename][rng]*vol_c_rate).sum()
            elif 'SP' in i[1]:
                usename = i[1]+'C'
                cold_temp = list(conc_pd.loc[usename][rng])
                cold_sum = (conc_pd.loc[usename][rng]*vol_c_rate).sum()
            elif 'RE' in i[1]:
                usename = i[1]+'C'
                cold_temp = list(conc_pd.loc[usename][rng])
                cold_sum = (conc_pd.loc[usename][rng]*vol_c_rate).sum()
            elif 'HU' in i[1]:
                usename = i[1]+'C'
                cold_temp = list(conc_pd.loc[usename][rng])
                cold_sum = (conc_pd.loc[usename][rng]*vol_c_rate).sum()
            #Cold and Hot Water nodes
            elif 'WA' in i[1]:
                # this doesn't seem different than else, revisit
                nameh = i[1] + 'H'
                namec = i[1] + 'C'
                cold_temp = list(conc_pd.loc[namec][rng])
                hot_temp = list(conc_pd.loc[nameh][rng])
                cold_sum = (conc_pd.loc[namec][rng]*vol_c_rate).sum()
                hot_sum = (conc_pd.loc[nameh][rng]*vol_h_rate).sum()
            else:
                nameh = i[1] + 'H'
                namec = i[1] + 'C'
                cold_temp = list(conc_pd.loc[namec][rng])
                hot_temp = list(conc_pd.loc[nameh][rng])
                cold_sum = (conc_pd.loc[namec][rng]*vol_c_rate).sum()
                hot_sum = (conc_pd.loc[nameh][rng]*vol_h_rate).sum()
           
            results_table.append([i, 
                                 hot_sum, 
                                 vol_h_used, 
                                 cold_sum, 
                                 vol_c_used, 
                                 hot_temp, 
                                 cold_temp])
            
    summary_pd = pd.DataFrame(data=results_table, columns=['patternInfo', 
                                                             'hotMass',
                                                             'hotVolume',
                                                             'coldMass',
                                                             'coldVolume',
                                                             'hotConc',
                                                             'coldConc'])
    return summary_pd



                
# =============================================================================
# EPANET and Multiprocessor Operation Functions
# =============================================================================
def BinReader_Quality(filename):
    '''
    Binary reader function calls WNTR's binary reader. Returns dataframe object.
    Relies on WNTR so changes to EPANET can be more centrally addressed in future.

    Parameters
    ----------
    filename : string
        filename for binary file to read in.

    Returns
    -------
    df : nodal quality dataframe
        See WNTR documentation for more details.
        returns df object that stores link and node characteristics as 
        df.node and df.link, which are true pandas dataframes
    '''
    df = (wntr.epanet.io.BinFile().read(filename)).node['quality'].transpose()
    
    return df  

def BinReader(filename):
    '''
    Binary reader function calls WNTR's binary reader. Returns dataframe object.
    Relies on WNTR so changes to EPANET can be more centrally addressed in future.

    Parameters
    ----------
    filename : string
        filename for binary file to read in.

    Returns
    -------
    df : wntr results object - dataframe stored in dictionaries
    
        See WNTR documentation for more details.
        returns df object that stores link and node characteristics as 
        df.node and df.link, which are true pandas dataframes
    '''
    df = wntr.epanet.io.BinFile().read(filename)
    
    return df  

def runepanet(infile):
    print('Running: ' + infile)
    mp.freeze_support()
    wntr.epanet.toolkit.runepanet(infile)

def mp_read(in_data):
    infile, event_list = in_data    
    runID = infile.split('.')[0]
    outbin = runID+'.bin'
    print ("Analyzing ", runID)
    mp.freeze_support()
    # while not os.path.isfile(outbin):
    #     print('working')
    #     time.sleep(1)
    conc_pd = BinReader_Quality(outbin)   # should just be a water quality dataframe
    
    summary_pd = generate_summary(event_list, conc_pd, tss)
    # Save summary to json object. 
    # Much smaller file size than binary and input files
    summary_pd.to_json(runID+'.json')
    
    # Split file delete actions per file for clearer error handling
    try:
        os.remove(runID + '.bin')
    except:
        print('Error removing ' + runID +'.bin')
    try:
        os.remove(runID + '.inp')
    except:
        print('Error removing ' + runID +'.inp')
    try:
        os.remove(runID + '.rpt')
    except:
        print('Error removing ' + runID +'.rpt')


def mp_run_epanet(available):
    def chunks(lst, n):
        a = []
        for i in range(0, len(lst), n):
             a.append(lst[i:i+n])
        return a
    
    # Calculate how many cores to use
    num_proc = int(mp.cpu_count()*.75) # not max due to memory constraints
    # if 'win' in sys.platform:
    #     num_proc = 1
    
    # num_proc = 1 # temporary reset, until multiprocessing is working correctly
    
    if num_proc > 1:
        run_sets = chunks(available, num_proc)
        # if __name__ == 'main':
        for group in run_sets:

            
            to_run = [x[2] + x[3] for x in group]
            
            pool = mp.Pool(processes=num_proc)
            res = pool.map(runepanet, to_run)
            pool.close()
            pool.join()
            
            # MP reader
            
            read_obj = [] # need iterable for multiprocess
            for run in group:
                base = run[0]
                infile = run[2] + run[3]
                events = cPickle.load(open(run[1], 'rb'))
                event_list = events[base]
                read_obj.append([infile, event_list])
            
            pool2 = mp.Pool(processes=num_proc)
            res2 = pool2.map(mp_read, read_obj)
            pool2.close()
            pool2.join()
            

    else:
        for run in available:
            try:
                base = run[0]            # Base name
                # Run EPANET simulation
                infile = run[2] + run[3] # Input file to consider
                runepanet(infile)       
                # Get Event List information
                pckl = run[1]            # Pickle file location
                pickle_obj = cPickle.load(open(pckl, 'rb'))
                event_list = pickle_obj[base]
                # Process binary file, save json
                mp_read(infile, event_list)
            except:
                print('Error running ' + infile)
            
                

# =============================================================================
# Household water usage simulator functions
# =============================================================================
def week_routine_person(days_in_week, weekdayroutine, weekendroutine):
    routine_person = []
    for day in days_in_week:
        if day == 'wd':
            routine_person.append(weekdayroutine)
        elif day == 'we':
            routine_person.append(weekendroutine)
    return routine_person


def week_routine_home(days_in_week, homeroutine):
    routine_home = []
    if homeroutine != False:
        for day in days_in_week:
            if day == 'wd':
                routine_home.append([])
            elif day == 'we':
                routine_home.append(homeroutine)
    return routine_home


def DeleteContents(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


# =============================================================================
# Old functions. Saved in case they are needed. Currently unused.
# =============================================================================
def MSXBinReader(filename, epanetinpfile):
    wn = wntr.network.WaterNetworkModel(epanetinpfile)
    duration = int(wn.options.time.duration)
    with open(filename, 'rb') as fin:
          ftype = '=f4'
          idlen = 32
          prolog = np.fromfile(fin, dtype = np.int32, count = 6)
          magic1 = prolog[0]
          version = prolog[1]
          nnodes = prolog[2]
          nlinks = prolog[3]
          nspecies = prolog[4]
          reportstep = prolog[5]
          species_list = []
          node_list = wn.node_name_list
          link_list = wn.link_name_list

          for i in range(nspecies):
                  species_len = int(np.fromfile(fin, dtype = np.int32, count = 1))
                  species_name = ''.join(chr(f) for f in np.fromfile(fin, dtype = np.uint8, count = species_len) if f!=0)
                  species_list.append(species_name)
          species_mass = []
          for i in range(nspecies):
                  species_mass.append(''.join(chr(f) for f in np.fromfile(fin, dtype = np.uint8, count = 16) if f != 0))
          timerange = range(0, duration+1, reportstep)
          
          tr = len(timerange)
          
          row1 = ['node']*nnodes*len(species_list)+['link']*nlinks*len(species_list)
          row2 = []
          for i in [nnodes,nlinks]:
                  for j in species_list:
                        row2.append([j]*i)
          row2 = [y for x in row2 for y in x]
          row3 = [node_list for i in species_list] + [link_list for i in species_list]
          row3 = [y for x in row3 for y in x]    
          
          tuples = list(zip(row1, row2, row3))
          index = pd.MultiIndex.from_tuples(tuples, names = ['type','species','name'])
          
          try:
                  data = np.fromfile(fin, dtype = np.dtype(ftype), count = tr*(len(species_list*(nnodes + nlinks))))
                  data = np.reshape(data, (tr, len(species_list*(nnodes + nlinks))))
          except Exception as e:
              print(e)
              print ("oops")
          postlog = np.fromfile(fin, dtype = np.int32, count = 4)
          offset = postlog[0]
          numreport = postlog[1]
          errorcode = postlog[2]
          magicnew = postlog[3] 
          if magic1 == magicnew:
              print("Magic# Match")
              df_fin = pd.DataFrame(data.transpose(), index = index, columns = timerange)
              df_fin = df_fin.transpose()
          else:
              print("Magic#s do not match!")
    return df_fin

# =============================================================================
# Deprecate BELOW
# =============================================================================
# def run_epanet(infile):
#     '''
    

#     Parameters
#     ----------
#     infile : string
#         Uses subprocess to run an external instance of EPANET.
        
        

#     Returns
#     -------
#     None.

#     '''
#     outrpt = infile.split('.')[0]+'.rpt'
#     outbin = infile.split('.')[0]+'.bin'
#     # print(infile)
#     print(outrpt, outbin)
#     print ("Running...", infile)    
#     subprocess.Popen([epanet_loc,infile,outrpt,outbin]).communicate()   

   

# def mp_run_epanet(available):
#     '''
#     available: a list of available files to run
#     '''
#     num_proc = int(mp.cpu_count()*.75) # not max due to memory constraints
#     if 'win' in sys.platform:
#         num_proc = 1
    
#     if num_proc == 1:
#         pass
    
#     else:
#         pass
    
#     more_to_run = True
#     avail_jobs = [x for x in available]   
#     while more_to_run:
#         procs = []
#         group = []
#         group2 = []
#         if not rebuild:
#             while len(avail_jobs) > 0:
#                 if os.path.isfile(avail_jobs[0][2]+'.json'):
#                     del avail_jobs[0]
#                     if len(avail_jobs) == 0:
#                         break
#                 else:
#                     group.append(avail_jobs[0][2])
#                     group2.append(avail_jobs[0][1])
#                     del avail_jobs[0]
#                     if len(group) == num_proc:
#                         break
#                     elif len(avail_jobs) == 0:
#                         more_to_run = False
#                         break
#         else:
#             for loop in range(num_proc):
#                 group.append(avail_jobs[0][2])
#                 group2.append(avail_jobs[0][1])
#                 del avail_jobs[0]
#                 if len(avail_jobs) == 0:
#                     more_to_run = False
#                     break
#         print ("Running jobs", group)        
#         for i in group:
#             job = i+'.inp'
#             p = mp.Process(target = run_epanet, args = (job,))
#             procs.append(p)
#             p.start()    
#         time.sleep(0.5)
#         pause = True
#         while pause:
#             time.sleep(0.1) 
#             num_running = sum([1 if x.is_alive() else 0 for x in procs])
#             if num_running == 0:
#                 pause = False
        
#         # wait for all temp binary files to be converted to '.bin' files        
#         if len([i for i in os.listdir('.') if 'en' in i]) > 0:
#             time.sleep(10)
            
#         ## PROCESS IN OUTPUT
#         procs = []
#         patt_base = ''
#         patt_obj = dict()
#         for i in range(len(group2)):
#             tmp = group2[i].split('-')
#             new_base = tmp[0]+'-'+tmp[1]
#             if new_base != patt_base:
#                 patt_obj = cPickle.load(open(new_base+'.pickle','rb'))
#             patt_base = new_base
#             patt_store = patt_obj[group2[i]]           
#             p = mp.Process(target=mp_read, args = (group[i],patt_store,))
#             procs.append(p)
#             p.start()
#         time.sleep(0.5)
#         pause = True
#         while pause: 
#             num_running = sum([1 if x.is_alive() else 0 for x in procs])
#             time.sleep(0.1)
#             if num_running == 0:
#                 pause = False           
#         if len(avail_jobs) == 0:
#             more_to_run = False
#     ID = available[0][0].split('-')[1].split('_')[0]
#     avail_setup = [i.split('.')[0] for i in os.listdir(os.getcwd()) if '.bin' in i]
#     available2 = []
#     for i in avail_setup:
#         jobIDs = i.split('-')[0]+'-'+ID+'_model'
#         available2.append([jobIDs, i, i])
#     if len(available2) > 0:
#         procs = []
#         patt_base = ''
#         patt_obj = dict()
#         for i in range(len(available2)):
#             tmp = available2[i][1].split('-')
#             new_base = tmp[0]+'-'+tmp[1]
#             if new_base != patt_base:
#                 patt_obj = cPickle.load(open(new_base+'.pickle','rb'))
#             patt_base = new_base
#             patt_store = patt_obj[available2[i][2]]           
#             p = mp.Process(target=mp_read, args = (available2[i][1],patt_store,))
#             procs.append(p)
#             p.start()
#         time.sleep(0.5)
#         pause = True
#         while pause: 
#             num_running = sum([1 if x.is_alive() else 0 for x in procs])
#             time.sleep(0.1)
#             if num_running == 0:
#                 pause = False           


# python_loc = sys.executable
# if 'win' not in sys.platform:                          #system == 'linux':
#        epanet_loc = './EPANET/runepanet2.sh' # need to compile/add this
# elif 'win' in sys.platform:                            #system == 'windows':
#        epanet_loc = './EPANET/runepanet.exe'