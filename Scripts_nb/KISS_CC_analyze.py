
# coding: utf-8

# In[1]:

import os
import glob
import datetime
import numpy as np
from copy import deepcopy
from miic.core.miic_utils import mat_to_ndarray, convert_time, datetime_list, save_dv, convert_to_matlab, save_dict_to_matlab_file, create_path
import miic.core.change_processing as chp
import miic.core.plot_fun as pf
import matplotlib.pyplot as plt 
from miic.core.stream import corr_trace_to_obspy
from miic.core.corr_mat_processing import corr_mat_time_select, corr_mat_from_h5,         corr_mat_extract_trace, corr_mat_trim, corr_mat_normalize, corr_mat_resample,         corr_mat_filter, corr_mat_time_select, corr_mat_correct_stretch
from multiprocessing import Pool
reload(chp)


# In[40]:

freq_win = [0.25,0.5]
stretch_range = 0.03
stretch_steps=50
vel = 1.5
time_window=[20,60]
#time_window=[5,18]
n_average = 48+1
dtl = datetime_list(datetime.datetime(2015,7,19,23,45),datetime.datetime(2016,8,10),inc=86400)

dv_path = '/home/chris/PROJECTS/KISS/monitoring/CC/change/version_A'
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


channels = ['SHE','SHN','SHZ','HHN','HHE','HHZ']
channel_pairs = []
for cha1 in channels:
    for cha2 in channels:
	channel_pairs.append("%s%s" % (cha1,cha2))



def do_job(station_pair):
    print(station_pair,)
    flist = []
    for path in ['/home/chris/rgreen/KISS_correlations/correlation_9/corr']:#'/home/rgreen/KISS/correlation_8/corr']:#,'/home/rgreen/KISS/correlation_9/corr']:
        for channel_pair in channel_pairs:
            for location in ['','10','00']:
                flist.append(os.path.join(path,channel_pair,"resamp_mat_%s.%s.%s.mat" % (station_pair,location,channel_pair)))
    measure_dv(flist,station_pair)




def measure_dv(flist,station_pair):
    tdv_path = os.path.join(dv_path,station_pair)
    create_path(tdv_path)
    for fl in flist:
        try:
            print(fl)
            mat = mat_to_ndarray(fl)
            ttime = mat['stats']['dist']/vel
            mat = corr_mat_filter(mat,freqs=freq_win)
            mat = corr_mat_resample(mat,dtl)

            reftr = corr_mat_extract_trace(mat,method='norm_mean')
            refst = corr_trace_to_obspy(reftr)
            for side in ['left','right']:
                dv = chp.velocity_change(mat,ref=refst,tw=[ttime+time_window[0], ttime+time_window[1]],return_simmat=True,
                                         stretch_range=stretch_range,stretch_steps=stretch_steps, sides=side)
                save_dv(dv,side,tdv_path)
        except:
            print('Failed')


if __name__ == '__main__':
    station_pairs = []
    for station1 in stations:
        net1,stat1 = station1.split('.')
        for station2 in stations:
            net2,stat2 = station2.split('.')
            station_pairs.append("%s%s.%s%s" % (net1,net2,stat1,stat2))
            station_pairs.append("%s%s.%s%s" % (net2,net1,stat2,stat1))


    p = Pool(15)
    p.map(do_job,station_pairs)
    for station_pair in station_pairs[2:10]:
       do_job(station_pair)
