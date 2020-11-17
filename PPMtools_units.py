# -*- coding: utf-8 -*-
"""
PPMtools_units

File for storing single location of units
"""


sec_per_min = 60
min_per_hr = 60
hr_per_day = 24
sec_per_day = hr_per_day * min_per_hr * sec_per_min
sec_per_hr = min_per_hr * sec_per_min
m_per_inch = 0.0254
mlpgal = 3785.411784
m3_per_gal = mlpgal / 1e6
mlpL = 1000. # ml per L
gpm_to_Lps = mlpgal / mlpL / sec_per_min  #1000 ml in L, 60 seconds in minute

# Pattern timestep as tss (seconds)
tss = 10                     
steps_per_min = int(sec_per_min / tss)
steps_per_day = int(sec_per_day / tss)
