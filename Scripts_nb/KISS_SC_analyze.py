
# coding: utf-8

# In[1]:

import os
import glob
import datetime
import numpy as np
from copy import deepcopy
from miic.core.miic_utils import mat_to_ndarray, convert_time, datetime_list, save_dv, convert_to_matlab, save_dict_to_matlab_file
import miic.core.change_processing as chp
import miic.core.plot_fun as pf
import matplotlib.pyplot as plt
from miic.core.stream import corr_trace_to_obspy
from miic.core.corr_mat_processing import corr_mat_time_select, corr_mat_from_h5,         corr_mat_extract_trace, corr_mat_trim, corr_mat_normalize, corr_mat_resample,         corr_mat_filter, corr_mat_time_select, corr_mat_correct_stretch
from multiprocessing import Pool
reload(chp)


# In[40]:

freq_win = [2,6]
stretch_range = 0.03
stretch_steps=50
#time_window=[2,12]
time_window=[5,18]
n_average = 48+1
dtl = datetime_list(datetime.datetime(2015,7,19,23,45),datetime.datetime(2016,8,10),inc=1800)

dv_path = '/home/chris/PROJECTS/KISS/monitoring/SC/change/version_B'
figure_path = dv_path


# In[36]:

stations = ['X9.OR1', 'X9.OR2', 'X9.OR3', 'X9.OR4',
            'X9.OR5', 'X9.OR6', 'X9.OR7', 'X9.OR8',
            'X9.OR9', 'X9.OR10', 'X9.OR11', 'X9.OR12',
            'X9.OR13', 'X9.OR14', 'X9.OR15', 'X9.OR16',
            'X9.OR17', 'X9.OR18', 'X9.OR19', 'X9.OR20',
            'X9.OR21', 'X9.OR22', 'X9.OR23', 'X9.OR24',
            'X9.OR25', 'X9.OR27', 'X9.OR28', 'X9.OR29',
            'X9.OR30', 'X9.OR31', 'X9.OR32',
            'X9.IR1', 'X9.IR2', 'X9.IR3', 'X9.IR4',
            'X9.IR6', 'X9.IR7', 'X9.IR8', 'X9.IR9',
            'X9.IR10', 'X9.IR11', 'X9.IR12','X9.IR13',
            'X9.IR14', 'X9.IR15', 'X9.IR16', 'X9.IR17',
            'X9.IR18', 'X9.IR19','X9.IR20', 'X9.SV1',
            'X9.SV2', 'X9.SV3', 'X9.SV4', 'X9.SV5',
            'X9.SV6','X9.SV7', 'X9.SV8', 'X9.SV9',
            'X9.SV12', 'X9.SV13', 'X9.OL1', 'X9.OL2',
            'X9.OL3', 'X9.OL4', 'X9.OL5', 'X9.OL6',
            'X9.OL7', 'X9.OL8', 'X9.OL9', 'D0.BZG',
            'D0.ESO', 'D0.KBG', 'D0.KIR', 'D0.KLY',
            'D0.KOZ', 'D0.TUMD', 'YY.BDR', 'YY.CIR',
            'YY.KBT', 'YY.KRS', 'YY.LGN', 'YY.SMK',
            'YY.SRK', 'YY.ZLN', 'YY.BZM', 'YY.BZW',
            'YY.KIR', 'YY.KMN','YY.KPT', 'YY.KZV',
            'YY.SRD', 'YY.TUM', 'YY.KRY', 'YY.MKZ']




def do_job(station):
    print(station,)
    net,sta = station.split('.')
    flist = sorted(glob.glob('/home/chris/PROJECTS/KISS/monitoring/SC/corr/*/trace_%s%s.%s%s.*.mat' % (net,net,sta,sta)))
    print(len(flist))
    try:
        measure_dv(flist)
    except:
        print('Failed for station %s' % station)




def measure_dv(flist):
    for fl in flist:
        print(fl)
        mat = mat_to_ndarray(fl)
        mat = corr_mat_filter(mat,freqs=freq_win)
        mat = corr_mat_resample(mat,dtl)

        reftr = corr_mat_extract_trace(mat,method='norm_mean')
        refst = corr_trace_to_obspy(reftr)
        dv = chp.velocity_change(mat,ref=refst,tw=time_window,return_simmat=True,
                                 stretch_range=stretch_range,stretch_steps=stretch_steps,)
        figure_file_name='%s.%s.%s.%s.png'%(mat['stats']['network'],mat['stats']['station'],
                                            mat['stats']['location'],mat['stats']['channel'])
        #pf.plot_dv(dv,figure_path,figure_file_name)
        save_dv(dv,'',dv_path)


if __name__ == '__main__':

    p = Pool(15)
    p.map(do_job,stations)
    #for station in stations:
    #    do_job(station)
