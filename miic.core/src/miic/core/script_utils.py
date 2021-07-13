# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 09:33:04 2017

@author: chris
"""

import os
import yaml
import shutil
import importlib
from miic.core.miic_utils import create_path, import_function_by_name
import miic.core.pxcorr_func as px
from copy import deepcopy
from obspy import UTCDateTime
import pandas as pd
from obspy.geodetics.base import gps2dist_azimuth
import numpy as np

def read_parameter_file(par_file):
    """Read yaml parameter file.
    """
    with open(par_file,'rb') as f:
        try:
            par = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise(exc)
    return par


def ini_project(par_file):
    """Initialize a project of network synchrinization
    
    Read the yaml parameter file, and complete its content, i.e. combine
    subdirectory names. Some project relevant directories are created and
    directory names completed. The list of combinations is filled if not given
    explicitly. The parameter dictionary is returned.
    
    :type par_file: str
    :param par_file: path of the yaml parameter file
    :rtype: dict
    :return: parameters
    """

    par = read_parameter_file(par_file)

    par.update({'execution_start':'%s' % UTCDateTime()})

    create_path(par['proj_dir'])
    par.update({'log_dir':os.path.join(par['proj_dir'],par['log_subdir'])})
    par.update({'fig_dir':os.path.join(par['proj_dir'],par['fig_subdir'])})
    create_path(par['log_dir'])
    create_path(par['fig_dir'])
    par['co'].update({'res_dir': os.path.join(par['proj_dir'],
                                             par['co']['subdir'])})
    par['co'].update({'fig_dir': os.path.join(par['fig_dir'],
                                             par['co']['subdir'])})
    par['dv'].update({'res_dir': os.path.join(par['proj_dir'],
                                             par['dv']['subdir'])})
    par['dv'].update({'fig_dir': os.path.join(par['fig_dir'],
                                             par['dv']['subdir'])})
    # copy parameter file to log dir
    shutil.copy(par_file,os.path.join(par['log_dir'],'%s_parfile.txt' % par['execution_start']))

    # replace function names for preprocessing with functions
    if 'preProcessing' in par['co'].keys():
        for procStep in par['co']['preProcessing']:
            procStep['function'] = import_function_by_name(procStep['function'])

    # create corr_args
    # replace function name by function itself
    for func in par['co']['corr_args']['TDpreProcessing']:
        func['function'] = import_function_by_name(func['function'])
    for func in par['co']['corr_args']['FDpreProcessing']:
        func['function'] = import_function_by_name(func['function'])
    if 'direct_output' in par['co']['corr_args']:
        par['co']['corr_args']['direct_output'].update({'base_dir': par['co']['res_dir']})
    return par



def correlation_subdir_name(date):
    """Create the path to a sub folder for the correlation traces.

    The path will have the following structure:
    YEAR/JDAY
    """

    if isinstance(date,UTCDateTime):
        date = date.datetime

    subpath = join(str(date.year),"%03d" % date.timetuple().tm_yday)

    return subpath

def combinations_in_dist_range(comb_list,lle_df,min_distance,max_distance) :
    """Filters station combination list within a distance range
    :type comb_list: list
    :param comb_list: list containing two list [[IDs of first trace],[IDs of second trace]]
    :type lle_df: :class:`~pandas.DataFrame`
    :param lle_df: The dataframe that has as index the station names and 3 columns
        lat, lon and ele.
    :type min_distance: float
    :param min_distance: minimum distance separation (km) of station combination to accept
    :type max_distance: float
    :param max_distance: maximum distance separation (km) of station combination to accept
    :rtype: list
    :return: list containing two list [[IDs of first trace],[IDs of second trace]]
    """

    # From coordinates df create non-duplicated station list (in case of specified channels)
    lats,lons=[],[]
    indices=lle_df.index.get_values()
    stas={}
    for i in indices :
        stas['.'.join(i.split('.')[:2])]=str(i)
    stations=sorted(stas.keys())
    for s in stations :
        row=lle_df.ix[stas[s]]
        lats.append(row['latitude'])
        lons.append(row['longitude'])
    m_lat,m_lon=np.array(lats),np.array(lons)

    # Distance matrix to calculate separations (in km)
    size = (len(m_lat),len(m_lon))
    distance_matrix = np.zeros(size)
    for idx in range(len(m_lat)):
        for idy in range(len(m_lat)):
            dist,_,_ = gps2dist_azimuth(m_lat[idx], m_lon[idx], m_lat[idy], m_lon[idy])
            distance_matrix[idx,idy] = dist/1000
    distance_df=pd.DataFrame(data=distance_matrix,index=pd.Index(stations),
                                columns=pd.Index(stations))

    # For each field of initial combination list, get station names, find separation
    # from distance matrix, apply filter test and pass to output
    first,second=comb_list[0],comb_list[1]
    filt_first,filt_second=[],[]
    for i in range(0,len(first)) :
        i1,i2=".".join(first[i].split('.')[0:2]),".".join(second[i].split('.')[0:2])
        separation=distance_df.loc[i2].loc[i1]
        if ((separation > float(min_distance)) and (separation < float(max_distance))):
            filt_first.append(first[i])
            filt_second.append(second[i])
    return [filt_first,filt_second]

def combine_station_channels(stations,channels,par_co,lle_df):
    """Create a list of combination

    Combine stations given in a list of NET.STATION parts of the seedID
    and a list of channel names using a given method.
    
    :type stations: list with items of the form 'NET.STATION'
    :param stations: stations to be used if present
    :type channel: list with the channel names
    :param channels: channels to be used if present
    :type par_co: dict
    :param par_co: Determines which traces of the strem are combined. It is
        expected to contain the key ``combination_method`` with the following
        possible values:
    :type lle_df: :class:`~pandas.DataFrame`
    :param lle_df: Pandas DataFrame with stations name as index and lat, lon,
        ele as columns
 
        ``'betweenStations'``: Traces are combined if either their station or
            their network names are different including all possible channel
            combinations.
        ``'betweenStations_distance'``: Same as betweenStations, but combinations
            are then filtered between distance range 'combination_mindist' and
            'combination_maxdist' that are to be given as additional keys of
            ``par_co``.
        ``'ANT'``: Combinations designed for Ambient Noise Tomography.
            Combinations are made between stations and only between channels that
            are available at each station. The provided coordinatefile must list 
            station-channels individually. e.g. NET.STA.*.HHZ NET.STA.*.HHN 
            Only the 5 combinations ZZ NN NE EN EE which are useful for ANT 
            are used. Distance range filter is applied.
        ``'ANT_extra_combs'``: 
                Same as ANT, but only combinations ZN NZ ZE EZ are accepted.
        ``'betweenComponents'``: Traces are combined if their components (last
            letter of channel name) names are different and their station and
            network names are identical (single station cross-correlation).
        ``'autoComponents'``: Traces are combined only with themselves.
        ``'betweenAllComponents': Of each station combine all components
            i.e. EE, EN, EZ, NN, NZ, ZZ.
        ``'allSimpleCombinations'``: All Traces are combined once (only one of
            (0,1) and (1,0))
        ``'allCombinations'``: All traces are combined in both orders ((0,1)
            and (1,0))
    :type ll_df: pandas.dataframe
    :param ll_df: dataframe containing the coordinate information of the stations
        as provided by :func:`~miic.core.miic_utils.lat_lon_ele_load`
    :rtype: list
    :return: list containing two list [[IDs of first trace],[IDs of second trace]]
    """
    method=par_co['combination_method']
    stations = sorted(deepcopy(stations))
    channels = sorted(deepcopy(channels))
    first = []
    second = []
    if method == 'betweenStations':
        for ii in range(len(stations)):
            for jj in range(ii+1,len(stations)):
                for k in range(len(channels)):
                    for l in range(len(channels)):
                        first.append('%s..%s' % (stations[ii],channels[k]))
                        second.append('%s..%s' % (stations[jj],channels[l]))
    elif method == 'betweenStations_distance' :
        for ii in range(len(stations)):
            for jj in range(ii+1,len(stations)):
                for k in range(len(channels)):
                    for l in range(len(channels)):
                        first.append('%s..%s' % (stations[ii],channels[k]))
                        second.append('%s..%s' % (stations[jj],channels[l]))
        min_distance,max_distance=par_co['combination_mindist'],par_co['combination_maxdist']
        first,second=combinations_in_dist_range([first,second],lle_df,min_distance,max_distance)
    elif method == 'ANT' :
        allowed_comp_combinations=["ZZ","NN","NE","EN","EE"]
        avail_chnls=lle_df.index.get_values()
        for ii in range(len(stations)) :
            for jj in range(ii+1,len(stations)): 
                for k in range(len(channels)) :
                    for l in range(len(channels)):
                        if ".".join([stations[ii],'*',channels[k]]) in avail_chnls :
                            if ".".join([stations[jj],'*',channels[l]]) in avail_chnls :
                                if channels[k][-1]+channels[l][-1] in allowed_comp_combinations :
                                    first.append('%s..%s' % (stations[ii],channels[k]))
                                    second.append('%s..%s' % (stations[jj],channels[l]))
        if len(first) == 0 :
            raise RuntimeError("ANT combination method found no available channels in coordinate file")
        min_distance,max_distance=par_co['combination_mindist'],par_co['combination_maxdist']
        first,second=combinations_in_dist_range([first,second],lle_df,min_distance,max_distance)
    elif method == 'ANT_extra_combs' :
        allowed_comp_combinations=["ZN","NZ","ZE","EZ"]
        avail_chnls=lle_df.index.get_values()
        for ii in range(len(stations)) :
            for jj in range(ii+1,len(stations)): 
                for k in range(len(channels)) :
                    for l in range(len(channels)):
                        if ".".join([stations[ii],'*',channels[k]]) in avail_chnls :
                            if ".".join([stations[jj],'*',channels[l]]) in avail_chnls :
                                if channels[k][-1]+channels[l][-1] in allowed_comp_combinations :
                                    first.append('%s..%s' % (stations[ii],channels[k]))
                                    second.append('%s..%s' % (stations[jj],channels[l]))
        if len(first) == 0 :
            raise RuntimeError("ANT combination method found no available channels in coordinate file")
        min_distance,max_distance=par_co['combination_mindist'],par_co['combination_maxdist']
        first,second=combinations_in_dist_range([first,second],lle_df,min_distance,max_distance)
    elif method == 'betweenComponents':
        for ii in range(len(stations)):
            for k in range(len(channels)):
                for l in range(k+1,len(channels)):
                    first.append('%s..%s' % (stations[ii],channels[k]))
                    second.append('%s..%s' % (stations[ii],channels[l]))
    elif method == 'autoComponents':
        for ii in range(len(stations)):
            for k in range(len(channels)):
                first.append('%s..%s' % (stations[ii],channels[k]))
                second.append('%s..%s' % (stations[ii],channels[k]))
    elif method == 'betweenAllComponents':
        for ii in range(len(stations)):
            for k in range(len(channels)):
                for l in range(k,len(channels)):
                    first.append('%s..%s' % (stations[ii],channels[k]))
                    second.append('%s..%s' % (stations[ii],channels[l]))
    elif method == 'allSimpleCombinations':
        for ii in range(len(stations)):
            for jj in range(ii,len(stations)):
                for k in range(len(channels)):
                    for l in range(len(channels)):
                        first.append('%s..%s' % (stations[ii],channels[k]))
                        second.append('%s..%s' % (stations[jj],channels[l]))
    elif method == 'allCombinations':
        for ii in range(len(stations)):
            for jj in range(len(stations)):
                for k in range(len(channels)):
                    for l in range(len(channels)):
                        first.append('%s..%s' % (stations[ii],channels[k]))
                        second.append('%s..%s' % (stations[jj],channels[l]))
    else:
        raise ValueError("Method has to be one of ('betweenStations', "
                        "'betweenStations_distance', 'ANT', "
                        "'ANT_extra_combs', 'betweenAllComponents', "
                         "'betweenComponents', 'autoComponents',"
                         "'allSimpleCombinations', 'allCombinations').")
    return [first, second]


def select_available_combinations(st,comb_list,targs):
    """Estimate available subset of combinations
    """

    # For joint normalisation require all three channels to be present
    # Check 3 channels for each station and if not remove from stream
    joint_norm=False
    for proc in targs['FDpreProcessing']:
        if 'joint_norm' in proc['args'].keys():
            if proc['args']['joint_norm']==True :
                joint_norm=True
    if joint_norm :
        channels_per_station={}
        for tr in st:
            channels_per_station[tr.stats.network+'.'+tr.stats.station]=[]
        for tr in st:
            channels_per_station[tr.stats.network+'.'+tr.stats.station].append(tr.stats.channel)
        for s in channels_per_station.keys() :
            if not (len(channels_per_station[s]) % 3 == 0) :
                rem_st=st.select(station=s.split('.')[1])
                for rem_tr in rem_st.traces :
                    st.remove(rem_tr)

    stations = []
    combis = []
    for tr in st:
        stations.append('%s.%s..%s' %(tr.stats.network,tr.stats.station,tr.stats.channel))

    for ind in range(len(st)):
        # find all occurrences of a trace in combinations
        findex = [ii for ii,x in enumerate(comb_list[0]) if x == stations[ind]]
        # for every occurrence ...
        for find in findex:
            try:
                # ... check whether the trace that is to be combined is present in the stream
                sind = stations.index(comb_list[1][find])
                combis.append((ind,sind))
            except:
                pass

    return combis


