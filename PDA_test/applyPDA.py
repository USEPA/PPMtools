# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 14:07:24 2022

@author: JBurkhar
"""

import numpy as np
import pandas as pd
import wntr
from itertools import combinations
import matplotlib.pyplot as plt
plt.close('all')

## Unit Conversions
ft2psi = 0.433527504001
gpm2mps = 6.30901964e-05
ft2m = 12. * 0.0254    # 0.3048m
psi2m = ft2m/ft2psi    # 0.70307  


params = pd.read_excel('PDA_params.xlsx', index_col=0, header=0)
# print(params)  ## for test, can comment out

source_pressure = 40 # psi
round_results = True
round_level = 3

## input INP file into WNTR format
inp_file = 'HPSS_elev.inp'
# inp_file = 'C:/Users/jburkhar/Environmental Protection Agency (EPA)/Premise Plumbing Modeling Team - Pressure Dependent Experiment/PDA_Analysis/JBB_House_PDA.inp'
wn = wntr.network.WaterNetworkModel(inp_file)



wn.get_node(wn.reservoir_name_list[0]).base_head = source_pressure * psi2m
print(f"{wn.get_node(wn.reservoir_name_list[0]).base_head:.2f} m")

## plot the network, if desired
# wntr.graphics.plot_network(wn)

nodes = [i for i in wn.node_name_list if i not in wn.reservoir_name_list]
nzd_nodes = [i for i in nodes if wn.get_node(i).base_demand > 0]
# print(nzd_nodes)


## build cross reference list with active faucets, corresponding hot/cold nodes
## and corresponding parameter type
xref = {'SH1': {'cold': 'SH1C', 'hot': 'SH1H', 'type': 'SH'},
        'TOL1': {'cold': 'TOL1C', 'hot': 'None', 'type': 'TOL'},
        'F1': {'cold': 'F1C', 'hot': 'F1H', 'type': 'F1'},
        'F2': {'cold': 'F2C', 'hot': 'F2H', 'type': 'F2'},
        'F3': {'cold': 'F3C', 'hot': 'F3H', 'type': 'F3'},
        'F4': {'cold': 'F4C', 'hot': 'F4H', 'type': 'F4'}}

sol_opt = {'MAXITER': 50000, 
           'TOL': 1e-8, 
           'BT_RHO': 0.01, 
           'BT_MAXITER': 5000, 
           'BACKTRACKING': True, 
           'BT_START_ITER': 2}

fixtures = list(xref.keys())


data_map = {} # create a storage data dictionary
for i in range(1, len(fixtures)+1):
    subperm = list(combinations(fixtures, i))
    for item in subperm:
        item_val = list(item)
        item_val.sort()
        data_map[''.join(item_val)] = {'fixts': item_val, 'flows': {j:None for j in item_val}}
    
# print(data_map)

data_map_df = pd.DataFrame(index=data_map.keys(), columns=xref.keys())
# print(data_map_df)


for active in data_map.keys():
    # print(active)
    # print(active_fixtures)
    wn = wntr.network.WaterNetworkModel(inp_file)
    # reset these values, may move to within a loop
    wn.options.hydraulic.demand_model = 'PDA'
    wn.options.time.hydraulic_timestep = 1
    wn.options.time.duration = 1
    wn.options.time.report_timestep = 1
    wn.options.time.pattern_timestep = 1
    wn.options.time.pattern_start = 0
    wn.options.hydraulic.accuracy = 1e-8
    wn.options.hydraulic.maxcheck = 50000
    wn.options.hydraulic.trials = 50000
    wn.options.hydraulic.checkfreq = 7
        
    wn.get_node(wn.reservoir_name_list[0]).base_head = source_pressure * psi2m

    active_fixtures = data_map[active]['fixts']

    for i in xref.keys(): #set up the parametrs from the params datastructure
        # print(i)
        for temp in ['cold', 'hot']:
            if xref[i][temp] != 'None':
                node_name = xref[i][temp]
                type_name = xref[i]['type']
                wn.get_node(node_name).demand_timeseries_list[0].base_value = float(params['D'][type_name] * gpm2mps)
                wn.get_node(node_name).required_pressure = float(params['Preq'][type_name] * psi2m)
                wn.get_node(node_name).minimum_pressure = float(params['Pmin'][type_name] * psi2m)
                wn.get_node(node_name).pressure_exponent = float(params['Pexp'][type_name] * 1.)
                
                # print(wn.get_node(node_name).demand_timeseries_list[0].base_value / gpm2mps)
                
                pattern_name = wn.get_node(node_name).demand_timeseries_list[0].pattern.name

                # print(wn.patterns[pattern_name].multipliers)
                wn.patterns[pattern_name].multipliers = np.array([0.])
                # print(wn.patterns[pattern_name].multipliers)
    
    modeled_fixtures = []
    for fix in active_fixtures: # actually turn on the active fixtures
        # print(fix)
        node_name = xref[fix]['cold']
        modeled_fixtures.append(node_name)
        pattern_name = wn.get_node(node_name).demand_timeseries_list[0].pattern.name
        wn.patterns[pattern_name].multipliers = np.array([1.])
        # print(wn.patterns[pattern_name].multipliers)
        
    # sim = wntr.sim.EpanetSimulator(wn)
    # results = sim.run_sim()
    
    sim = wntr.sim.WNTRSimulator(wn)
    try:
        results = sim.run_sim(
                          convergence_error=True,
                          solver_options=sol_opt,
                          HW_approx='piecewise'
                          )
    
    # print(results.node['demand'][modeled_fixtures])
    
        results_data = results.node['demand'][modeled_fixtures].loc[1] / gpm2mps
        success_flag = True
    except:
        success_flag = False
        results_data = 'None'
    
    # print(results_data)
    
    
    for fix in active_fixtures:
        if success_flag:
            flow = results_data[xref[fix]['cold']]
            if flow < 0:
                flow = 0.
            data_map[active]['flows'][fix] = flow * 1.
            if round_results:
                data_map_df.loc[active][fix] = np.round(flow * 1., round_level)
            else:
                data_map_df.loc[active][fix] = flow * 1.
        else: 
            data_map[active]['flows'][fix] = np.nan


print(data_map_df)




