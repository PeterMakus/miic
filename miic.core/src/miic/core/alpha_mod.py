"""
@author:
Eraldo Pomponi

@copyright:
The MIIC Development Team (eraldo.pomponi@uni-leipzig.de)

@license:
GNU Lesser General Public License, Version 3
(http://www.gnu.org/copyleft/lesser.html)

Created on Nov 16, 2010
"""
# Proxy for the fucntion that will  be moved to stream.py
from __future__ import absolute_import
from miic.core.stream import *
# ########################################################

# Main imports
import os
import datetime
import re
import numpy as np
import string

# ETS imports
try:
    BC_UI = True
    from traits.api \
        import HasTraits, List, Int, Dict, \
        Float, Str, Bool, Enum, Button, File, Directory

    from traitsui.api \
        import View, Item, HGroup, VGroup
    from traitsui.editors import TextEditor
except ImportError:
    BC_UI = False
    pass

# Obspy imports
from obspy.core import read, Stream, Trace, UTCDateTime
from obspy.arclink import Client as Client_arc
from obspy.seishub import Client as Client_seis

# Local imports
# from miic.core.wt_fun import WT_Denoise
from miic.core.miic_utils import dir_read

# #############################################################################
# Exceptions                                                                 #
# #############################################################################


class InputError(Exception):
    """
    Exception for Input errors.
    """
    def __init__(self, msg):
        Exception.__init__(self, msg)


def time_windows_list_generation(t_start="2009-08-24 00:20:03",
                                 width=3600,
                                 how_many=10):

    t_win_list = []
    t_s = UTCDateTime(t_start)
    for k in np.arange(how_many):
        t_win_list.append(t_s + k * width)
    return t_win_list

if BC_UI:
    class _time_windows_list_generation_view(HasTraits):
        t_start = UTCDateTime("2009-08-24 00:20:03")
        width = Int(3600)
        how_many = Int(10)

        trait_view = View(Item("t_start", editor=TextEditor()),
                          Item("width", label="width (sec)"),
                          Item("how_many"))


def time_windows_list_reduction(t_win_list, width=3600, \
                                host="localhost", \
                                port=8080, \
                                timeout=100, \
                                network_id="PF", \
                                station_id="FOR", \
                                location_id="", \
                                channel_id="HLE"):

    t_win_available = []
    for tw in t_win_list:
        st, n_trace = stream_seishub_read(host=host, \
                                         port=port, \
                                         timeout=timeout, \
                                         start_time=tw, \
                                         time_interval=width, \
                                         network_id=network_id, \
                                         station_id=station_id, \
                                         location_id=location_id, \
                                         channel_id=channel_id, \
                                         get_paz=False)
        if n_trace > 0:
            its_ok = True
            for tr in st:
                if len(tr) == 0:
                    its_ok = False
                    break
            if its_ok:
                t_win_available.append(tw)
    return t_win_available

if BC_UI:
    class _time_windows_list_reduction_view(HasTraits):

        width = Int(3600)
        host = Str("localhost")
        port = Int(8080)
        timeout = Int(100)
        network_id = Str("PF")
        station_id = Str("FOR")
        location_id = Str("")
        channel_id = Str("HLE")
    
        trait_view = View(HGroup(Item('host'),
                                 Item('port'),
                                 Item('timeout'),
                                 label='Server'),
                          HGroup(Item('width'), label='Time'),
                          HGroup(Item('network_id', label='nw'),
                                 Item('station_id', label='sta.'),
                                 Item('location_id', label='loc.'),
                                 Item('channel_id', label='ch'),
                                 label='Network'))


def tw_gen(t_start="2009-08-24 00:20:03",
               width=3600,
               how_many=10, \
               host="localhost", \
               port=8080, \
               timeout=100, \
               network_id="PF", \
               station_id="FOR", \
               location_id="", \
               channel_id="HLE"):

    t_win_list = time_windows_list_generation(t_start=t_start, width=width, how_many=how_many)
    t_win_l = t_win_list
    return t_win_l

if BC_UI:
    class _tw_gen_view(HasTraits):
    
        t_start = UTCDateTime('2009-08-24 00:20:03')
        width = Int(3600)
        how_many = Int(10)
        host = Str("localhost")
        port = Int(8080)
        timeout = Int(100)
        network_id = Str("PF")
        station_id = Str("FOR")
        location_id = Str("")
        channel_id = Str("HLE")
    
        trait_view = View(HGroup(Item("t_start", editor=TextEditor()),
                                 Item("width", label="width (sec)"),
                                 Item("how_many"),
                                 label='Time win'),
                          HGroup(Item('host'),
                                 Item('port'),
                                 Item('timeout'),
                                 label='Server'),
                          HGroup(Item('network_id', label='nw'),
                                 Item('station_id', label='sta.'),
                                 Item('location_id', label='loc.'),
                                 Item('channel_id', label='ch'),
                                 label='Network'))

# #############################################################################
# Stream plot functions                                                      #
# #############################################################################


def stream_plot(st, automerge=False, type='normal'):
    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")

    st.plot(automerge=automerge, type=type)
    return

if BC_UI:
    class _stream_plot_view(HasTraits):
        automerge = Bool(False)
        type = Enum('normal', 'dayplot')
    
        trait_view = View(Item('automerge'),
                          Item('type'))

# #############################################################################
# Stream read functions                                                      #
# #############################################################################


def stream_arklink_read(host="webdc.eu", port=18001, timeout=100,
                 start_time="2009-08-24 00:20:03", time_interval=30,
                 network_id="BW", station_id="RJOB", location_id="",
                 channel_id="EH*", get_paz=False):
    """ Arklink server client.

    For a detailed description of how it works refer to ObsPy website
    (obspy.org)

    """
    client = Client_arc(host, port, timeout)
    t = UTCDateTime(start_time)
    try:
        st = client.getWaveform(network_id, station_id, location_id, channel_id, \
                                t, t + time_interval)
        n_trace = len(st)

        if get_paz:
            paz = client.getPAZ(network_id, station_id, location_id, channel_id, \
                                t, t + time_interval)
            return st, paz, n_trace
        else:
            return st, n_trace
    except:
        print "An error occurred reading the data."
        st = []
        n_trace = 0
        paz = []
        if get_paz:
            return st, paz, n_trace
        else:
            return st, n_trace

if BC_UI:
    class _stream_arklink_read_view(HasTraits):
        host = Str("webdc.eu")
        port = Int(18001)
        timeout = Int(100)
        start_time = UTCDateTime("2009-08-24 00:20:03")
        time_interval = Int(30)
        network_id = Str("BW")
        station_id = Str("RJOB")
        location_id = Str("")
        channel_id = Str("EH*")
        get_paz = Bool(False)
        
        trait_view = View(HGroup(Item('host'),
                                 Item('port'),
                                 Item('timeout'),
                                 label='Server'),
                          HGroup(Item('start_time', editor=TextEditor()),
                                 Item('time_interval'),
                                 label='Time'),
                          HGroup(Item('network_id', label='nw'),
                                 Item('station_id', label='sta.'),
                                 Item('location_id', label='loc.'),
                                 Item('channel_id', label='ch'),
                                 Item('get_paz', label='get PAZ'),
                                 label='Network'))


def stream_seishub_read(host="localhost", port=8080, timeout=100,
                 start_time="2010-01-01 00:20:03", time_interval=30,
                 network_id="PF", station_id="", location_id="",
                 channel_id="HLE", get_paz=False, remove_mean=False,
                 remove_trend=False):
    """ Seishub server client.

    For a detailed description of how it works refer to ObsPy website
    (obspy.org)

    """

    client = Client_seis(base_url="http://" + host + ':' + str(port),
                         timeout=timeout)
    t = UTCDateTime(start_time)

    st = Stream()

    if station_id == "":
        st = client.waveform.getWaveform(network_id, str(station_id),
                                         location_id,
                                         channel_id, t, t + time_interval)
    else:
        for station in station_id:
            try:
                st += client.waveform.getWaveform(network_id, str(station),
                                                  location_id,
                                                  channel_id,
                                                  t,
                                                  t + time_interval)
            except:
                pass

    if len(st) > 0:
        if remove_trend:
            st = stream_detrend(st)

        if remove_mean:
            st = stream_demean(st)

        st.merge(method=1, fill_value=0, interpolation_samples=1)
        n_trace = len(st)
    else:
        n_trace = 0

    if get_paz:
        paz = client.station.getPAZ(network_id, station_id, t)
        return st, paz, n_trace
    else:
        return st, n_trace

    return st, n_trace


if BC_UI:
    class _stream_seishub_read_view(HasTraits):
        host = Str("localhost")
        port = Int(8080)
        timeout = Int(100)
        start_time = UTCDateTime("2010-01-01 00:20:03")
        time_interval = Int(30)
        network_id = Str("PF")
        station_id = List(Str(""))
        location_id = Str("")
        channel_id = Str("HLE")
        get_paz = Bool(False)
        remove_mean = Bool(False)
        remove_trend = Bool(False)
    
        trait_view = View(HGroup(Item('host'),
                                 Item('port'),
                                 Item('timeout'),
                                 label='Server'),
                          HGroup(Item('start_time', editor=TextEditor()),
                                 Item('time_interval'),
                                 label='Time'),
                          HGroup(Item('remove_mean'),
                                 Item('remove_trend'),
                                 label='Process'),
                          HGroup(Item('network_id', label='nw'),
                                 Item('station_id', label='sta.',
                                      height=100, width=120),
                                 Item('location_id', label='loc.'),
                                 Item('channel_id', label='ch'),
                                 Item('get_paz', label='get PAZ'),
                                 label='Network'))


def kutec_read(fname):
    """ Read the K-UTec proprietary file format.

    Read data in the K-UTec specific IMC FAMOS format into a stream object.
    As there is no obvious station information in the data file
    Network is set to KU and Station is set to the first five letters of the
    filename.

    :parameters:
    ------------
    fname : string
        path to the file containing the data to be read

    .. rubric:: Returns

    st : obspy.core.Stream object
        Obspy stream object containing the data

    """
    tr = Trace()

    line = []
    keys = {}
    f = open(fname, 'r')
    char = f.read(1)  # read leading '|'
    while char == '|':
        key = []
        cnt = 0
        while 1:
            key.append(f.read(1))
            if key[-1] == ',':
                cnt += 1
            if cnt == 3:
                break
        tkeys = string.split(string.join(key, ''), ',')
        key.append(f.read(int(tkeys[2])))
        keyline = string.join(key, '')
        f.read(1)  # read terminating ';'
        char = f.read(1)  # read leading '|'
        # print char
        while (char == '\r') or (char == '\n'):
            char = f.read(1)  # read leading '|'
        #    print char
        keyval = keyline.split(',')
        # ######
        # # in the post 20120619 version files there are leading
        # linefeed in the key (\n), remove them here
        if keyval[0].startswith('\n|'):
            print "does this happen", keyval
            keyval[0] = keyval[0][2:]

        if keyval[0] == 'CF':
            keys[keyval[0]] = {}
            keys[keyval[0]]['Dateiformat'] = int(keyval[1])
            keys[keyval[0]]['Keylaenge'] = int(keyval[2])
            keys[keyval[0]]['Prozessor'] = int(keyval[3])
        elif keyval[0] == 'CK':
            keys[keyval[0]] = {}
            keys[keyval[0]]['Version'] = int(keyval[1])
            keys[keyval[0]]['Lang'] = int(keyval[2])
            keys[keyval[0]]['Dump'] = keyval[3]
            keys[keyval[0]]['Abgeschlossen'] = int(keyval[3])
            if keys[keyval[0]]['Abgeschlossen'] != 1:
                print "%s %s = %s not implemented." % (keyval[0], \
                        'Abgeschlossen', keys[keyval[0]]['DirekteFolgeAnzahl'])
        elif keyval[0] == 'NO':
            keys[keyval[0]] = {}
            keys[keyval[0]]['Version'] = int(keyval[1])
            keys[keyval[0]]['Lang'] = int(keyval[2])
            keys[keyval[0]]['Ursprung'] = int(keyval[3])
            keys[keyval[0]]['NameLang'] = int(keyval[4])
            keys[keyval[0]]['Name'] = keyval[5]
            keys[keyval[0]]['KommLang'] = int(keyval[6])
            if keys[keyval[0]]['KommLang']:
                keys[keyval[0]]['Kommemtar'] = keyval[7]
        elif keyval[0] == 'CP':
            keys[keyval[0]] = {}
            keys[keyval[0]]['Version'] = int(keyval[1])
            keys[keyval[0]]['Lang'] = int(keyval[2])
            keys[keyval[0]]['BufferReferenz'] = int(keyval[3])
            keys[keyval[0]]['Bytes'] = int(keyval[4])  # Bytes fuer
                                                        # einen Messwert
            keys[keyval[0]]['ZahlenFormat'] = int(keyval[5])
            keys[keyval[0]]['SignBits'] = int(keyval[6])
            keys[keyval[0]]['Maske'] = int(keyval[7])
            keys[keyval[0]]['Offset'] = int(keyval[8])
            keys[keyval[0]]['DirekteFolgeAnzahl'] = int(keyval[9])
            keys[keyval[0]]['AbstandBytes'] = int(keyval[10])
            if keys[keyval[0]]['DirekteFolgeAnzahl'] != 1:
                print "%s %s = %s not implemented." % (keyval[0], \
                   'DirekteFolgeAnzahl', keys[keyval[0]]['DirekteFolgeAnzahl'])
                break

        elif keyval[0] == 'Cb':
            keys[keyval[0]] = {}
            keys[keyval[0]]['Version'] = int(keyval[1])
            keys[keyval[0]]['Lang'] = int(keyval[2])
            keys[keyval[0]]['AnzahlBufferInKey'] = int(keyval[3])
            if keys[keyval[0]]['AnzahlBufferInKey'] != 1:
                print "%s %s = %d not implemented." % (keyval[0], \
                    'AnzahlBufferInKey', keys[keyval[0]]['AnzahlBufferInKey'])
                break
            keys[keyval[0]]['BytesInUserInfo'] = int(keyval[4])
            keys[keyval[0]]['BufferReferenz'] = int(keyval[5])
            keys[keyval[0]]['IndexSampleKey'] = int(keyval[6])
            keys[keyval[0]]['OffsetBufferInSampleKey'] = int(keyval[7])
            if keys[keyval[0]]['OffsetBufferInSampleKey'] != 0:
                print "%s %s = %d not implemented." % (keyval[0], \
                                    'OffsetBufferInSampleKey', \
                                    keys[keyval[0]]['OffsetBufferInSampleKey'])
                break
            keys[keyval[0]]['BufferLangBytes'] = int(keyval[8])
            keys[keyval[0]]['OffsetFirstSampleInBuffer'] = int(keyval[9])
            if keys[keyval[0]]['OffsetFirstSampleInBuffer'] != 0:
                print "%s %s = %d not implemented." % (keyval[0], \
                                'OffsetFirstSampleInBuffer', \
                                keys[keyval[0]]['OffsetFirstSampleInBuffer'])
                break
            keys[keyval[0]]['BufferFilledBytes'] = int(keyval[10])
            keys[keyval[0]]['x0'] = float(keyval[12])
            keys[keyval[0]]['Addzeit'] = float(keyval[13])
            if keys[keyval[0]]['BytesInUserInfo']:
                keys[keyval[0]]['UserInfo'] = int(keyval[14])
        elif keyval[0] == 'CS':
            keys[keyval[0]] = {}
            keys[keyval[0]]['Version'] = int(keyval[1])
            keys[keyval[0]]['Lang'] = int(keyval[2])
            keys[keyval[0]]['AnzahlBufferInKey'] = int(keyval[3])
            tmp = string.join(keyval[4:], ',')
            keys[keyval[0]]['Rohdaten'] = tmp

            npts = keys['Cb']['BufferFilledBytes'] / keys['CP']['Bytes']
            tr.stats['npts'] = npts
            # allocate array
            tr.data = np.ndarray(npts, dtype=float)
            # treat different number formats
            if keys['CP']['ZahlenFormat'] == 4:
                tmp = np.fromstring(keys['CS']['Rohdaten'], dtype='uint8', \
                                count=npts * 2)
                tr.data = (tmp[0::2].astype(float) + \
                       (tmp[1::2].astype(float) * 256))
                tr.data[np.nonzero(tr.data > 32767)] -= 65536
            elif keys['CP']['ZahlenFormat'] == 8:
                tr.data = np.fromstring(keys['CS']['Rohdaten'],
                                        dtype='float64',
                                        count=npts)
            else:
                print "%s %s = %d not implemented." % (keyval[0], \
                             'ZahlenFormat', keys[keyval[0]]['ZahlenFormat'])
                break

        elif keyval[0] == 'NT':
            keys[keyval[0]] = {}
            keys[keyval[0]]['Version'] = int(keyval[1])
            keys[keyval[0]]['Lang'] = int(keyval[2])
            keys[keyval[0]]['Tag'] = int(keyval[3])
            keys[keyval[0]]['Monat'] = int(keyval[4])
            keys[keyval[0]]['Jahr'] = int(keyval[5])
            keys[keyval[0]]['Stunden'] = int(keyval[6])
            keys[keyval[0]]['Minuten'] = int(keyval[7])
            keys[keyval[0]]['Sekunden'] = float(keyval[8])
            tr.stats['starttime'] = UTCDateTime(keys[keyval[0]]['Jahr'], \
                                                keys[keyval[0]]['Monat'], \
                                                keys[keyval[0]]['Tag'], \
                                                keys[keyval[0]]['Stunden'], \
                                                keys[keyval[0]]['Minuten'], \
                                                keys[keyval[0]]['Sekunden'])
        elif keyval[0] == 'CD':
            keys[keyval[0]] = {}
            keys[keyval[0]]['Version'] = int(keyval[1])
            keys[keyval[0]]['Lang'] = int(keyval[2])
            keys[keyval[0]]['dx'] = float(keyval[3])
            tr.stats['delta'] = keys[keyval[0]]['dx']
            keys[keyval[0]]['kalibiert'] = int(keyval[4])
            if keys[keyval[0]]['kalibiert'] != 1:
                print "%s %s = %d not implemented." % \
                    (keyval[0], 'kalibiert',
                     keys[keyval[0]]['kalibiert'])
                break
            keys[keyval[0]]['EinheitLang'] = int(keyval[5])
            keys[keyval[0]]['Einheit'] = keyval[6]

            if keys[keyval[0]]['Version'] == 2:
                keys[keyval[0]]['Reduktion'] = int(keyval[7])
                keys[keyval[0]]['InMultiEvents'] = int(keyval[8])
                keys[keyval[0]]['SortiereBuffer'] = int(keyval[9])
                keys[keyval[0]]['x0'] = float(keyval[10])
                keys[keyval[0]]['PretriggerVerwendung'] = int(keyval[11])
            if keys[keyval[0]]['Version'] == 1:
                keys[keyval[0]]['Reduktion'] = ''
                keys[keyval[0]]['InMultiEvents'] = ''
                keys[keyval[0]]['SortiereBuffer'] = ''
                keys[keyval[0]]['x0'] = ''
                keys[keyval[0]]['PretriggerVerwendung'] = 0

        elif keyval[0] == 'CR':
            keys[keyval[0]] = {}
            keys[keyval[0]]['Version'] = int(keyval[1])
            keys[keyval[0]]['Lang'] = int(keyval[2])
            keys[keyval[0]]['Transformieren'] = int(keyval[3])
            keys[keyval[0]]['Faktor'] = float(keyval[4])
            keys[keyval[0]]['Offset'] = float(keyval[5])
            keys[keyval[0]]['Kalibriert'] = int(keyval[6])
            keys[keyval[0]]['EinheitLang'] = int(keyval[7])
            keys[keyval[0]]['Einheit'] = keyval[8]
        elif keyval[0] == 'CN':  # station names
            keys[keyval[0]] = {}
            keys[keyval[0]]['Version'] = int(keyval[1])
            keys[keyval[0]]['Lang'] = int(keyval[2])
            keys[keyval[0]]['IndexGruppe'] = int(keyval[3])
            keys[keyval[0]]['IndexBit'] = int(keyval[5])
            keys[keyval[0]]['NameLang'] = int(keyval[6])
            keys[keyval[0]]['Name'] = keyval[7]
            keys[keyval[0]]['KommLang'] = int(keyval[8])
            keys[keyval[0]]['Kommentar'] = keyval[9]
        else:
            keys[keyval[0]] = {}
            keys[keyval[0]]['KeyString'] = keyval[1:]

    # NT key is beginning of measurement (starting of measurement unit)
    # keys['Cb']['Addzeit'] needs to be added to obtain the absolute trigger
    # time

    tr.stats['starttime'] += keys['Cb']['Addzeit']

    # Adjust starttime according to pretrigger (There is some uncertainty
    # about the CD key) to get relative trigger time
    # for CD:Version == 1 always use Cb:x0
    # for CD:Version == 2 only use Cb:x0 if CD:PretriggerVerwendung == 1
    if keys['CD']['Version'] == 1 or \
        (keys['CD']['Version'] == 2 and
         keys['CD']['PretriggerVerwendung'] == 1):
        tr.stats['starttime'] += keys['Cb']['x0']

    if 'CR' in keys:
        if keys['CR']['Transformieren']:
            tr.data = tr.data * keys['CR']['Faktor'] + keys['CR']['Offset']

    f.close()
    # ### Channel naming
    tr.stats['network'] = 'KU'
    tr.stats['location'] = ''
    # ### Pre 20120619 namin convention to extract the station name from the
    # filename
    # tr.stats['station'] = fname[-12:-7]
    # ### Now take the station name from the ICN key
    tr.stats['station'] = keys['CN']['Name'].replace('_', '')
    # ### or construct a name that is consistent with the old filename
    # generated one from the key
    # ### This is is very likely to cause a problem sooner or later.
    # tr.stats['station'] = 'MK%03d' % int(keys['CN']['Name'].split('_')[-1])

    # tr.stats['station'] = keys['CN']['Name'].replace('_','')

    st = Stream()
    st.extend([tr])

    return st


def summit_seg2_read(fname):
    """ Read SEG2 data recorded with the DMT summit aquisition unit.

    Read the SEG2 formatted seismic data aquired with the summit recorder
    and fill the ID fields in the stats.

    :parameters:
    ------------
    :type fname: string
    :param fname: Path to the file containing the data to be read
    :rtype: :class:`~obspy.core.Stream` object
    :return: **st**: obspy.core.Stream object
        Obspy stream object containing the data
    """
    try:
        from obspy.seg2.seg2 import readSEG2
    except ImportError:
        print "obspy.segy package not installed. Exit"
        return

    # read the stream
    st = readSEG2(fname)
    # enter ID in fields of the stream
    for tr in st:
        tr.stats['network'] = tr.stats.seg2.MEASURING_POINT
        tr.stats['station'] = tr.stats.seg2.STATION_CODE
        tr.stats['channel'] = tr.stats.seg2.REGISTRATION_DIRECTION
        # This needs to be fixed
        tr.stats['sac'] = {}

        # longitude in degrees
        tr.stats['sac']['stlo'] = \
            float(tr.stats.seg2.RECEIVER_LOCATION.split(' ')[0]) * \
                180 / 6371000 / 3.141592653589793
        # longitude in degrees
        tr.stats['sac']['stla'] = \
            float(tr.stats.seg2.RECEIVER_LOCATION.split(' ')[1]) * \
                180 / 6371000 / 3.141592653589793
        # elevation in meters
        tr.stats['sac']['stel'] = \
            float(tr.stats.seg2.RECEIVER_LOCATION.split(' ')[2])

    return st


#  From Ernst Niederleithinger 5.9.2012
def usarray_read(fname):
    """ Read the BAM US-Array lbv data format used on Mike-2 test specimen.

    Read the BAM US-Array lbv data format used on Mike-2 test specimen into a
    stream object.
    As there is no obvious station (or any other) information in the data file.
    As the parameters are not supposed to change, they are hardcoded here.

    :parameters:
    ------------
    :type fname: string
    :param fname: Path to the file containing the data to be read
        (WITHOUT EXTENSION) extensions .dat and .hdr will be added
        automatically
    :rtype: :class:`~obspy.core.Stream` object
    :return: **st**: obspy.core.Stream object
        Obspy stream object containing the data
    """

    # filenames
    lbvfilename = fname + '.lbv'
    hdrfilename = fname + '.hdr'

    # initialise
    st = Stream()
    tr = Trace()
    # tr = SacIO()

    # static parameters
    t = os.path.getmtime(hdrfilename)
    tt = datetime.datetime.fromtimestamp(t)

    tr.stats['starttime'] = UTCDateTime(tt.year, tt.month, tt.day, tt.hour,
                                        tt.minute, tt.second, tt.microsecond)
    tr.stats['network'] = 'BAM-USArray'
    tr.stats['channel'] = 'z'

    # reading header from file
    fh = open(hdrfilename, 'r')
    while True:
        line = fh.readline()
        if line.__len__() < 1:
            break
        line = line.rstrip()
        if line.find('PK') > -1:
            parts = re.split(':', line)
            tr.stats['location'] = parts[1].lstrip()
        if line.find('transceivers') > -1:
            parts = re.split(':', line)
            ntra = int(parts[1].lstrip())
            traco = np.zeros((ntra, 3), float)
            for i in range(ntra):
                coordstr = fh.readline().split()
                for j in range(3):
                    traco[i, j] = float(coordstr[j])
        if line.find('measurements') > -1:
            parts = re.split(':', line)
            nmeas = int(parts[1].lstrip())
            measco = np.zeros((nmeas, 2), int)
            for i in range(nmeas):
                configstr = fh.readline().split()
                for j in range(2):
                    measco[i, j] = float(configstr[j])
        if line.find('samples') > -1:
            parts = re.split(':', line)
            tr.stats['npts'] = int(parts[1].lstrip())
        if line.find('samplefreq') > -1:
            parts = re.split(':', line)
            tr.stats['sampling_rate'] = int(parts[1].lstrip())

    fh.close()

    # reading data from file
    fd = open(lbvfilename, 'rb')
    datatype = '>i2'
    read_data = np.fromfile(file=fd, dtype=datatype)
    fd.close()

    # sort and store traces
    for i in range(nmeas):
        # receiver number stored as station name
        tr.stats['station'] = str(measco[i, 1])
        # receiver coords (storing not yet implemented)
        stla = traco[measco[i, 1] - 1, 1]  # x
        stlo = traco[measco[i, 1] - 1, 1]  # y
        stel = traco[measco[i, 1] - 1, 1]  # z
        # transmitter number stored as event name (storing not yet implemented)
        kevnm = str(measco[i, 0])
        # transmitter coords (storing not yet implemented)
        evla = traco[measco[i, 1] - 1, 0]  # x
        evlo = traco[measco[i, 1] - 1, 0]  # y
        evdp = traco[measco[i, 1] - 1, 0]  # z
        tr.data = read_data[i * tr.stats.npts:(i + 1) * tr.stats.npts]
        st.extend([tr])
        # plot 1 trace for test purposes
        # if i==20:
        #    tr.plot()
        #    print ('plot done')

    return st


def stream_read(filename=None, format=None, example=False):

    if example:
        st = read()
    else:
        if format == 'K-UTec':
            st = kutec_read(filename)
        elif format == 'BAM':
            st = usarray_read(filename)
        elif format == 'Summit-SEG2':
            st = summit_seg2_read(filename)
        else:
            if format == 'None (Automatic)':
                format = None
            st = read(filename, format)

    n_trace = len(st)
    base_name = '.'.join([st[0].stats.network, st[0].stats.station, \
                          st[0].stats.location, \
                          str(st[0].stats.starttime).replace(':', '_')])
    start_time = st[0].stats.starttime
    return st, n_trace, base_name, start_time


if BC_UI:
    class _stream_read_view(HasTraits):
        example = Bool(False)
        filename = File
        format = Enum('None (Automatic)', 'GSE2', 'MSEED', 'SAC', \
                      'SEISAN', 'WAV', 'Q', 'SH_ASC', 'K-UTec', 'BAM',
                      'Summit-SEG2')
    
        trait_view = View(Item('example', label='examp. stream'),
                          HGroup(Item('filename'),
                                 Item('format'),
                                 enabled_when='not example'))


def dir_read_stream(base_dir='', pattern='*.raw', sort_flag=True, \
                    format='None (Automatic)'):
    """ Read all files in specified directory into one single stream object.

    Reads all files in the directory assuming one trace per file and stores it
    in one stream.
    """

    import glob

    if sort_flag:
        file_list = sorted(glob.glob(os.path.join(base_dir, pattern)))
    else:
        file_list = glob.glob(os.path.join(base_dir, pattern))
    stack_st = Stream()
    for this_file in file_list:
        st, _, _, _ = stream_read(filename=this_file, format=format)
        for tr in st:
            stack_st.append(tr)

    return(stack_st)


if BC_UI:
    class _dir_read_stream_view(HasTraits):
    
        base_dir = Directory
        pattern = Str('*.raw')
        sort_flag = Bool(True)
        # preview = Button('Preview')
        # file_list_preview = List(File)
        format = Enum('None (Automatic)', 'GSE2', 'MSEED', 'SAC', \
                  'SEISAN', 'WAV', 'Q', 'SH_ASC', 'K-UTec', 'BAM')
        files_list = List
        _file_list_preview = List(File)
        _num_files = Int(0)
    
        trait_view = View(Item('base_dir'),
                          Item('pattern'),
                          Item('sort_flag', label='sorted'),
                          Item('format'),
                          # Item('preview'),
                          # HGroup(Item('file_list_preview', style='readonly'),
                          #       Item('num_files', style='readonly')),
                          Item('_num_files', style='readonly', \
                               label='Num selec. files'),
                          resizable=True)
    
        def __init__(self, file_list=None, base_dir='', pattern='*.raw', \
                     sort_flag=True, format='None (Automatic)'):
            super(HasTraits, self).__init__()
            if file_list is not None:
                self._file_list_prev = file_list
            self.base_dir = base_dir
            self.pattern = pattern
            self.sorted = sort_flag
            self.format = format
    
        def _base_dir_changed(self):
            self._file_list_preview = \
                dir_read(self.base_dir, self.pattern, self.sort_flag)
            self._num_files = len(self._file_list_preview)
        
        def _pattern_changed(self):
            self._file_list_preview = \
                dir_read(self.base_dir, self.pattern, self.sort_flag)
            self._num_files = len(self._file_list_preview)
    
# #############################################################################
# Stream manipulation                                                        #
# #############################################################################


def stream_copy(st):
    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")
    st_copy = st.copy()
    return st_copy


if BC_UI:
    class _stream_copy_view(HasTraits):
        msg = Str('Connect the stream to be copied')
    
        trait_view = View(Item('msg', style='readonly'))
    

def stream_slice(st, start_time="2008-12-17 00:01:00", interval=10, \
                 keep_empty_traces=False, displacement=0):

    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")

    t_start = UTCDateTime(start_time) + displacement
    t_stop = t_start + interval

    st_slice = st.slice(t_start, t_stop, keep_empty_traces=keep_empty_traces)

    return st_slice


if BC_UI:
    class _stream_slice_view(HasTraits):
        start_time = Str("2008-12-17 00:01:00")
        displacement = Int(0)
        interval = Int(10)
        keep_empty_traces = Bool(False)
    
        trait_view = View(VGroup(Item('start_time'),
                                Item('displacement'),
                                Item('interval'),
                                Item('keep_empty_traces')))

# #############################################################################
# Stream filtering and more                                                  #
# #############################################################################


def instrument_caracterization(poles, zeros, gain, sensitivity):

    paz = {'poles': poles,
           'zeros': zeros,
           'gain': gain,
           'sensitivity': sensitivity}

    return paz


if BC_UI:
    class _instrument_caracterization_view(HasTraits):
    
        poles = List
        p_real = Float(0.0)
        p_imag = Float(0.0)
        add_p = Button('Add Pole')
    
        zeros = List
        z_real = Float(0.0)
        z_imag = Float(0.0)
        add_z = Button('Add Zero')
    
        gain = Float(1)
        sensitivity = Float(1)
    
        trait_view = View(VGroup(HGroup(Item('p_real'),
                                        Item('p_imag'),
                                        Item('add_p', show_label=False)),
                                 Item('poles', style='readonly'),
                                 label='Poles'),
                          VGroup(HGroup(Item('z_real'),
                                        Item('z_imag'),
                                        Item('add_z', show_label=False)),
                                 Item('zeros', style='readonly'),
                                 label='Zeros'),
                          HGroup(Item('gain'),
                                 Item('sensitivity'),
                                 label='G & S'))

        def _add_p_fired(self):
            new_p = self.p_real + self.p_imag * 1j
            self.poles.append(new_p)
    
        def _add_z_fired(self):
            new_z = self.z_real + self.z_imag * 1j
            self.zeros.append(new_z)
    

def correct_responce(st, paz_orig, paz_desidered):

    from obspy.signal import seisSim

    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")

    for k in np.arange(st.count()):
        st[k].data = seisSim(st[0].data, st[0].stats.sampling_rate, \
                             paz_desidered, inst_sim=paz_orig)

    st_corr = st
    return st_corr


if BC_UI:
    class _correct_responce_view(HasTraits):
        paz_orig = Dict()
        paz_desidered = Dict()
    
        trait_view = View(Item('paz_orig'),
                          Item('paz_desidered'))
    
    
def corn_freq_2_paz(fc, damp):

    from obspy.signal import cornFreq2Paz

    paz_out = cornFreq2Paz(fc, damp)

    return paz_out


if BC_UI:
    class _corn_freq_2_paz_view(HasTraits):
        fc = Float(1.0)
        damp = Float(0.707)
    
        trai_view = View(Item('fc', label='Corner Freq.'),
                         Item('damp'))

# def stream_downsample(st, final_freq, no_filter=False, \
#                      strict_length=False):
#
#    if not isinstance(st, Stream):
#        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")
#
#    for tr in st:
#        sampling_rate = tr.stats.sampling_rate
#        decimation_factor = np.floor(sampling_rate / final_freq)
#        if decimation_factor != (sampling_rate / final_freq):
#            print "downsample factor rounded to integer: %4.2f -> %i !!!!" % \
#                ((sampling_rate / final_freq), decimation_factor)
#        elif decimation_factor > 16:
#            print "downsample factor > 16. Bound to 16"
#            decimation_factor = 16
#
#        from obspy.signal import __version__
#
#        if __version__ > '0.6.0':
#
#            tr.decimate(decimation_factor.astype(int),
#                        no_filter,
#                        strict_length)
#        else:
#
#            tr.downsample(decimation_factor.astype(int),
#                          no_filter,
#                          strict_length)
#
#    st_down = st
#    return st_down
#
#
# class _stream_downsample_view(HasTraits):
#    final_freq = Int(2)
#    no_filter = Bool(False)
#    strict_length = Bool(False)
#
#    trait_view = View(Item('final_freq'),
#                      Item('no_filter', style='custom'),
#                      Item('strict_length', style='custom'))


def stream_select(st, network=None, station=None, location=None, \
                  channel=None, sampling_rate=None, npts=None, component=None):

    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")

    st_sel = st.select(network, station, location, channel, sampling_rate, \
                       npts, component)
    n_trace = len(st_sel)

    return st_sel, n_trace


if BC_UI:
    class _stream_select_view(HasTraits):
    
        network = Str("")
        station = Str("")
        location = Str("")
        channel = Str("")
        sampling_rate = Int
        npts = Int
        component = Str
    
        trait_view = View(HGroup(Item('network'),
                                 Item('station'),
                                 Item('location'),
                                 Item('channel')),
                          Item('sampling_rate'),
                          Item('npts'),
                          Item('component'))


def stream_rotation(st):

    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")

    st_N = st.select(channel="EHN")

    st_E = st.select(channel="EHE")

    st_N[0].data = st_N[0].data + st_E[0].data

    return st_N


if BC_UI:
    class _stream_rotation_view(HasTraits):
    
        trait_view = View()


# def stream_wt_denoise(st, family, order, level, mode='soft'):
#
#    if not isinstance(st, Stream):
#        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")
#
#    wt_c = WT_Denoise(family=family, order=order, level=level)
#
#    for tr in st:
#        wt_c.sig = tr.data
#        wt_c.filter(mode=mode)
#        tr.data = wt_c.sig
#
#    st_den = st
#    return st_den
#
#
# class _stream_wt_denoise_view(HasTraits):
#
#    family = Enum(['haar', 'db', 'sym', 'coif', 'bior', 'rbio', 'dmey'])
#    order = Int(2)
#    level = Int(3)
#    mode = Enum('soft', 'hard')
#
#    trait_view = View(Item('family'),
#                      Item('order'),
#                      Item('level'),
#                      Item('mode', label='thresh. mode'))


# def stream_events_removal(st, family, order, level):
#
#    if not isinstance(st, Stream):
#        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")
#
#    from wt_fun import WT_Event_Filter
#
#    wt_c = WT_Event_Filter(family=family, order=order, level=level)
#
#    for tr in st:
#        wt_c.sig = tr.data
#        wt_c.filter()
#        tr.data = wt_c.sig
#
#    st_no_events = st
#    return st_no_events
#
#
# class _stream_events_removal_view(HasTraits):
#
#    family = Enum(['haar', 'db', 'sym', 'coif', 'bior', 'rbio', 'dmey'])
#    order = Int(2)
#    level = Int(3)
#
#    trait_view = View(Item('family'),
#                      Item('order'),
#                      Item('level'))


def stream_remove_mean(st):

    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")

    for tr in st:
        tr.data = tr.data - np.mean(tr.data)
    st_no_mean = st
    return st_no_mean


if BC_UI:
    class _stream_remove_mean_view(HasTraits):
    
        trait_view = View()


def stream_empty_creation():
    st = Stream()
    return st


if BC_UI:
    class _stream_empty_creation_view(HasTraits):
    
        trait_view = View()


st_stack = Stream()


def stream_stack(st_curr):

    global st_stack

    if st_stack is None:
        st_stack = st_curr
    else:
        st_stack += st_curr
    return st_stack


def clear_st_stack(fake):

    global st_stack

    if st_stack is not None:
        st_stack = None


if BC_UI:
    class _clear_st_stack_view(HasTraits):
        trait_view = View()


def stream_tr_count(st):

    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")

    n_tr = len(st)

    return n_tr


if BC_UI:
    class _stream_tr_count_view(HasTraits):
        msg = Str('Count Traces in a Stream object')
        trait_view = View(Item('msg', style='readonly'))


def stream_sort(st):
    """ Sort the Traces by station name """
    st.sort(keys=['station', 'channel'])
    st_sort = st
    return st_sort


if BC_UI:
    class _stream_sort_view(HasTraits):
        msg = Str('Sort Traces by station name')
        trait_view = View(Item('msg', style='readonly'))


def stream_normalize(st, global_max=False):

    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")

    st.normalize(global_max=global_max)

    st_n = st

    return st_n


if BC_UI:
    class _stream_normalize_view(HasTraits):
    
        global_max = Bool(False)

        trait_view = View(Item('global_max'))


def stream_collapse_tr(st):

    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")

    stream_new = Stream()
    # Generate sorted list of traces (no copy)
    # Sort order, id, starttime, endtime
    ids = []
    for tr in st:
        if not tr.id in ids:
            ids.append(tr.id)
    for id in ids:
        print "new_trace id: %s" % id
        tr_new = Trace()
        tr_new.data = np.zeros(st[0].data.shape)
#        tr_new.stats = {}
        tr_new.stats_tr1 = {}
        tr_new.stats_tr2 = {}
        starttime1_list = []
        starttime2_list = []
        endtime1_list = []
        endtime2_list = []
        n_tr = 0
        for tr in st:
            if tr.id == id:
                print tr.id
                if len(tr_new.data) != len(tr.data):
                    lp = len(tr_new.data) - len(tr.data)
                    print "lp: %d" % lp
                    if lp > 0:
                        left = np.ceil(lp / 2)
                        right = lp - left
                        cdata = np.append(np.zeros(left, dtype=tr.data.dtype),
                                          tr.data)
                        tr.data = np.append(cdata,
                                            np.zeros(right,
                                                     dtype=tr.data.dtype))
                    else:
                        lp = -lp
                        left = np.ceil(lp / 2)
                        right = lp - left
                        tr.data = tr.data[left:-right]
                    print "len tr: %d" % len(tr)
                    print "len tr_new: % d" % len(tr_new)
                tr_new.data += tr.data
                n_tr += 1
                starttime1_list.append(tr.stats_tr1.starttime)
                starttime2_list.append(tr.stats_tr2.starttime)
                endtime1_list.append(tr.stats_tr1.endtime)
                endtime2_list.append(tr.stats_tr2.endtime)

                tr_new.stats.update(tr.stats)
                tr_new.stats_tr1.update(tr.stats_tr1)
                tr_new.stats_tr2.update(tr.stats_tr2)
        tr_new.data /= n_tr
        tr_new.stats['starttime1'] = starttime1_list
        tr_new.stats['starttime2'] = starttime2_list
        tr_new.stats['endtime1'] = endtime1_list
        tr_new.stats['endtime2'] = endtime2_list
        stream_new.append(tr_new)

    return stream_new


def stream_collapse_tr_new(st, npts, onacopy=True):
    """ Collapse all the traces with the same id averaging their points value.

    This function collapse (adds) all the traces in one Stream that shares the
    same id to a single one with averaged data vector and the same
    meta-information (i.e. tr.stats object).
    All the traces are padded/shriked to npts points before averaging.
    This function works by default on a copy of the original Stream so that it
    is not affected by the function execution. To override the original one put
    the flag ``onacopy`` to ``False``

    :type st: :class:`~obspy.core.stream.Stream`
    :param st: Stream that contains the traces that will be collapsed
    :type npts: Int
    :param npts: Number of points in the resulting traces
    :type onacopy: Bool
    :param onacopy: Work on a copy of the original stream if True

    :rtype: :class:`~obspy.core.stream.Stream`
    :return: **st_collapsed**: Stream with one trace for each unique tr.id.
    """
    if not isinstance(st, Stream):
        raise InputError("'st' must be a 'obspy.core.stream.Stream' object")

    if onacopy:
        st_collapsed = st.copy()
    else:
        st_collapsed = st

    traces = st_collapsed.traces
    traces_dict = {}

    try:
        while True:
            trace = trace_sym_pad_shrink_to_npts(traces.pop(0), npts)
            id = trace.getId()
            if id not in traces_dict:
                traces_dict[id] = [trace]
            else:
                traces_dict[id].append(trace)
    except IndexError:
        pass

    for id in traces_dict.keys():
        # ntr = len(traces_dict[id])
        cur_trace = traces_dict[id].pop(0)
        # loop through traces of same id
        for _i in xrange(len(traces_dict[id])):
            trace = traces_dict[id].pop(0)
            # disable sanity checks because there are already done
            cur_trace.data += trace.data
            cur_trace.stats_tr1.npts += min(trace.stats_tr1.npts, \
                                            trace.stats_tr2.npts)
            cur_trace.stats_tr2.npts += min(trace.stats_tr1.npts, \
                                            trace.stats_tr2.npts)
        # It is more convenient if traces are successively stacked
        # not the normalize cur_trace.data /= ntr
        traces.append(cur_trace)

    return st_collapsed


if BC_UI:
    class _stream_collapse_tr_new_view(HasTraits):
        npts = Int(131072)
        onacopy = Bool(True)
    
        trait_view = View(Item('npts'),
                          Item('onacopy', label='Work on a copy'))


def stream_extract_ndarray(st):

    nd_out = np.zeros([len(st), len(st[0])])

    for (i, tr) in enumerate(st):
        nd_out[i, :] = tr.data

    return nd_out


def t_extract_ymd(t):

    # t = UTCDateTime(t)
    if t.month < 10:
        t_month_str = '0' + str(t.month)
    else:
        t_month_str = str(t.month)

    if t.day < 10:
        t_day_str = '0' + str(t.day)
    else:
        t_day_str = str(t.day)

    t_marker = str(t.year) + '-' + t_month_str + '-' + t_day_str
    return t_marker


def hello_world():
    print "Hello world"


if BC_UI:
    class _hello_world_view(HasTraits):
    
        msg = Str("Bye")
    
        trait_view = View(Item('msg'))

# EOF
