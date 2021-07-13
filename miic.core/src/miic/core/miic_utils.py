# -*- coding: utf-8 -*-
"""
@author:
Eraldo Pomponi

@copyright:
The MIIC Development Team (eraldo.pomponi@uni-leipzig.de)

@license:
GNU Lesser General Public License, Version 3
(http://www.gnu.org/copyleft/lesser.html)

Created on Oct 5, 2011

Changes:
- convert npts from type used in obspy future.types.newint.newint
  back to long as new types stumble savemat  (21/07/2015 F Tilmann)
"""


# Main imports
import os,sys
import numpy as np
import scipy.io as sio
from scipy.io import loadmat, savemat
import datetime
import collections
import time
from cPickle import Pickler
import shutil
import importlib
import h5py

# Pandas import
from pandas import DataFrame, Panel, Series
from pandas.io.parsers import read_table

# ETS imports
try:
    BC_UI = True
    from traits.api import HasTraits, List, Int, \
        Str, Bool, Enum, Directory, File, Float
    from traitsui.api import View, Item, VGroup
except ImportError:
    BC_UI = False
    pass
    
# Obspy imports
from obspy.core import Stream, Trace, UTCDateTime


##############################################################################
# Exceptions                                                                 #
##############################################################################


class InputError(Exception):
    """
    Exception for Input errors.
    """
    def __init__(self, msg):
        Exception.__init__(self, msg)

##############################################################################
# Utility                                                                    #
##############################################################################


def create_rnd_array(nSignal=1, nSample=1000):
    """ Creates a random normal 2D ndarray.

    This function creates a 2D random normal array where the number of rows
    are equal to ``nSignal`` and the number of columns are equal
    to ``nSamples``.

    :type nSignal: int
    :param nSignal: Number of random realizations (rows).
    :type nSample: int
    :param nSamples: Number of samples of each realization (col)

    :rtype: 2D :class:`~numpy.ndarray`
    :return: **rnd_array**: random normal ndarray
    """

    rnd_array = np.random.normal(0, 1, (nSignal, nSample))
    return rnd_array


if BC_UI:
    class _create_rnd_array_view(HasTraits):
    
        nSignal = Int(2)
        nSample = Int(1000)
    
        traits_view = View(Item('nSignal'),
                           Item('nSample'))
                           

def create_range_array(low=0, high=1, nSamples=1000):
    """ Creates a 1D ndarray using range.

    This function creates an 1D array that has ``nSamples`` elements in the
    range from ``low`` to ``high``.

    :type low: int
    :param low: Range low boundary
    :type high: int
    :param high: Range high boundary
    :type nSamples: int
    :param nSamples: Number of samples

    :rtype: 1D :class:`~numpy.ndarray`
    :return: **range_array**: 1d ndarray
    """

    if (high - low == nSamples):
        ar = np.arange(low, high)
    else:
        ar = np.linspace(low, high, num=nSamples)

    return ar


if BC_UI:
    class _create_range_array_view(HasTraits):
    
        low = Int(0)
        high = Int(1)
        nSamples = Int(1000)
    
        traits_view = View(Item('low'),
                           Item('high'),
                           Item('nSamples'))


def dict_sel(d, key):
    """ Dictionary element selection.

    Return the value associated with a specified ``key`` in the input
    dictionary ``d``.

    :type d: dictionary
    :param d: Dictionary
    :type key: any
    :param key: Selected key

    :rtype: any
    :return: **d[key]**
    """
    if key in d:
        return d[key]
    else:
        print "key not found"
        return []


if BC_UI:
    class _dict_sel_view(HasTraits):
    
        key = Str
    
        trait_view = View(Item('key'))
    

def add_prefix(name, prefix=''):
    """ Add a prefix to a read-only string.

    :type name; string
    :param name: Read only string
    :type prefix: string
    :param prefix: Prefix to be added.

    :rtype: string
    :return: **comb_str**: Concatenated string prefix + name
    """
    return prefix + name


if BC_UI:
    class _add_prefix_view(HasTraits):
        name = Str
        prefix = Str
    
        trait_view = View(Item('name', style='readonly'),
                          Item('prefix'))


def merge_str(str1, str2):
    """ Merge two strings.

    :type str1: string
    :param str1: First string
    :type str2: string
    :param str2: Second string

    :rtype: string
    :return: **comb_str**: str1 + str2
    """
    return str1 + str2


if BC_UI:
    class _merge_str_view(HasTraits):
        str1 = Str
        str2 = Str
    
        trait_view = View(Item('str1'),
                          Item('str2'))


def dir_read(base_dir='', pattern='*.webnet', sort_flag=True):
    """ Create a list of files in a dir tree which name match a def pattern.

    :type base_dir: directory
    :param base_dir: Directories tree root
    :type pattern: string
    :param pattern: Patter to look for (e.g. *.mseed, */*/.mseed etc)
    :type sort_flag: bool
    :param sort_flag: If the result should be sorted or not

    :rtype: list of string
    :return: **files_list**: List of all files matching the ``pattern``
    """
    import glob

    if sort_flag:
        files_list = sorted(glob.glob(os.path.join(base_dir, pattern)))
    else:
        files_list = glob.glob(os.path.join(base_dir, pattern))

    return files_list


if BC_UI:
    class _dir_read_view(HasTraits):
    
        base_dir = Directory
        pattern = Str('*.webnet')
        sort_flag = Bool(True)
        # preview = Button('Preview')
        # file_list_preview = List(File)
        files_list = List
        _file_list_preview = List(File)
        _num_files = Int(0)
    
        trait_view = View(Item('base_dir'),
                          Item('pattern'),
                          Item('sort_flag', label='sorted'),
                          # Item('preview'),
                          # HGroup(Item('file_list_preview', style='readonly'),
                          #       Item('num_files', style='readonly')),
                          Item('_num_files', style='readonly', \
                               label='Num selec. files'),
                          resizable=True)
    
        def __init__(self, file_list=None, base_dir='', pattern='*.webnet', \
                     sort_flag=True):
            super(HasTraits, self).__init__()
            if file_list is not None:
                self._file_list_prev = file_list
            self.base_dir = base_dir
            self.pattern = pattern
            self.sorted = sort_flag
    
        def _base_dir_changed(self):
            self._file_list_preview = dir_read(self.base_dir, self.pattern, \
                                               self.sort_flag)
            self._num_files = len(self._file_list_preview)
    
        def _pattern_changed(self):
            self._file_list_preview = dir_read(self.base_dir, self.pattern, \
                                               self.sort_flag)
            self._num_files = len(self._file_list_preview)


zerotime = UTCDateTime(1971,1,1)

def create_path(directory):
    """Create a given path with all preceeding parts.

    Provided there is write access the function will creates
    all levels of the given path.

    :type directory: string
    :param directory: path of the directory to be created

    :rtype: int
    :return: 0
    """

    if not os.path.exists(directory) :
        # Use try in case another parallel process has made it in that time
        try :
            os.makedirs(directory)
        except OSError as e :
            if e[0]==17 :
                pass
            else :
                raise OSError(e)
    else:
        assert os.path.isdir(directory), "%s exists but is not a directory" % subpath
    return 0



def archive_code(scriptname):
    """Read parameters and archive code

    This is a convenience function that helps to track processing routines and
    parameter setting. Tracking is not done by propagating meta information.
    It just archives parameter files and processing scripts. The functions
    assumes that parameters are stored in a pythen file of the
    same name as the script that calls this function extended with `_par`.
    These parameters are read and returned as a module (e.g. `par`). This
    means that a parameter `parameter` set in the parameter file is accessible
    `par.parameter`. One parameter is required to be present in the parameter
    file: `res_dir`. This directory is created and within it a folder
    `code_dir` to which the script and the paremater files are copied and extended
    by a time string.

    :type scriptname: string
    :param scriptname: name of the executed script that is to be archived

    :rtype: module
    :return: module with the parameters for the script
    """

    # time string
    tim = time.strftime('%Y%m%d_%H%M%S')
    # name of paramter file according to above convention
    parname = scriptname[:-3]+'_par'
    # import parameters
    par = __import__(parname)
    # create directory to archive scripts
    code_dir = os.path.join(par.res_dir,'code_dir')
    create_path(code_dir)
    # copy files
    shutil.copyfile(scriptname,os.path.join(code_dir,scriptname[:-3]+'_'+tim+'.py'))
    shutil.copyfile(parname+'.py',os.path.join(code_dir,parname+'_'+tim+'.py'))
    return par


def ndarray_to_mat(nd_array, base_dir=None, filename="canvas_mat.mat", \
                   mat_var_name='corr_data'):
    """ Save an ndarray to a Matlab file.

    :type nd_array: :class:`~numpy.ndarray`
    :param nd_array: Array to be saved
    :type base_dir: directory
    :param base_dir: Directory where to save the file (i.e. the current one if
        not specified)
    :type filename: string
    :param filename: File name
    :type mat_var_name: string
    :param mat_var_name: The name of the matlab variable that will store the
        ndarray
    """

    if base_dir is None or not os.path.isdir(base_dir):
        base_dir = os.getcwd()

    sio.savemat(os.path.join(base_dir, filename), {mat_var_name: nd_array})
    return


if BC_UI:
    class _ndarray_to_mat_view(HasTraits):
        base_dir = Directory
        filename = Str
        mat_var_name = Str
    
        trait_view = View(Item('base_dir'),
                          Item('filename'),
                          Item('mat_var_name'))
    

def mat_to_ndarray(filename, flatten=True):
    """ Load a Matlab file into a dictionary.

    Keys of this dictionary are the names of the variables stored in the file.

    :type filename: full path filename
    :param filename: The name of the file to be loaded

    :rtype load_var: dictionary
    :return: **load_var**: Returned dictionary of the
        form { 'var_name' : var_value}
    """

    load_var = {}
    if os.path.isfile(filename):
        sio.loadmat(filename, mdict=load_var)
    else:
        raise ValueError("file doesn't exist")

    if flatten:
        # Flatten the returned dictionary
        for key in load_var:
            if load_var[key] is not None:
                flat_var = flatten_recarray(load_var[key])
                load_var.update({key: flat_var})

    if load_var.has_key('corr_trace') :
        if not len(load_var['corr_trace']) == load_var['stats']['npts'] :
            load_var['corr_trace']=np.squeeze(load_var['corr_trace'])

    return load_var


if BC_UI:
    class _mat_to_ndarray_view(HasTraits):
    
        filename = File
        flatten = Bool(True)
        trait_view = View(Item('filename'),
                          Item('flatten'))

def save_dict_to_hdf5(dic, filename):
    """
    ....
    """
    with h5py.File(filename, 'w') as h5file:
        recursively_save_dict_contents_to_group(h5file, '/', dic)

def recursively_save_dict_contents_to_group(h5file, path, dic):
    """
    ....
    """
    for key, item in dic.items():
        if isinstance(item, (np.ndarray, np.int64, np.float64, unicode, float, int, str, bytes, long)):
            h5file[path + key] = item
        elif isinstance(item, dict):
            recursively_save_dict_contents_to_group(h5file, path + key + '/', item)
        else:
            raise ValueError('Cannot save %s type'%type(item))

def load_dict_from_hdf5(filename):
    """
    ....
    """
    with h5py.File(filename, 'r') as h5file:
        return recursively_load_dict_contents_from_group(h5file, '/')

def recursively_load_dict_contents_from_group(h5file, path):
    """
    ....
    """
    ans = {}
    for key, item in h5file[path].items():
        if isinstance(item, h5py._hl.dataset.Dataset):
            ans[key] = item.value
        elif isinstance(item, h5py._hl.group.Group):
            ans[key] = recursively_load_dict_contents_from_group(h5file, path + key + '/')
    return ans

def corr_to_hdf5(data,stats,stats_tr1,stats_tr2,base_name,base_dir) :
    """ Output a correlation function to a hdf5 file.
    The hdf5 file contains three groups for the 3 stats dictionaries,
    and a "corr_data" group into which each correlation function
    is appended as a HDF5-dataset

    :type data: :class:`~numpy.ndarray`
    :param data: Correlation function to be written to hdf5 file
    :type stats: dictionary
    :param stats: Correlation stats determined by miic.core.corr_fun.combine_stats
    :type stats_tr1: dictionary
    :param stats_tr1: Trace stats for tr1
    :type stats_tr2: dictionary
    :param stats_tr2: Trace stats for tr2

    :type base_name: string
    :param base_name: Common "root" for every generated filename.
        It must not include underscores.
    :type base_dir: directory
    :param base_dir: Path where to save the files
    """

    _tr1dict = {'network': stats_tr1.network,
                'station': stats_tr1.station,
                'location': stats_tr1.location,
                'channel': stats_tr1.channel,
                'sampling_rate': stats_tr1.sampling_rate,
                'starttime': '%s' % stats_tr1.starttime,
                'endtime': '%s' % stats_tr1.endtime,
                'npts': long(stats_tr1.npts)}
    if 'sac' in stats_tr1:
        _tr1dict['stla'] = stats_tr1.sac.stla
        _tr1dict['stlo'] = stats_tr1.sac.stlo
        _tr1dict['stel'] = stats_tr1.sac.stel

    _tr2dict = {'network': stats_tr2.network,
                'station': stats_tr2.station,
                'location': stats_tr2.location,
                'channel': stats_tr2.channel,
                'sampling_rate': stats_tr2.sampling_rate,
                'starttime': '%s' % stats_tr2.starttime,
                'endtime': '%s' % stats_tr2.endtime,
                'npts': long(stats_tr2.npts)}
    if 'sac' in stats_tr2:
        _tr2dict['stla'] = stats_tr2.sac.stla
        _tr2dict['stlo'] = stats_tr2.sac.stlo
        _tr2dict['stel'] = stats_tr2.sac.stel

    _stats = {'network': stats.network,
              'station': stats.station,
              'location': stats.location,
              'channel': stats.channel,
              'sampling_rate': stats.sampling_rate,
              'starttime': '%s' % stats.starttime,
              'endtime': '%s' % stats.endtime,
              'npts': long(stats.npts)}
    if 'sac' in stats:
        _stats['stla'] = stats.sac.stla
        _stats['stlo'] = stats.sac.stlo
        _stats['stel'] = stats.sac.stel
        if np.all(map(lambda x: x in stats.sac, \
                      ['evla', 'evlo', 'evel', 'az', 'baz', 'dist'])):
            _stats['evla'] = stats.sac.evla
            _stats['evlo'] = stats.sac.evlo
            _stats['evel'] = stats.sac.evel
            _stats['az'] = stats.sac.az
            _stats['baz'] = stats.sac.baz
            _stats['dist'] = stats.sac.dist

    # Determine file name and time
    corr_id=".".join([stats.network,stats.station,stats.location,stats.channel])
    filename = os.path.join(base_dir,base_name + '_' + corr_id.replace('-', '')+'.h5')
    t = max(_tr1dict['starttime'],_tr2dict['starttime'])
    time = '%s' % t
    time = time.replace('-', '').replace('.', '').replace(':', '')

    # If file doesn't exist create the stats groups and data in corr_data group
    if not os.path.exists(filename):
        create_path(base_dir)
        h5dicts={'stats_tr1':_tr1dict, 'stats_tr2':_tr2dict, 'stats':_stats,
                'corr_data':{t:data} }
        save_dict_to_hdf5(h5dicts, filename)
    # Else append data to corr_data group
    else :
        with h5py.File(filename, 'a') as h5file:
            try :
                h5file.create_dataset("corr_data/"+t, data=data)
            except RuntimeError as e :
                print("The appending dataset is corr_data/"+t+" in file "+filename)
                #sys.exit()
                raise e

    return 0


def convert_to_matlab(st,
                      base_name,
                      base_dir,
                      suffix='',
                      seconds=0,
                      is_corr=False):
    """ Save an ObsPy Stream to a series of Matlab files.

    Each ``Trace`` contained in the ``Stream`` object will be stored in a
    different file which name is formatted as
    ``<timestamp>_'base_name'_<trace_seed_id_no_dash>_'suffix'_.mat``.
    Both <timestamp> and <trace_seed_id_no_dash> are generated directly
    reading trace meta-information so they are not accessible.
    If ``base_name == None or base_name == ''`` it is substituted with the
    string ``trace``.
    if ``suffix == None or suffix ==''`` it simply omitted keeping just one
    underscore to close the filename.
    This way to compose the filename is consistent with what expected by
    functions like :class:`~miic.core.macro.recombine_corr_data` that are
    supposed to read back the data from them.
    In case the parameter ``second`` is passed and different from 0 just
    ``second`` seconds will be saved in the Matlab file so that, for each
    ``Trace`` ``tr``, what is taken is ``tr(tr.stats.starttime,
    tr.stats.starttime + seconds).
    If the ``is_corr`` flag is `True``, the time interval is doubled and is
    symmetric respect to the default "zero-timelag" of
    UTCDateTime(1971, 1, 1, 0, 0, 0).

    >>>ref = UTCDateTime(1971, 1, 1, 0, 0, 0)
    >>>tr = tr.slice(ref-seconds,ref+seconds)

    :type st: :class:`~obspy.core.stream.Stream`
    :param st: ObsPy ``Stream`` object to be saved
    :type base_name: string
    :param base_name: Common "root" for every generated filename.
        It must not include underscores.
    :type base_dir: directory
    :param base_dir: Path where to save the files
    :type suffix: string
    :param suffix: Optional suffix for the filename
    :type seconds: int (Optional)
    :param seconds: How many seconds to retain of the original trace
    :type is_corr: bool (Optional)
    :param is_corr: If True the seconds
    """

    if not isinstance(st, Stream):
        raise TypeError("st must be an obspy Stream object.")

    if base_dir is None or not os.path.isdir(base_dir):
        base_dir = os.getcwd()

    if base_name is None or base_name == "":
        base_name = 'trace'

    for tr in st:
        # It is less efficient to do that trace by trace but we do not know
        # if all of them have the same starting time or not.
        if seconds != 0:
            if not is_corr:
                tr = tr.slice(tr.stats.starttime,
                              tr.stats.starttime + seconds)
            else:
                t_start = UTCDateTime(1971, 1, 1, 0, 0, 0) - seconds
                t_stop = UTCDateTime(1971, 1, 1, 0, 0, 0) + seconds
                tr.trim(t_start, t_stop)

        filename = base_name + '_' + tr.id.replace('-', '')

        if suffix is not None and suffix != '':
            filename += '_' + suffix

        # filename += '_'

        mat_struct = {}

        t = UTCDateTime(0)

        if hasattr(tr, 'stats_tr1'):

            t = max(t, tr.stats_tr1.starttime)

            _tr1dict = {'network': tr.stats_tr1.network,
                        'station': tr.stats_tr1.station,
                        'location': tr.stats_tr1.location,
                        'channel': tr.stats_tr1.channel,
                        'sampling_rate': tr.stats_tr1.sampling_rate,
                        'starttime': '%s' % tr.stats_tr1.starttime,
                        'endtime': '%s' % tr.stats_tr1.endtime,
                        'npts': long(tr.stats_tr1.npts)}
            if 'sac' in tr.stats_tr1:
                _tr1dict['stla'] = tr.stats_tr1.sac.stla
                _tr1dict['stlo'] = tr.stats_tr1.sac.stlo
                _tr1dict['stel'] = tr.stats_tr1.sac.stel

            mat_struct['stats_tr1'] = _tr1dict

        if hasattr(tr, 'stats_tr2'):

            t = max(t, tr.stats_tr2.starttime)

            _tr2dict = {'network': tr.stats_tr2.network,
                        'station': tr.stats_tr2.station,
                        'location': tr.stats_tr2.location,
                        'channel': tr.stats_tr2.channel,
                        'sampling_rate': tr.stats_tr2.sampling_rate,
                        'starttime': '%s' % tr.stats_tr2.starttime,
                        'endtime': '%s' % tr.stats_tr2.endtime,
                        'npts': long(tr.stats_tr2.npts)}
            if 'sac' in tr.stats_tr2:
                _tr2dict['stla'] = tr.stats_tr2.sac.stla
                _tr2dict['stlo'] = tr.stats_tr2.sac.stlo
                _tr2dict['stel'] = tr.stats_tr2.sac.stel

            mat_struct['stats_tr2'] = _tr2dict

        if hasattr(tr, 'stats'):

            _stats = {'network': tr.stats.network,
                      'station': tr.stats.station,
                      'location': tr.stats.location,
                      'channel': tr.stats.channel,
                      'sampling_rate': tr.stats.sampling_rate,
                      'starttime': '%s' % tr.stats.starttime,
                      'endtime': '%s' % tr.stats.endtime,
                      'npts': long(tr.stats.npts)}
            if 'sac' in tr.stats:
                _stats['stla'] = tr.stats.sac.stla
                _stats['stlo'] = tr.stats.sac.stlo
                _stats['stel'] = tr.stats.sac.stel
                if np.all(map(lambda x: x in tr.stats.sac, \
                              ['evla', 'evlo', 'evel', 'az', 'baz', 'dist'])):
                    _stats['evla'] = tr.stats.sac.evla
                    _stats['evlo'] = tr.stats.sac.evlo
                    _stats['evel'] = tr.stats.sac.evel
                    _stats['az'] = tr.stats.sac.az
                    _stats['baz'] = tr.stats.sac.baz
                    _stats['dist'] = tr.stats.sac.dist

            mat_struct['stats'] = _stats

        mat_var_name = 'corr_trace'
        mat_struct[mat_var_name] = tr.data

        time = '%s' % t
        time = time.replace('-', '').replace('.', '').replace(':', '')
        sio.savemat(os.path.join(base_dir, time + '_' + filename), mat_struct,oned_as='column')


if BC_UI:
    class _convert_to_matlab_view(HasTraits):
        base_name = Str('trace')
        suffix = Str('')
        base_dir = Directory('./')
        seconds = Int(300)
        is_corr = Bool(True)
    
        trait_view = View(Item('base_name'),
                          Item('suffix'),
                          Item('base_dir'),
                          Item('seconds'),
                          Item('is_corr')
                          )


X = None


def stack(vect, axis):
    """ Stacks together arrays of compatible size.

    This function stacks (pile up) array with compatible size to create a
    matrix. This stack can be done row-wise (``axis=0``) or column-wise
    (``axis=1``). To achieve this behaviour in a function based environment
    like blockcanvas, it uses a ``global`` variable that persist between
    successive call to this routine.
    It must be taken into account that this global variable needs to be
    reseted by hand if it is necessary to restart the piling procedure
    (see also the function ``clear_global_X``).

    :type vect: :class:`~numpy.ndarray`
    :param vect: 1D Array to stack with the current global variable ``X``
    :type axis: int
    :param axis: Stacking axis. 0: row-wise, 1: column-wise

    :rtype X: :class:`~numpy.ndarray`
    :return: **X**: Global variable that holds the stacked data
    """

    global X

    if X is None:
        if axis == 0:
            X = np.reshape(vect, (1, vect.size))
        elif axis == 1:
            X = np.reshape(vect, (vect.size, 1))
        return X
    else:
        try:
            if axis == 0:
                X = np.vstack([X, vect.reshape((1, vect.size))])
            elif axis == 1:
                X = np.hstack([X, vect.reshape((vect.size, 1))])

        except Exception, e:
            print "Exception occurred stacking data!!!"
            print "Exception: %s" % e

            if axis == 0:
                fv = np.ones((1, X.shape[1])) * np.NaN
                X = np.vstack([X, fv])
            elif axis == 1:
                fv = np.ones((X.shape[0], 1)) * np.NaN
                X = np.hstack([X, fv])
            pass

    return X


if BC_UI:
    class _stack_view(HasTraits):
    
        axis = Enum([0, 1])
        trait_view = View(Item('axis',
                               label='along axis 0:columnwise 1:rowwise'))
    

def clear_global_X():
    """ Reset the global variable ``X`` to None """
    global X

    if X is not None:
        X = None


def submat_x(X, low_x, high_x):
    """ Extract a sub-matrix from a matrix ``X`` along the x-axis (columns) """
    subX = X[:, low_x:high_x]
    return subX


if BC_UI:
    class _submat_x_view(HasTraits):
        low_x = Int
        high_x = Int
    
        trait_view = View(Item('low_x'),
                          Item('high_x'))
    

def submat_y(X, low_y, high_y):
    """ Extract a sub-matrix from a matrix ``X`` along the y-axis (rows).
    """
    subY = X[low_y:high_y, :]
    return subY


if BC_UI:
    class _submat_y_view(HasTraits):
        low_y = Int
        high_y = Int
    
        trait_view = View(Item('low_y'),
                          Item('high_y'))
    

def nd_mat_center_part(ndmat, win_len, axis=0):
    """ Extract the "central" part of a matrix.

    Extract the "central" part of size ``win_len`` from a matrix ``X`` along
    the specified axis. The center is the sample with zero referenced index
    floor((X.shape[axis]-1)/2). If ``win_len`` is an even number the center in
    the output will similarily be at floor((win_len-1)/2).

    :type ndmat: :class:`~numpy.ndarray`
    :param ndmat: matrix to take the central part
    :type win_len: int
    :param win_len: central windows length
    :type axis: int
    :param axis: axis where to act
    """
    row, col = ndmat.shape
    row = float(row)
    col = float(col)

    if axis == 0:
        center = np.floor((row - 1.) / 2.)
        lower = np.max([0, center - np.floor(float(win_len - 1) / 2)])
        upper = np.min([row, lower + win_len])
        cent_mat = ndmat[lower:upper, :]
    else:
        center = np.floor((col - 1.) / 2.)
        lower = np.max([0, center - np.floor(float(win_len - 1) / 2)])
        upper = np.min([col, lower + win_len])
        cent_mat = ndmat[:, lower:upper]
    print "lower: %d\ncenter: %d\nupper: %d" % (lower, center, upper)
    return cent_mat


if BC_UI:
    class _nd_mat_center_part_view(HasTraits):
        win_len = Int(100)
        axis = Enum(0, 1)
    
        trait_view = View(Item('win_len'),
                          Item('axis'))


def matrix_product(A, B):
    """ Simple matrix product using np.dot """
    C = np.dot(A, B)
    return C


if BC_UI:
    class _matrix_product_view(HasTraits):
        trait_view = View()


def collapse_to_single_vect(X, axis, select_portion=False, first_line=0, \
                            last_line=100):
    """ Collapse a matrix to a single normalized vector along a defined axis.

    The normalizing factor is equal to the number of points in the chosen axis
    (i.e. when ``axis=0`` it collapse the matrix ``X`` to a single row
    obtained summing column-wise and dividing each sample by the number of
    rows of ``X``).
    It is also possible to control how many rows/columns will be collapsed
    passing ``select_portion==True`` and the two index ``first_line=0`` and
    ``last_line=100``: Only the 100 rows/columns in the passed interval will
    be collapsed.

    :type X: :class:`~numpy.ndarray`
    :param X: 2D array to collapse to 1D
    :type axis: int
    :param axis: Collapsing axis. 0: row-wise, 1: column-wise
    :type select_portion: bool
    :param select_portion: If collapse a certain numbers of lines instead of
        the whole matrix
    :type first_line: int
    :param first_line: If ``selected_portion==True`` it says at which index
        starting selecting lines to collapse
    :type last_line: int
    :param last_line: If ``selected_portion==True`` it says at which index
        ending selecting lines to collapse

    :rtype: :class:`~numpy.ndarray`
    :return: **coll_array**: 1D array
    """
    if axis == 0 and select_portion:
        X = X[first_line:last_line, :]
    elif axis == 1 and select_portion:
        X = X[:, first_line:last_line]

    if axis == 0:
        denom = X.shape[0]
    else:
        denom = X.shape[1]

    coll_array = np.nansum(X, axis=axis) / denom
    return coll_array


if BC_UI:
    class _collapse_to_single_vect_view(HasTraits):
        
        axis = Enum([0, 1])
        select_portion = Bool(False)
        first_line = Int(0)
        last_line = Int(100)
    
        trait_view = View(Item('axis',
                               label='axis (0:row-wise, 1:col-wise)'),
                          Item('select_portion'),
                          Item('first_line', enabled_when='select_portion==True'),
                          Item('last_line', enabled_when='select_portion==True'))


def find_comb(base_dir, suffix='', is_mat=False):
    """ Find all possible combinations written in the filenames

    Checks all the filenames in a directory to find all possible
    combinations of stations that have been created.
    """
    f_pattern = '*.mat'
    files_list1 = dir_read(base_dir, pattern=f_pattern, sort_flag=True)

    comb = []
    for file_full_name in files_list1:
        _, filename = os.path.split(file_full_name)
        filename, _ = os.path.splitext(filename)
        filename_parts = filename.split('_')
        if suffix != '':
            filename_parts = filename_parts[:-1]
        if is_mat:
            filename_parts = filename_parts[1:]
        else:
            filename_parts = filename_parts[2:]
        ccomb = ('_').join(filename_parts)
        if ccomb not in comb:
            comb.append(ccomb)
    return comb


def split_file(filename):
    gday = filename.split('_', 1)[0]
    ctime = gday.split('-')
    cdate = datetime.date(int(ctime[0]), int(ctime[1]), int(ctime[2]))
    return cdate


def from_str_to_datetime(str_date, datetimefmt=False):
    """Convert a dash separated string date in a datetime object."""
    ctime = str_date.split('-')
    if datetimefmt:
        cdate = datetime.datetime(int(ctime[0]), int(ctime[1]), int(ctime[2]))
    else:
        cdate = datetime.date(int(ctime[0]), int(ctime[1]), int(ctime[2]))
    return cdate


def extract_time_vect(base_dir, pattern):
    """ Extract time vector from filenames.

    Extract the time vector relative to a group of files stored in the same
    directory with a standatd filename:
    "Year"_"trace"_"pattern"+".mat"
    """
    f_pattern = '*' + pattern + '*.mat'
    files_list1 = dir_read(base_dir=base_dir, pattern=f_pattern, \
                           sort_flag=True)

    time_vect = []
    for celem1 in files_list1:
        _, f_name = os.path.split(celem1)
        time_vect.append(split_file(f_name))
    return time_vect


def norm1(X, axis):
    """ Matrix normalization.

    Normalize each row (column) of a matrix dividing it by the reference array
    obtained summing the matrix row-wise (column-wise).
    """
    denom = X.sum(axis=axis)
    if denom is not 0:
        if axis == 0:
            X = X / denom
        else:
            app = X.T / denom
            X = app.T

    return X


def transpose(X):
    """ Transpose the matrix ``X`` """
    return X.T


if BC_UI:
    class _transpose_view(HasTraits):
        trait_view = View()


def reshape_mat_to_vect(X, axis):
    """ Reshape the matrix elements to obtain a 1D array.

    If ``axis==0`` the returned 1D array is a row vector of shape [1,X.size]
    otherwise , when ``axis==1``, it is a column vector of shape [X.size,1]
    """

    if axis == 0:
        vec_x = X.reshape([1, X.size])
    elif axis == 1:
        vec_x = X.reshape([X.size, 1])

    return vec_x


if BC_UI:
    class _reshape_mat_to_vect_view(HasTraits):
        
        axis = Enum([0, 1])
    
        trait_view = View(Item('axis',
                               label='axis (0:col, 1:row)'))
    

def nd_nan_to_num(x):
    """ Replace NaNs with 0 and +-Inf with +-large number.
    """
    x_clean = np.nan_to_num(x)

    return x_clean


def datetime_list(start, end, inc=86400.):
    """ Create a list of datetime objects.

    Create a list of regularly spaces :class:~`datetime.datetime` objects.
    The first element is ``start`` and the last element is smaller than
    ``end``. The distance between elements is ``inc``

    :type start: :class:~`datetime.datetime` object or string as defined in
        miic.core.miic_utils.convert_time.
    :param start: first elemet of list
    :type end: :class:~`datetime.datetime` object or string as defined in
        miic.core.miic_utils.convert_time.
    :param end: termiation of list
    :type inc: float
    :param inc: spacing between elements in seconds

    :rtype time_list: list
    :return: **time_list**: list of datetime objects

    """

    start_date = convert_time([start])[0]
    end_date = convert_time([end])[0]

    date_inc = datetime.timedelta(seconds=inc)

    time_list = [start_date]
    next_t = time_list[-1] + date_inc

    while next_t < end_date:
        time_list.append(next_t)
        next_t = time_list[-1] + date_inc

    return time_list


if BC_UI:
    class _datetime_list_view(HasTraits):
        start = Str("2000-01-01")
        end = Str("2001-01-01")
        inc = Float("86400.")
    
        trait_view = View(Item('start'),
                          Item('end'),
                          Item('inc'))


def combinations(n_trace, std_comb,k=0):
    """ Create the list of combinations.

    Create the list of possible combinations between a specified number
    of traces. Several different possibility are available:
    ``Auto-corr`` andgenerates a list of tuples of this form (n,n)
    ``Full-corr`` generates all the possible tuples of this form (n,m)
    where ``n!=m`` and ``0 <= n < n_trace`` and ``0 <= m < n_trace``.
    ``Single-corr``,k generates all the possible tuples of the form (n,k)
                  or (k,n) for n!=k, such that always the first number is smaller than the second.
                  If k<0 or >=n, return empty list

    :type n_trace: int
    :param n_trace: Number of traces
    :type std_comb: enum
    :param std_comb: Type of combination to generate. It can be one of:
            ['Auto-corr','Full-corr']

    :rtype: list of tuples
    :return: **comb**: List of possible combinations. For example,
        if ``n_trace==3`` and ``std_comb=='Auto-corr'`` ->
        comb = [(0,0),(1,1),(2,2)]

    """
    comb = []

    if std_comb == 'Auto-corr':
        for k in range(n_trace):
            comb.append((k, k))
    elif std_comb == 'Full-corr':
        comb = [(x, y) for x in range(n_trace) \
                       for y in range(x + 1, n_trace)]
    elif std_comb == 'Single-corr':
        if k>=0 and k<n_trace:
            comb = [(x, k) for x in range(k)]
            comb += [(k,x) for x in range(k+1,n_trace)]
        else:
            comb = []
    else:
        raise ValueError, "Unknown combination type %s" % std_comb
    return comb


if BC_UI:
    class _combinations_view(HasTraits):
    
        n_trace = Int
        std_comb = Enum('Auto-corr', 'Full-corr')
    
        _type_c = List
    
        trait_view = View(Item('n_trace'),
                          Item('std_comb',
                               enabled_when="s_type=='Standard'",
                               style='custom'),
                          Item('_type_c', style='readonly', label='Combinations'),
                          resizable=True, title='SELECTION',
                          buttons=['OK', 'Help'])
    
        def _reset(self):
            self._type_c = []
            self.custom_comb = []
    
        def _n_trace_changed(self, old, new):
            self._reset()
            self._type_c = combinations(self.n_trace, self.std_comb)
    
        def _std_comb_changed(self):
            self._reset()
            self._type_c = combinations(self.n_trace, self.std_comb)


def comb_with_missed_stations(n_stations, std_comb, missed_stations):
    """ Create the list of combinations.

    Create the list of possible combinations between a specified number
    of stations. Two different possibility are available: ``Auto-corr`` and
    ``Full-corr``. The former generates a list of tuples of this form (n,n)
    while the latter generates all the possible tuples of this form (n,m)
    where ``n!=m`` and ``0 <= n < n_trace`` and ``0 <= m < n_trace``.
    It handles missed stations so that every station listed in the
    ``missed_stations`` parameter will not be included in the final list of
    combinations.

    :type n_trace: int
    :param n_trace: Number of traces
    :type std_comb: enum
    :param std_comb: Type of combination to generate. It can be one of:
            ['Auto-corr','Full-corr']
    :type missed_stations: list
    :param missed_stations: Missed stations list (e.g. [2,5,6])

    :rtype: list of tuples
    :return: **comb**: List of possible combinations. For example,
        if ``n_trace==3`` and ``std_comb=='Auto-corr'`` ->
        comb = [(0,0),(1,1),(2,2)]
    """
    comb = []

    if std_comb == 'Auto-corr':
        for k in range(n_stations):
            comb.append((k, k))
    elif std_comb == 'Full-corr':
        comb = [(x, y) for x in range(n_stations) \
                       for y in range(x + 1, n_stations) \
                       if x not in missed_stations and \
                       y not in missed_stations]
    return comb


def nd_save(filename, var):
    """ Save an ndarray in the original NumPy format.
    """
    np.save(filename, var)


if BC_UI:
    class _nd_save_view(HasTraits):
        filename = File()
        trait_view = View(Item('filename'))


def nd_load(filename):
    """ Load an ndarray from a file in NumPy format (.npy)
    """
    return np.load(filename)


if BC_UI:
    class _nd_load_view(HasTraits):
        filename = File()
        trait_view = View(Item('filename'))


def nd_toList(ndv):
    """ Convert a numpz arraz to a list """
    list_a = ndv.tolist()
    return list_a


def load_matlab_file(filename):
    """ Load variables from MatLab file.

    Load all variables stored in a MatLab (.mat) file and return them
    as a dictionary with the keys being the name of the variables. The
    functionality is based on :class:`~scipy.io.loadmat` and inherits
    its capabilities and limitations.

    :type filename: string
    :param filename: Name of the file to be loaded.

    :rtype: dictionary
    :return: **mat_vars**: dictionary holding the variables found in the file.
        The key is the name of the variable.
    """
    mat_vars = loadmat(file_name=filename)
    return mat_vars


if BC_UI:
    class _load_matlab_file_view(HasTraits):
        filename = File()
        trait_view = View(Item('filename'))


def enum_list(ls):
    """ Enumerate a list """
    ls_enum = enumerate(ls)
    return ls_enum


def to_str(var):
    """ Convert a variable to string """
    svar = str(var)
    return svar


def nd_size(nda):
    """ Return and print the shape of an ndarray """
    row, col = nda.shape
    print "row: %d" % row
    print "col: %d" % col
    return row, col


def fold_acausal(X):
    """ Fold the acausal part of an Auto/Cross corr. matrix and mirror it """
    X[:, X.shape[1] / 2:] = (X[:, X.shape[1] / 2:] + \
                             X[:, :X.shape[1] / 2][:, ::-1]) / 2
    X_fol = np.hstack((X[:, X.shape[1] / 2:][::-1], X[:, X.shape[1] / 2:]))
    return X_fol


if BC_UI:
    class _fold_acausal_view(HasTraits):
        trait_view = View()



def lat_lon_ele_load(filename):
    """ Load lat lon and ele from a tab delimited file.

    This function load lat, lon and ele from a tab delimited file into a
    pandas DataFrame so that those informaiton can be retrived using its
    wide capabilities.

    :type filename: full path filename
    :param filename: The file to load

    :rtype: :class:`~pandas.DataFrame`
    :return: **df**: Pandas DataFrame with stations name as index and lat, lon,
        ele as columns
    """

    df = read_table(filename, index_col=0)

    return df


if BC_UI:
    class _lat_lon_ele_load_view(HasTraits):
    
        filename = File
    
        trait_view = View(Item('filename'))


def trace_calc_az_baz_dist(tr1, tr2):
    """ Return azimut, back azimut and distance between tr1 and tr2
    This funtions calculates the azimut, back azimut and distance between tr1
    and tr2 if both have geo information in their stats dictonary.
    Required fields are:
        tr.stats.sac.stla
        tr.stats.sac.stlo

    :type tr1: :class:`~obspy.core.trace.Trace`
    :param tr1: First trace to account
    :type tr2: :class:`~obspy.core.trace.Trace`
    :param tr2: Second trace to account

    :rtype: float
    :return: **az**: Azimut angle between tr1 and tr2
    :rtype: float
    :return: **baz**: Back azimut angle between tr1 and tr2
    :rtype: float
    :return: **dist**: Distance between tr1 and tr2
    """

    if not isinstance(tr1, Trace):
        raise TypeError("tr1 must be an obspy Trace object.")

    if not isinstance(tr2, Trace):
        raise TypeError("tr2 must be an obspy Trace object.")

    try:
        from obspy.geodetics import gps2dist_azimuth 
    except ImportError:
        print "Missed obspy funciton gps2dist_azimuth"
        print "Update obspy."
        return

    dist, az, baz = gps2dist_azimuth(tr1.stats.sac.stla, \
                                     tr1.stats.sac.stlo, \
                                     tr2.stats.sac.stla, \
                                     tr2.stats.sac.stlo)

    return az, baz, dist


if BC_UI:
    class _trace_calc_az_baz_dist_view(HasTraits):
        trait_view = View()


def nextpow2(n):
    """ Return the smalest integer number larger than ``n`` that is a power
    of 2.
    """
    m_f = np.log2(n)
    m_i = np.ceil(m_f)
    return (2 ** m_i).astype(int)


##############################################################################
# Data handling                                                              #
##############################################################################


def select_item_from_list(in_list, item_pos=0):
    """ Select a specified item from a list.

    Select the ``item_pos`` element from the list ``in_list`` and return it.

    :type in_list: list
    :param in_list: list from which item is to be extracted
    :type item_pos: int
    :param item_pos: position of the item to be extracted from the list

    :rtype: item
    :return: **item**: item_pos element of the list
    """

    # check input
    if not isinstance(in_list, list):
        raise TypeError('input variable in_list is not a list.')

    item = in_list[item_pos]

    return item


if BC_UI:
    class _select_item_from_list_view(HasTraits):
        item_pos = Int(0)
        trait_view = View(Item('item_pos'))
    

def select_var_from_dict(dictionary, key):
    """ Select variable from dictionary.

    Select a variable (value) associated to the key ``key``
    from a dictionary and return the variable.

    :type dictionary: dictionary
    :param dictionary: dictionary holding the variable in associated to the
            key ``key``
    :type key: string
    :param key: name of the key associated to the varable to select

    :rtype: variable
    :return: **variable**: variable stored associated to the key ``key``.
    """

    # check input
    if not isinstance(dictionary, dict):
        raise TypeError('input variable dictionary is not a dictionary.')

    if not key in dictionary.keys():
        print 'InputError: dictionary has no key key'

    return dictionary[key]


if BC_UI:
    class _select_var_from_dict_view(HasTraits):
        key = Str()
        trait_view = View(Item('key'))


def add_var_to_dict(key, variable, dictionary=None):
    """ Add a variable to a dictionary.

    Add a variable to a dictionary as value associated to the key ``key``.

    :type dictionary: dict
    :param dictionary: dictionary to which the variable should be added.
        If None a new dictionary is created.
    :type key: str
    :param key: name of the key to which the vradiable is to be associated
            with.
    :type variable: any
    :param data that should be added to the dictionary

    :rtype: dict
    :return: **dictionary**: extended or new dictionary.
    """

    if not isinstance(dictionary, dict):
        raise TypeError('input variable dictionary is not a dictionary.')

    if not isinstance(key, str):
        raise TypeError('input variable key must be a string.')

    # check input
    if dictionary is None:
        dictionary = {}

    dictionary[key] = variable

    return dictionary


if BC_UI:
    class _add_var_to_dict_view(HasTraits):
        key = Str()
        trait_view = View(Item('string'))


def print_keys_from_dict(dictionary):
    """ Print the keys present in a dictionary.

    Print the keys present in dictionary ``dictionary`` and return the list
    a dictionary holding the list of keys and the type of the associated data.

    :type dictionary: dict
    :param dictionary: dictionary of which the keys are to be printed

    :rtype: key_list
    :return: **key_list**: dictionary holding a list of the keys and the data
             types
    """

    # check input
    if not isinstance(dictionary, dict):
        raise TypeError('input variable dictionary is not a dictionary.')

    key_list = {'keys': [], 'types': []}
    # print the keys
    for key in dictionary.keys():
        key_list['keys'].append(key)
        key_list['types'].append(type(dictionary[key]))
        print '%s : %s' % (key, type(dictionary[key]))

    return key_list


if BC_UI:
    class _print_keys_from_dict_view(HasTraits):
        trait_view = View()


def save_dict_to_matlab_file(filename, dictionary):
    """ Save a dictionary to a matlab file.

    Save values stored in a dictionary as variables having the name of the key
    in a matlab file.

    :type dicitonary: dict
    :param dictionary: dicitonary to be saved
    :type filename: str
    :param filename: name of the matlab file to be created
    """

    #print 'saving to %s' % filename
    savemat(filename, dictionary, oned_as='row')

    return


if BC_UI:
    class _save_dict_to_matlab_file_view(HasTraits):
        filename = Str()
        trait_view = View(Item('filename'))


def convert_time(time_vect):
    """ Convert a list/array of timestaps in a array of datetime.datetime obj

    This fucntion does the conversion of a list/array of string in a list/array
    of :class:`~datetime.datetime` objects. The time format allowed for the
    string representation is one of:
    - %Y-%m-%dT%H:%M:%S.%fZ
    - %Y-%m-%d %H:%M:%S.%f
    - %Y-%m-%d %H:%M:%S
    - %Y-%m-%d

    :type time_vect: list or :class:`~numpy.ndarray` of String
    :param time_vect: List/array of timestamp in string format.

    :rtype: :class:`~numpy.ndarray` of :class:`~datetime.datetime` objs
    :return: Array of :class:`~datetime.datetime` objects
    """

    if isinstance(time_vect[0], datetime.datetime):
        rtime = np.array(time_vect)
        return rtime

    if type(time_vect) is np.ndarray:
        time_vect = time_vect.tolist()

    rtime = []
    for t in time_vect:
        try:
            ctime = datetime.datetime.strptime(t.strip(),
                                              "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            try:
                ctime = datetime.datetime.strptime(t.strip(),
                                               "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    ctime = datetime.datetime.strptime(t.strip(),
                                                  "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        ctime = datetime.datetime.strptime(t.strip(),
                                                           "%Y-%m-%d")
                    except Exception, e:
                        print e
                        print "Time format error"
                        return None

        rtime.append(ctime)
    rtime = np.array(rtime)
    return rtime


if BC_UI:
    class _convert_time_view(HasTraits):
        trait_view = View()


def convert_time_to_string(time_vect):
    """Convert a list/array of datetime.datetime obj to an array of strings

    This fucntion does the conversion of a list/array of
    of :py:class:`~datetime.datetime` objects to an array of time strings of
    the format of the format %Y-%m-%d %H:%M:%S.%f.
    The list/array of time strings must have a format know to
    :py:class:``~miic.core.miic_utils.convert_time``.

    :type time_vect: :class:`~numpy.ndarray` of :py:class:`~datetime.datetime`
        objs or timestamps in string format
    :param time_vect: List/Array of time stamps

    :rtype: :class:`~numpy.ndarray` of String
    :return: Array of timestamp in string format.
    """

    rtime = []
    if not isinstance(time_vect[0], datetime.datetime):
        time_vect = convert_time(time_vect)

    for t in time_vect:
        rtime.append(t.strftime("%Y-%m-%d %H:%M:%S.%f"))

    rtime = np.array(rtime)
    return rtime


if BC_UI:
    class _convert_time_to_string_view(HasTraits):
        trait_view = View()


def correlation_subdir_name(date):
    """Create the path name to a sub folder with YEAR/JDAY format

    The path will have the following structure:
    YEAR/JDAY
    
    :type date: datetime.datetime or obspy.UTCDateTime
    :param date: date of the data
    
    :rtype: str
    :return: name of subpath
    """

    if isinstance(date,UTCDateTime):
        date = date.datetime

    subpath = os.path.join(str(date.year),"%03d" % date.timetuple().tm_yday)

    return subpath



def serial_date_from_datetime(dt):
    """ Converts a datetime.datetime object into a number as toordinal but
    including seconds.
    """

    sd = dt.toordinal() + float(dt.hour)/24 + float(dt.minute)/1440 + \
        (float(dt.second)+float(dt.microsecond)/1000000)/86400
    return sd


def flatten(x):
    """ Return the flattened version of the input array x

    This funciton works with all :class:`~collections.Iterable` that can be
    nested in an irregular fashion.

    .. rubric: Example

    >>>L=[[[1, 2, 3], [4, 5]], 6]
    >>>flatten(L)
    [1, 2, 3, 4, 5, 6]

    :type x: :class:`~collections.Iterable`
    :param: Iterable to be flattened

    :rtype: list
    :return: x as a flattened list
    """
    result = []
    for el in x:
        if isinstance(el, collections.Iterable) and \
            not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


if BC_UI:
    class _flatten_view(HasTraits):
        trait_view = View()


def flatten_recarray(x):
    """ Flatten a recarray
    """
    flat_dict = {}
    if hasattr(x, 'dtype'):
        if hasattr(x.dtype, 'names'):
            if x.dtype.names is not None:
                for name in x.dtype.names:
                    field = flatten(x[name])
                    if field != []:
                        flat_dict.update({name: field[0]})
                    else:
                        flat_dict.update({name: field})
                return flat_dict
    return x


def save_dv(dv, suffix, save_dir, pattern=''):
    """ Save dv dictionary

    Note: Masked array have to be considered with care because masked
        values will be substituted with the associated ``fill_value``
        of the corresponding object.
    """
    if dv_check(dv)['is_incomplete']:
        raise ValueError("Error: dv is not a valid dv dictionary.")

    # Adjust masked arrays. It is better to do that explicitely than
    # relay on the save function
    for key in dv.keys():
        if isinstance(dv[key], np.ndarray):
            try:
                dv[key] = dv[key].filled()
            except:
                pass

    if pattern == '':

        stats = flatten_recarray(dv['stats'])

        # Fix the problem of havin empty list instead of empty strings
        for key in stats:
            if stats[key] == []:
                stats[key] = ''

        pattern = stats['network'].replace('-', '') + '.' + \
                  stats['station'].replace('-', '') + '.' + \
                  stats['location'].replace('-', '') + '.' + \
                  stats['channel'].replace('-', '')

    if suffix != '':
        vchange_file_name = 'vchange_full_' + \
            pattern + '_' + suffix + '.mat'
    else:
        vchange_file_name = 'vchange_full_' + pattern + '.mat'

    savemat(os.path.join(save_dir, vchange_file_name), dv, oned_as='column')


if BC_UI:
    class _save_dv_view(HasTraits):
    
        save_dir = Directory()
        suffix = Str('')
        pattern = Str('PFPF.UV05UV12.0000.HHZHHZ')
        use_pattern = Bool(False)
    
        trait_view = View(Item('suffix', label='filename suffix'),
                          Item('save_dir'),
                          Item('use_pattern'),
                          Item('pattern',
                               label='Pattern (optional)',
                               enabled_when='use_pattern'))


def _timestamp(dt):
    return time.mktime(dt.timetuple()) + dt.microsecond / 1000000.0
    

def _stats_dict_from_obj(stats):
    """ Convert the obspy stats object to a dictionary used by miic
  
    """  
    stats_dict = {'network': stats.network,
                'station': stats.station,
                'location': stats.location,
                'channel': stats.channel,
                'sampling_rate': stats.sampling_rate,
                'starttime': '%s' % stats.starttime,
                'endtime': '%s' % stats.endtime,
                'npts': long(stats.npts)}
    if 'sac' in stats:
        stats_dict['stla'] = stats.sac.stla
        stats_dict['stlo'] = stats.sac.stlo
        stats_dict['stel'] = stats.sac.stel
        if np.all(map(lambda x: x in stats.sac,
                    ['evla', 'evlo', 'evel', 'az', 'baz', 'dist'])):
             stats_dict['evla'] = stats.sac.evla
             stats_dict['evlo'] = stats.sac.evlo
             stats_dict['evel'] = stats.sac.evel
             stats_dict['az'] = stats.sac.az
             stats_dict['baz'] = stats.sac.baz
             stats_dict['dist'] = stats.sac.dist
    
    return stats_dict 


def _check_stats(stats):

    ERRORS = []

    stats = flatten_recarray(stats)

    # Check the timing
    starttime = convert_time([stats['starttime']])[0]
    endtime = convert_time([stats['endtime']])[0]
    npts = stats['npts']
    fs = stats['sampling_rate']

    if starttime > endtime:
        ERRORS.append("starttime greater then endtime")
        return ERRORS

    # Delta T in seconds
    delta = _timestamp(endtime) - _timestamp(starttime)
    expected_npts = delta * fs + 1

    if not np.allclose(expected_npts, npts, atol=1.):
        ERRORS.append("npts not consistent with starttime, \
            endtime and sampling_rate")
        return ERRORS

    return None


def _check_dict(d, keys_class):

    is_incomplete = False
    missed_keys = []
    wrong_classes = []
    for (key, cclass) in keys_class:
        if key not in d:
            is_incomplete = True
            missed_keys.append(key)
        else:
            # Check class
            if not isinstance(d[key], cclass):
                wrong_classes.append(key)

    return is_incomplete, missed_keys, wrong_classes


def corr_check(corr_fun_struct):
    """ Correlation function dictionary check

    This function test if the a loaded correlation function dictionary
    contains the requested keywords and if their corresponding value is of the
    proper class to continue the processing, e.g., recombining then to form a
    correlation matrix.

    Actually the requested keywords are:
        'corr_trace'  (not for the old_style corr_fun)
        'stats'
        'stats_tr1'
        'stats_tr2'

    and their class is, for all of them, :py:class:`numpy.ndarray`.
    The three "stats" objects are also checked for some "main" errors like
    the starttime greather then the endtime or a substaintial (greater then 1
    sample) disagreement between starttime, endtime, sampling_rate and npts.

    :type corr_fun_struct: dict
    :param corr_fun_struct: Correlation function dictionary

    :rtype: dict
    :return: **ret_dict**: dictionary that contains the following keys:
        *is_incomplete*: True if a keyword is missed
        *missed_keys*: list of missed keywords
        *wrong_class*: list of keyworkds which value is of a wrong class
        *ERROR_stats*: list of errors (strings) detected in the 'stats' object
        *ERROR_stats_tr1*: list of errors (strings) detected in the
            'stats_tr1' object
        *ERROR_stats_tr2**: list of errors (strings) detected in the
            'stats_tr2' object

    ... rubric:: Notes

    If the correlation function have been saved to a matlab file and than
    reloaded, it is supposed that the stats onìbjects have been flattened.
    For instance, this can be achieved doing the reload with the function
    :py:func:`~miic.core.miic_utils.mat_to_ndarray` setting the flag
    flatten to True (this is the default value)
    """
    keys = ['corr_trace', 'stats', 'stats_tr1', 'stats_tr2']

    klass = [np.ndarray, dict, dict, dict]

    is_incomplete, missed_keys, wrong_classes = \
        _check_dict(corr_fun_struct, zip(keys, klass))

    ERROR_stats = None
    if ('stats' not in missed_keys) and ('stats' not in wrong_classes):
        ERROR_stats = _check_stats(corr_fun_struct['stats'])

    ERROR_stats_tr1 = None
    if ('stats_tr1' not in missed_keys) and ('stats_tr1' not in wrong_classes):
        ERROR_stats_tr1 = _check_stats(corr_fun_struct['stats_tr1'])

    ERROR_stats_tr2 = None
    if ('stats_tr2' not in missed_keys) and ('stats_tr2' not in wrong_classes):
        ERROR_stats_tr2 = _check_stats(corr_fun_struct['stats_tr2'])

    ret_dict = {}
    ret_dict['is_incomplete'] = is_incomplete
    ret_dict['missed_keys'] = missed_keys
    ret_dict['wrong_classes'] = wrong_classes
    ret_dict['ERROR_stats'] = ERROR_stats
    ret_dict['ERROR_stats_tr1'] = ERROR_stats_tr1
    ret_dict['ERROR_stats_tr2'] = ERROR_stats_tr2

    return ret_dict


def spectrogram_check(spectrogram):
    """ Spectrogram dictionary check

    This function test if the a loaded spectrogram dictionary
    contains the requested keywords and if their corresponding value is of the
    proper class to continue the processing.
    
    the requested keywords and the corresponding types are:
        'spec_mat' : :py:class:`numpy.ndarray`
        'stats'    : dictionary of type stats
        'frequency': :py:class:`numpy.ndarray`
        'time'       :py:class:`numpy.ndarray`
        'unit'     : string
    
    :type spectrogram: dict
    :param spectrogram: Spectrogram dictionary

    :rtype: dict
    :return: **ret_dict**: dictionary that contains the following keys:
        *is_incomplete*: True if a keyword is missed
        *missed_keys*: list of missed keywords
        *wrong_class*: list of keyworkds which value is of a wrong class
        *ERROR_stats*: list of errors (strings) detected in the 'stats' object
    """

    keys = ['spec_mat', 'stats', 'frequency', 'time', 'unit']

    klass = [np.ndarray, dict, np.ndarray, np.ndarray, np.ndarray]

    is_incomplete, missed_keys, wrong_classes = \
        _check_dict(spectrogram, zip(keys, klass))

    ERROR_stats = ['']
    if ('stats' not in missed_keys) and ('stats' not in wrong_classes):
        ERROR_stats = _check_stats(spectrogram['stats'])

    ret_dict = {}
    ret_dict['is_incomplete'] = is_incomplete
    ret_dict['missed_keys'] = missed_keys
    ret_dict['wrong_classes'] = wrong_classes
    ret_dict['ERROR_stats'] = ERROR_stats
    if not (missed_keys or wrong_classes or ERROR_stats):
        ret_dict['valid'] = True
    else:
        ret_dict['valid'] = False

    return ret_dict


def corr_mat_check(corr_mat_struct):
    """ Correlation matrix dictionary check

    This function test if the a loaded correlation matrix dictionary
    contains the requested keywords and if their corresponding value is of the
    proper class to continue the processing, e.g., to calcule the velocity
    change.

    Actually the requested keywords are:
        'corr_data'
        'stats'
        'stats_tr1'
        'stats_tr2'
        'time'

    and their class is, for all of them, :py:class:`numpy.ndarray`.
    The three "stats" objects are also checked for some "main" errors like
    the starttime greather then the endtime or a substaintial (greater then 1
    sample) disagreement between starttime, endtime, sampling_rate and npts.

    :type corr_mat_struct: dict
    :param corr_mat_struct: Correlation matrix dictionary

    :rtype: dict
    :return: **ret_dict**: dictionary that contains the following keys:
        *is_incomplete*: True if a keyword is missed
        *missed_keys*: list of missed keywords
        *wrong_class*: list of keyworkds which value is of a wrong class
        *ERROR_stats*: list of errors (strings) detected in the 'stats' object
        *ERROR_stats_tr1*: list of errors (strings) detected in the
            'stats_tr1' object
        *ERROR_stats_tr2**: list of errors (strings) detected in the
            'stats_tr2' object

    ... rubric:: Notes

    If the correlation matrices have been saved to a matlab file and than
    reloaded, it is supposed that the stats onìbjects have been flattened.
    For instance, this can be achieved doing the reload with the function
    :py:func:`~miic.core.miic_utils.mat_to_ndarray` setting the flag
    flatten to True (this is the default value)
    """
    keys = ['corr_data', 'stats', 'stats_tr1', 'stats_tr2', 'time']

    klass = [np.ndarray, dict, dict, dict, np.ndarray]

    is_incomplete, missed_keys, wrong_classes = \
        _check_dict(corr_mat_struct, zip(keys, klass))

    ERROR_stats = ['']
    if ('stats' not in missed_keys) and ('stats' not in wrong_classes):
        ERROR_stats = _check_stats(corr_mat_struct['stats'])

    ERROR_stats_tr1 = ['']
    if ('stats_tr1' not in missed_keys) and ('stats_tr1' not in wrong_classes):
        ERROR_stats_tr1 = _check_stats(corr_mat_struct['stats_tr1'])

    ERROR_stats_tr2 = ['']
    if ('stats_tr2' not in missed_keys) and ('stats_tr2' not in wrong_classes):
        ERROR_stats_tr2 = _check_stats(corr_mat_struct['stats_tr2'])

    ret_dict = {}
    ret_dict['is_incomplete'] = is_incomplete
    ret_dict['missed_keys'] = missed_keys
    ret_dict['wrong_classes'] = wrong_classes
    ret_dict['ERROR_stats'] = ERROR_stats
    ret_dict['ERROR_stats_tr1'] = ERROR_stats_tr1
    ret_dict['ERROR_stats_tr2'] = ERROR_stats_tr2

    return ret_dict


def dv_check(dv_dict):
    """ Velocity change dictionary check

    This function test if a loaded velocity change dictionary
    contains the requested keywords and if their corresponding value is of the
    proper class to continue the processing, e.g., to create a DataFrame.

    Actually the requested keywords -> class pairs are:
        'corr'            -> :py:class:`numpy.ndarray`
        'value'           -> :py:class:`numpy.ndarray`
        'time'            -> :py:class:`numpy.ndarray`
        'sim_mat'         -> :py:class:`numpy.ndarray`
        'stats'           -> dict
        'second_axis'     -> :py:class:`numpy.ndarray`
        'value_type'      -> basestring
        'method'          -> basestring

    The "stats" objects is also checked for some "main" errors like
    the starttime greather then the endtime or a substaintial (greater then 1
    sample) disagreement between starttime, endtime, sampling_rate and npts.

    :type dv_dict: dict
    :param dv_dict: Velocity change dictionary

    :rtype: dict
    :return: **ret_dict**: dictionary that contains the following keys:
        *is_incomplete*: True if a keyword is missed
        *missed_keys*: list of missed keywords
        *wrong_class*: list of keyworkds which value is of a wrong class
        *ERROR_stats*: list of errors (strings) detected in the 'stats' object

    ... rubric:: Notes

    If the dv dictionary have been saved to a matlab file and than
    reloaded, it is supposed that the stats onìbjects have been flattened.
    For instance, this can be achieved doing the reload with the function
    :py:func:`~miic.core.miic_utils.mat_to_ndarray` setting the flag
    flatten to True (this is the default value)
    """
    keys = ['corr', 'value', 'time', 'sim_mat', 'stats', \
            'second_axis', 'value_type', 'method']

    klass = [np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict, \
             np.ndarray, np.ndarray, np.ndarray]

    is_incomplete, missed_keys, wrong_classes = \
        _check_dict(dv_dict, zip(keys, klass))

    ERROR_stats = ['']
    if ('stats' not in missed_keys) and ('stats' not in wrong_classes):
        ERROR_stats = _check_stats(dv_dict['stats'])

    ret_dict = {}
    ret_dict['is_incomplete'] = is_incomplete
    ret_dict['missed_keys'] = missed_keys
    ret_dict['wrong_classes'] = wrong_classes
    ret_dict['ERROR_stats'] = ERROR_stats

    return ret_dict


def dcs_check(dcs_dict):
    """ Dv-Corr-Stats dictionary (dcs_dict) check

    This function test if a dcs dictionary contains the requested
    keywords and if their corresponding value is of the
    proper class to continue the processing, e.g., to do the inversion.

    Actually the requested keywords -> class pairs are:
        'dvP'             -> :py:class:`pandas.Panel`
        'corrP'           -> :py:class:`pandas.Panel`
        'stats'           -> :py:class:`pandas.DataFrame`

    :type dcs_dict: dict
    :param dcs_dict: Dv-Corr-Stats dictionary

    :rtype: dict
    :return: **ret_dict**: dictionary that contains the following keys:
        *is_incomplete*: True if a keyword is missed
        *missed_keys*: list of missed keywords
        *wrong_class*: list of keyworkds which value is of a wrong class
    """

    keys = ['dvP', 'corrP', 'stats']

    klass = [Panel, Panel, DataFrame]

    is_incomplete, missed_keys, wrong_classes = \
        _check_dict(dcs_dict, zip(keys, klass))

    ret_dict = {}
    ret_dict['is_incomplete'] = is_incomplete
    ret_dict['missed_keys'] = missed_keys
    ret_dict['wrong_classes'] = wrong_classes

    return ret_dict


def adv_check(adv_dict):
    """ Apparent velocity change dictionary (adv_dict) check

    This function test if a adv dictionary contains the requested
    keywords and if their corresponding value is of the
    proper class to continue the processing, e.g., to plot the
    apparent velocity change on a grid.

    Actually the requested keywords -> class pairs are:
        'apparent_dv'     -> :py:class:`pandas.DataFrame`
        'points_geo_info' -> :py:class:`pandas.DataFrame`
        'residuals'       -> :py:class:`pandas.DataFrame`

    :type adv_dict: dict
    :param adv_dict: Apparent velocity change dictionary

    :rtype: dict
    :return: **ret_dict**: dictionary that contains the following keys:
        *is_incomplete*: True if a keyword is missed
        *missed_keys*: list of missed keywords
        *wrong_class*: list of keyworkds which value is of a wrong class
    """

    keys = ['apparent_dv', 'points_geo_info', 'residuals']

    klass = [DataFrame, DataFrame, DataFrame]

    is_incomplete, missed_keys, wrong_classes = \
        _check_dict(adv_dict, zip(keys, klass))

    ret_dict = {}
    ret_dict['is_incomplete'] = is_incomplete
    ret_dict['missed_keys'] = missed_keys
    ret_dict['wrong_classes'] = wrong_classes

    return ret_dict


def create_panel(df_list, df_names):
    """ Create a Panel given a list of DataFrame and a list of names

    This function creates a :py:class:`~pandas.Panel` putting together a list
    of DataFrame contained in the `df_list' argument and assigning to each
    one of them a name according to the list `df_names`
    (df_list[i] -> df_names[i]).

    :type df_list: list of :py:class:`~pandas.DataFrame`
    :param df_list: List of DataFrames to combine on a single Panel
    :type df_names: list of strings
    :param df_names: List of names to assign to the DataFrames

    :rtype: :py:class:`~pandas.Panel`
    :return: **dp**: Panel - dp[name] = df name where name=df_names[i]
        and df = df_list[i]
    """

    for df in df_list:
        if not isinstance(df, DataFrame):
            raise TypeError("'df_list' must contain pandas DataFrames")

    if len(df_list) != len(df_names):
        raise ValueError("Each DataFrame must have a unique name")

    # Dictionary that will hold the DataFrame to pass to the Panel constructor
    dd = {}

    for (df, name) in zip(df_list, df_names):
        dd[name] = df

    dp = Panel(dd)

    return dp


def dv_dataframe_weight(dv, corr):
    """ Multiply column-by-column two DataFrame

    This funciton multiplies column-by-column two
    :py:class:`~pandas.DataFrame` and returns the obtained DataFrame.
    One possible application is where one of the two DataFrames represents
    a weight for the other like what happend when averaging multiple
    velocity changes for the same stations-pair obtained with different
    componens.

    :type dv: :py:class:`~pandas.DataFrame`
    :param dv: First DataFrame
    :type corr: :py:class:`~pandas.DataFrame`
    :param corr: Second DataFrame

    :rtype: :py:class:`~pandas.DataFrame`
    :return: **dv_weighted**: dv_weighted[col] = dv[col] * corr[col] for all
        col in dv
    """
    if (not isinstance(dv, DataFrame)) or (not isinstance(corr, DataFrame)):
        raise TypeError("dv and corr must be pandas DataFrames")

    if not np.all(dv.columns == corr.columns):
        raise ValueError("dv and corr DataFrame do not contain all the same \
            stations")

    dv_weighted = dv.copy()

    for station in dv:
        cdv = dv[station]
        weight = corr[station]
        dv_weighted[station] = cdv * weight

    return dv_weighted


def dv_weighted_average(dv_corr_tupels_list):
    """ Calculate the weighted average of dv/v curves

    This function does the weighted average of different dv/v curves, for
    example obtained analyzing different componenets combinations (i.e. ZZ,
    NN, EE, EZ etc.).
    Differen curves are weighted according to the their correlation variance
    as in Weaver et al. GJI 2011 (On the precision of noise correlation
    interferometry).

    :type dv_corr_tupels_list: list
    :param dv_corr_tupels_list: list of dv_corr tuples like [(dv1,corr1),
    (dv2,corr2),.....,(dvN,corrN)]. Each dv and corr is an object of type
    :py:class:`~pandas.DataFrame`.

    :rtype: dict
    :return: **avg_df_dict**: dictionary that contains the following keys:
        **avg_dv**: averaged dv/v curves (:py:class:`~pandas.DataFrame`)
        **avg_corr**: averaged correlation curves
            (:py:class:`~pandas.DataFrame`)
    """

    (dv, corr) = dv_corr_tupels_list[0]

    # remove the channel from the combined seed id
    dv.rename(columns=lambda x: '.'.join(x.split('.')[:-1]), inplace=True)
    corr.rename(columns=lambda x: '.'.join(x.split('.')[:-1]), inplace=True)

    # remove extreme points
    dv[corr > 0.999] = np.nan
    corr[corr > 0.999] = np.nan

    weight = np.power((1 - corr ** 2) / (4 * corr ** 2), -1)

    res_dv = dv * weight
    res_corr = corr * weight

    for (dv, corr) in dv_corr_tupels_list[1:]:
        # remove the channel from the combined seed id
        dv.rename(columns=lambda x: '.'.join(x.split('.')[:-1]),
                  inplace=True)
        corr.rename(columns=lambda x: '.'.join(x.split('.')[:-1]),
                    inplace=True)

        # remove extreme points
        dv[corr > 0.999] = np.nan
        corr[corr > 0.999] = np.nan

        # Calculate the variance
        cw = np.power((1 - corr ** 2) / (4 * corr ** 2), -1)

        # increment the pseudo-correlation
        res_corr += corr * cw

        # apply the weight to the dv
        res_dv += dv * cw

        # increment the total weight
        weight += cw

    # normalize the resulting dataframes
    res_dv = res_dv / weight
    res_corr = res_corr / weight

    # add a fake channel to creeate a data structure consistent with the rest
    # of the library
    # TODO: create the list of combined channels and put it here instead of
    # the fake channels pair.
    res_dv.rename(columns=lambda x: x + '.XX-XX', inplace=True)
    res_corr.rename(columns=lambda x: x + '.XX-XX', inplace=True)

    avg_df_dict = {'avg_dv': res_dv,
                   'avg_corr': res_corr}

    return avg_df_dict


def interp_gaps(x, max_len=5, inds=None):
    """ Fill missed values through linear interpolation

    This function fills missed values through linear interpolation if the gap
    is shorter than a maximum lenght.

    :type x: 1D :class:`~numpy.ndarray`
    :param x: Array where to fill missed values
    :type max_len: int
    :param max_len: maximun length of a filled gap
    :type inds: 1D :class:`~numpy.ndarray` (optional)
    :param inds: index where to interpolate (must be increasing). If None it
        default to np.arange(x.shape[0])

    :rtype: 1D :class:`~numpy.ndarray`
    :return:**x**:Array with missed values filled when suitable
    """
    x = np.array(x)

    # Check if there are missed values
    if ~np.isnan(np.sum(x)):
        return x

    if inds is None:
        inds = np.arange(x.shape[0])

    invalid = np.isnan(x)
    valid = -invalid

    firstIndex = valid.argmax()
    lastIndex = valid.shape[0] - valid[::-1].argmax() - 1

    valid = valid[firstIndex:lastIndex]
    invalid = invalid[firstIndex:lastIndex]
    inds = inds[firstIndex:lastIndex]

    # Find missed values intervals and their length
    start = np.where(np.diff(valid))[0][::2] + 1
    stop = np.where(np.diff(valid))[0][1::2] + 1

    length = stop - start
    ms = (length < max_len)

    # If all the intervals are longer then max_len return
    # the original vector
    if np.sum(ms) == 0:
        return x

    # Do the linear interpolation
    invalid = np.concatenate(map(lambda (x, y): np.arange(x, y),
                                 zip(start[ms], stop[ms]))).astype('int')

    x[firstIndex:lastIndex][invalid] = \
            np.interp(inds[invalid],
            inds[valid],
            x[firstIndex:lastIndex][valid])

    return x


def create_date_obj(year, month, day):
    """ Creates a datetime object """
    return datetime.date(year, month, day)


if BC_UI:
    class _create_date_obj_view(HasTraits):
        year = Int(2011)
        month = Int(12)
        day = Int(1)

        trait_view = View(Item('year'),
                          Item('month'),
                          Item('day'))


def load_pickled_Series_DataFrame_Panel(filename):
    """ Load a pickled DataFrame (ref. pandas prj) """
    df = np.lib.npyio.load(filename)
    return df


if BC_UI:
    class _load_pickled_Series_DataFrame_Panel_view(HasTraits):
        filename = File()
        trait_view = View(Item('filename'))


def get_values_DataFrame(df):
    """ Get the values out of DataFrame (ref. pandas prj) """
    values = df.values
    index = df.index
    columns = df.columns
    return {'values': values, 'index': index, 'columns': columns}


if BC_UI:
    class _get_values_DataFrame_view(HasTraits):
        trait_view = View()


def get_valid_traces(st):
    """Retun only valid traces of a stream.

    Remove traces that are 100% masked from a stream. This happens when 
    a masked trace is trimmed within a gap. The function works in place.

    :type st: obspy.Stream
    :param st: stream to work on

    """

    assert type(st) == Stream, "Input st is not an obspy.Stream."

    for tr in st:
        if isinstance(tr.data,np.ma.MaskedArray):
            if tr.data.mask.all():
                st.remove(tr)
    return


def import_function_by_name(func):
    """Import a function of a given name.

    Import a function given its name as string and return it.
    Example for func_name: obspy.core.read

    :type func_name: string
    :param func_name: name of function to import
    :rtype: object
    :return: function
    """

    assert type(func)==str, "func is not a string"
    assert '.' in func, "func must name the function including its module: %s"\
                         % func
    modname = func[:-1*func[::-1].index('.')-1]
    funcname = func[-1*func[::-1].index('.'):]
    mod = importlib.import_module(modname)
    function = getattr(mod, funcname)
    return function


def find_stations_name(comb):
    """ Extract the ordered list of stations from a set of traces id """

    stations_list = []
    for label in comb:
        networks, stations, locations, channels = label.split('.')
        one, two = stations.split('-')
        if one not in stations_list:
            stations_list.append(one)
        if two not in stations_list:
            stations_list.append(two)
    stations_list.sort()
    return np.array(stations_list)


def from_comb_to_stations_list(comb, full_stations_list):
    """ Extract the list of stations involved in a series of combinations """

    stat_list = set([])
    for label in comb:
        networks, stations, locations, channels = label.split('.')
        one, two = stations.split('-')
        first = np.ravel(np.argwhere(full_stations_list == one))[0]
        second = np.ravel(np.argwhere(full_stations_list == two))[0]
        stat_list.update([first, second])
    return stat_list


def from_str_comb_to_list(str_comb, full_stations_list):
    """ From a list of str combinations to a list of tuples

    This function transform a list of combinations in the form
    ['UV01-UV12','UV03-UV21',...] in a list of tuples
    like [(1,12),(3,21),...]. It works for combinations where
    the station name is just two letters.

    .. rubric:: Note

    Remember that indexing in python starts from 0 rather then the
    general form of the str combinations that starts form station 1.
    """

    comb_list = []

    for label in str_comb:
        networks, stations, locations, channels = label.split('.')
        one, two = stations.split('-')
        first = np.ravel(np.argwhere(full_stations_list == one))[0]
        second = np.ravel(np.argwhere(full_stations_list == two))[0]
        comb_list.append((first + 1, second + 1))

    return comb_list


def extract_stations_info(stats_df):
    """ Extrace stations geographical infromation from stats DataFrame

    This function extraxt the geographycal information about all stations
    reported in the stats DataFrame as it is created by the funciton
    :py:func:`~miic.core.macro.from_single_pattern_to_panel`.

    :type stats_df: :py:class:`~pandas.DataFrame`
    :param stats_df: Stats DataFrame

    :rtype: :py:class:`~pandas.DataFrame`
    :return:**stations_info**: Pandas DataFrame which index is the ordered
        list of stations and the columns are: 'easting', 'northing' and
        'elevation'.
    """

    if (not isinstance(stats_df, DataFrame)):
        raise TypeError("stats_df and corr must be pandas DataFrames")

    stations_name = find_stations_name(stats_df.index)

    stations_info = DataFrame(index=stations_name,
                              columns=['easting', 'northing', 'elevation'])
    parsed = []

    for label in stats_df.T:
        # print label
        networks, stations, locations, channels = label.split('.')
        one, two = stations.split('-')

        if one not in parsed:
            stations_info.ix[one]['easting'] = stats_df.ix[label]['stlo']
            stations_info.ix[one]['northing'] = stats_df.ix[label]['stla']
            stations_info.ix[one]['elevation'] = stats_df.ix[label]['stel']
            parsed.append(one)

        if two not in parsed:
            stations_info.ix[two]['easting'] = stats_df.ix[label]['evlo']
            stations_info.ix[two]['northing'] = stats_df.ix[label]['evla']
            stations_info.ix[two]['elevation'] = stats_df.ix[label]['evel']
            parsed.append(two)

    return stations_info


def from_single_pattern_to_panel(load_dir='.', save_dir='./save', fs=10.0, \
                                 suffix='', old_style=False):
    """ Create :class:`pandas.Panel` object recombining all corr and dv curves.

    This function creates two :py:class:`pandas.Panel` object recombining
    respectively all correlation `curve` and `dv/v` curve created for
    a specific dataset and one :py:class:`pandas.DataFrame` containing all
    the metainformation in each `stats` object associated with one stations
    pair.
    Source timing, correlation value and velocity change are all stored in a
    matlab file with the name of this form (look at
    :class:`~miic.core.miic_utils.convert_to_matlab` for a detailed
    description):
        vchange_full_<pattern>_<suffix>_.mat

    Suffix is equal to ``"_%sHz" % fs`` when ``old_style==True``.

    Patterns that are processed without errors are logged in a file
    ``success_patterns.npy`` saved in the `save_dir` directory.

    :type load_dir: string
    :param load_dir: Where the dv/v and corr curves are stored
    :type save_dir: string
    :param save_dir: Where the two Panels will be saved
    :type fs: float
    :param fs: Pseudo Sampling frequency for the corr curve
    :type suffix: string
    :param suffix: Optional suffix for the filename to look for (it must be the
        same as used with the :class:`~miic.core.macro.vchange_estimate`
        function through with the corr ad dv/v curves were created)
    :type old_style: bool
    :param old_style: If true, the suffic is generated using the `fs`
        ( "_<fs>Hz") instead of being passed as a parameter)
    """

    if not os.path.isdir(save_dir):
        print "`save_dir` doesn't exist ..... creating"
        os.mkdir(save_dir)

    base_patterns = []

    if old_style:
        suffix = "%sHz" % fs

    successfull = find_comb(load_dir, suffix)

    stats_df = DataFrame(columns=['evel',
                                  'endtime',
                                  'dist',
                                  'network',
                                  'channel',
                                  'stlo',
                                  'baz',
                                  'stel',
                                  'evla',
                                  'npts',
                                  'station',
                                  'location',
                                  'starttime',
                                  'sampling_rate',
                                  'stla',
                                  'az',
                                  'evlo'])

    for (i, pattern) in enumerate(successfull):

        if suffix != '':
            vchange_fname = 'vchange_full_' + pattern + '_' + suffix + '.mat'
        else:
            vchange_fname = 'vchange_full_' + pattern + '.mat'

        vchange_vars = mat_to_ndarray(os.path.join(load_dir, vchange_fname))

        time = convert_time(vchange_vars['time'])

        if time is None:
            print "Time format error: skip pattern %s" % pattern
            continue

        corr = np.squeeze(vchange_vars['corr'])

        try:
            dv = np.squeeze(vchange_vars['value'])  # Current key
        except KeyError:  # Try to address also the old style dv dict
            try:
                dv = np.squeeze(vchange_vars['dv'])
            except KeyError:
                try:
                    dv = np.squeeze(vchange_vars['dt'])
                except Exception:
                    raise Exception

        if 'stats' in vchange_vars:
            stats = flatten_recarray(vchange_vars['stats'])

            # It is necessary to be then able to separate the different
            # stations name from the columns name of the created dataframe
            keywords = ['network', 'station', 'location', 'channel']
            tr_id = '.'.join([stats[key] for key in \
                              keywords if isinstance(stats[key], basestring)])
            pattern = tr_id

            cdf = DataFrame(stats, index=[pattern])
            stats_df = stats_df.append(cdf, verify_integrity=True)

        # Adapt dv and corr in case they are single curves
        try:
            _, _ = dv.shape
        except ValueError:
            dv = dv[np.newaxis, :]
            corr = corr[np.newaxis, :]

        if i == 0:
            xyz = {}
            pqr = {}
            win_lab = []
            for k in range(len(dv)):
                lab = 'win-%i' % k
                win_lab.append(lab)
                xyz[lab] = {}
                pqr[lab] = {}

        for j in range(len(dv)):
            cc = Series(corr[j], index=time)
            # ss = Series(dv[j] - 1, index=time)
            ss = Series(dv[j], index=time)
            xyz[win_lab[j]].update({pattern: ss})
            pqr[win_lab[j]].update({pattern: cc})

        base_patterns.append(pattern)

    dv = Panel(xyz)
    corr = Panel(pqr)

    dcs_dict = {'dvP': dv,
                'corrP': corr}
    if len(stats_df) > 0:
        dcs_dict.update({'stats': stats_df})

    with open(os.path.join(save_dir, 'dcs_dict.pickle'), 'w') as f_out:
        p = Pickler(f_out)
        p.dump(dcs_dict)

    #     dv.save(os.path.join(save_dir, 'dv.pickle'))
    #     corr.save(os.path.join(save_dir, 'corr.pickle'))
    #     if len(stats_df) > 0:
    #         stats_df.save(os.path.join(save_dir, 'stats.pickle'))

    np.save(os.path.join(save_dir, 'success_patterns.npy'), \
        base_patterns)

    return dcs_dict


if BC_UI:
    class _from_single_pattern_to_panel_view(HasTraits):
        load_dir = Directory()
        save_dir = Directory()
        fs = Float(10.0)
        old_style = Bool(False)
        suffix = Str('')
        
        trait_view = View(VGroup(Item('load_dir'),
                                 Item('save_dir'),
                                 Item('fs',
                                      enabled_when='old_style'),
                                 Item('old_style'),
                                 Item('suffix',
                                      label='filename suffix',
                                      enabled_when='not old_style')
                                 )
                          )
##############################################################################
# Test function                                                              #
##############################################################################


def trimmed_std(data, percentile):
    """Trimmed standard deviation."""
    # data = np.array(data)
    data.sort()
    percentile = percentile / 2.
    low = int(percentile * len(data))
    high = int((1. - percentile) * len(data))
    return data[low:high].std(ddof=0)


def ref_sine(n_points):
    """ Reference sine waveform."""
    x = np.linspace(0, 20 * np.pi, n_points)
    y = np.sin(x)
    return y


def print_input(input_str):
    """ Print its input."""
    print input_str
    return


def print_tuples(iterable):
    """Print tuples."""
    for (key, value) in iterable:
        print "(%(key)s,%(value)s)" % {'key': key, 'value': value}
    return


def print_tuple(key, value):
    """Print a tuple."""
    print "(%(key)s,%(value)s)" % {'key': key, 'value': value}
    return

# EOF
