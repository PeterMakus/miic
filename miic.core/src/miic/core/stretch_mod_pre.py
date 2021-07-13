"""
@author:
Eraldo Pomponi

@copyright:
The MIIC Development Team (eraldo.pomponi@uni-leipzig.de)

@license:
GNU Lesser General Public License, Version 3
(http://www.gnu.org/copyleft/lesser.html)

Created on Aug 19, 2011
"""

# Main imports
import numpy as np
import scipy.ndimage
from scipy.interpolate import UnivariateSpline
from pandas import DataFrame, date_range

# ETS imports
from traits.api import HasTraits, Int, Float, Bool, List, Enum
from traitsui.api import View, Item, Tabbed

from obspy.signal.invsim import cosTaper

from miic.core.miic_utils import nextpow2, from_str_to_datetime


def stretch_mat_creation(ref_tr, str_range=0.1, nstr=100):
    """ Matrix of stretched instance of a reference trace.

    The reference trace is stretched using a cubic spline interpolation
    algorithm form ``-str_range`` to ``str_range`` (in %) for totally
    ``nstr`` steps.
    The output of this function is a matrix containing the stretched version
    of the reference trace (one each row) (``new_m``) and the corresponding
    stretching amount (``deltas``).

    :type ref_tr: :class:`~numpy.ndarray`
    :param ref_tr: 1d ndarray. The reference trace that will be stretched
    :type str_range: float
    :param str_range: Amount, in percent, of the desired stretching (one side)
    :type nstr: int
    :param nstr: Number of stretching steps (one side)

    :rtype: :class:`~numpy.ndarray`, float
    :return:
        **new_m**:
            2d ndarray of stretched version of the reference trace.
            Its size is ``(nstr,len(ref_tr)/2)`` if ``signle_side==True``
            otherwise it is ``(nstr,len(ref_tr))``
        **deltas**: List of float, stretch amount for each row
            of ``new_m``
    """

    n = len(ref_tr)
    samples_idx = np.arange(n) - n // 2
    deltas = 1 + np.linspace(-str_range, str_range, nstr)
    str_timemat = np.zeros((nstr, n))
    for ii in np.arange(nstr):
        str_timemat[ii, :] = samples_idx / deltas[nstr - 1 - ii]
    new_m = np.zeros_like(str_timemat)
    coord = np.zeros((2, n))
    for (i, row) in enumerate(str_timemat):
        coord[0, :] = row + n // 2
        new_m[i, :] = scipy.ndimage.map_coordinates(\
                                    ref_tr.reshape((len(ref_tr), 1)), coord)
    return new_m, deltas


class _stretch_mat_creation_view(HasTraits):
    str_range = Float(0.1)
    nstr = Int(100)
    single_side = Bool(False)

    trait_view = View(Item('str_range'),
                      Item('nstr'),
                      Item('single_side'))


def velocity_change_estimete(mat, tw, strrefmat, strvec, sides='both',
                             return_sim_mat=False):
    """ Velocity change estimate through stretching and comparison.

    Velocity changes are estimated comparing each correlation function stored
    in the ``mat`` matrix (one for each row) with ``strrefmat.shape[0]``
    stretched versions  of a reference trace stored in ``strrefmat``.
    The stretch amount for each row of ``strrefmat`` must be passed in the
    ``strvec`` vector.
    The best match (stretch amount and corresponding correlation value) is
    calculated on different time windows (each row of ``tw`` is a different
    one) instead of on the whole trace.

    :type mat: :class:`~numpy.ndarray`
    :param mat: 2d ndarray containing the correlation functions.
        One for each row.
    :type tw: :class:`~numpy.ndarray` of int
    :param tw: 2d ndarray of time windows to be use in the velocity change
         estimate.
    :type strrefmat: :class:`~numpy.ndarray`
    :param strrefmat: 2D array containing stretched version of the reference
         matrix
    :type strvec: :class:`~numpy.ndarray` or list
    :param strvec: Stretch amount for each row of ``strrefmat``
    :type sides: string
    :param sides: Side of the reference matrix to be used for the velocity
        change estimate ('both' | 'left' | 'right')

    :rtype: :class:`~numpy.ndarray`, :class:`~numpy.ndarray`,
        :class:`~numpy.ndarray`
    :return:
        **corr**: 2d ndarray containing the correlation value for the best
            match for each row of ``mat`` and for each time window.
            Its dimension is: :func:(len(tw),mat.shape[1])

        **dt**: 2d ndarray containing the stretch amount corresponding to
            the best match for each row of ``mat`` and for each time window.
            Its dimension is: :func:(len(tw),mat.shape[1])
        **sim_mat**: 3d ndarray containing the similarity matricies that
            indicate the correlation coefficient with the reference for the
            different time windows, different times and different amount of
            stretching.
            Its dimension is: :py:func:`(len(tw),mat.shape[1],len(strvec))`
    """

    assert(strrefmat.shape[1] == mat.shape[1])

    center_p = mat.shape[1] // 2

    nstr = strrefmat.shape[0]

    corr = np.zeros((len(tw), mat.shape[0]))
    dt = np.zeros((len(tw), mat.shape[0]))
    sim_mat = np.zeros([mat.shape[0], len(strvec), len(tw)])

    for (ii, ctw) in enumerate(tw):

        if sides == 'both':
            ctw = np.hstack((center_p - ctw[::-1], center_p + ctw))
        elif sides == 'left':
            ctw = (center_p - ctw[::-1])
        elif sides == 'right':
            ctw = (center_p + ctw)
        elif sides == 'single':
            ctw = ctw
        else:
            print 'sides = %s not a valid option. Using sides = single' % sides

        mask = np.zeros((mat.shape[1],))
        mask[ctw] = 1

        ref_mask_mat = np.tile(mask, (nstr, 1))
        mat_mask_mat = np.tile(mask, (mat.shape[0], 1))

        first = mat * mat_mask_mat
        second = strrefmat * ref_mask_mat

        dprod = np.dot(first, second.T)

        # Normalization
        f_sq = np.sum(first ** 2, axis=1)
        s_sq = np.sum(second ** 2, axis=1)

        f_sq = f_sq.reshape(1, len(f_sq))
        s_sq = s_sq.reshape(1, len(s_sq))

        den = np.sqrt(np.dot(f_sq.T, s_sq))

        tmp = dprod / den
        sim_mat[:, :, ii] = tmp

        tmp_corr_vect = tmp.max(axis=1)
        corr[ii, :] = tmp_corr_vect
        dt[ii, :] = strvec[tmp.argmax(axis=1)]

    if return_sim_mat:
        dv = {'corr': np.squeeze(corr), 'dt': np.squeeze(dt),
              'stretch_vect': strvec, 'sim_mat': np.squeeze(sim_mat),
              'dv_type': 'single_ref'}
    else:
        dv = {'corr': np.squeeze(corr), 'dt': np.squeeze(dt),
              'stretch_vect': strvec, 'dv_type': 'single_ref'}

    return dv


class _velocity_change_estimete_view(HasTraits):
    sides = Enum('both', 'left', 'right', 'single')
    trait_view = View(Item('sides'))


def time_shift_estimate(corr_data, ref_trc=None, tw=None, shift_range=10,
                        shift_steps=100, single_sided=False):
    """ Time shift estimate through shifting and comparison.

    This function is intended to estimate shift of traces as they can occur
    in noise cross-correlation in case of drifting clocks.

    Time shifts are estimated comparing each correlation function stored
    in the ``corr_data`` matrix (one for each row) with ``shift_steps``
    shifted versions  of reference trace stored in ``ref_trc``.
    The maximum amount of shifting may be passed in ``shift_range``.
    The best match (shifting amount and corresponding correlation value) is
    calculated on different time windows. If ``tw = None`` the shifting is
    estimated on the whole trace.

    :type corr_data: :class:`~numpy.ndarray`
    :param corr_data: 2d ndarray containing the correlation functions.
        One for each row.
    :type ref_trc: :class:`~numpy.ndarray`
    :param ref_trc: 1D array containing the reference trace to be shifted and
        compared to the individual traces in ``mat``
    :type tw: list of :class:`~numpy.ndarray` of int
    :param tw: list of 1D ndarrays holding the indices of sampels in the time
        windows to be use in the time shift estimate. The sampels are counted
        from the zero lag time with the index of the first sample being 0. If
        ``tw = None`` the full time range is used.
    :type shift_range: scalar
    :param shift_range: Maximum amount of time shift in samples (in one
        direction).
        Shifting is tested in both directions from ``-shift_range`` to
        ``shift_range``
    :type shift_steps: scalar`
    :param shift_steps: Number of shifted version to be tested. The increment
            will be ``(2 * shift_range) / shift_steps``
    :type sinlge_sided: boolean
    :param single_sided: If ``True`` the zero lag time of the traces is in the
        first sample. If ``False`` zero lag is assumed to be in the center of
        the traces and the shifting is evaluated on the causal and acausal
        parts of the traces separately and averaged. This is done to avoid bias
        from velocity changes (stretching) in the case of strongly asymmetric
        traces.

    :rtype: dictionary
    :return: **shift_result**: dictionary with the following key-value pairs

        **corr**: :class:`~numpy.ndarray` 2d ndarray containing the correlation
                  value for the best
        match for each row of ``mat`` and for each time window.
        Its dimension is: :func:(len(tw),mat.shape[1])

        **shift**: :class:`~numpy.ndarray` 2d ndarray containing the amount of
                    shifting corresponding to the best match for each row of
                    ``mat`` and for each time window. Shift is measured in
                    units of the sampling interval.
        Its dimension is: :py:func:`(len(tw),mat.shape[1])`
    """

    mat = corr_data

    # generate the reference trace if not given (use the whole time span)
    if ref_trc is None:
        ref_trc = np.nansum(mat, axis=0) / mat.shape[0]

    # generate time window if not given (use the full length of the correlation
    # trace)
    if tw is None:
        tw = time_windows_creation([0], [int(np.floor(mat.shape[1] / 2.))])

    # taper and extend the reference trace to avoid interpolation
    # artefacts at the ends of the trace
    taper = cosTaper(len(ref_trc), 0.05)
    ref_trc *= taper

    # different values of shifting to be tested
    shifts = np.linspace(-shift_range, shift_range, shift_steps)

    # time axis
    time_idx = np.arange(len(ref_trc))

    # create the array to hold the shifted traces
    ref_shift = np.zeros((len(shifts), len(ref_trc)))

    # create a spline object for the reference trace
    ref_tr_spline = UnivariateSpline(time_idx, ref_trc, s=0)

    # evaluate the spline object at different points and put in the prepared
    # array
    for (k, this_shift) in enumerate(shifts):
        ref_shift[k, :] = ref_tr_spline(time_idx - this_shift)

    # search best fit of the crosscorrs to one of the shifted ref_traces
    if single_sided:
        vdict = velocity_change_estimete(mat, tw, ref_shift,
                                         shifts, sides='right',
                                         return_sim_mat=True)
        corr = vdict['corr']
        shift = vdict['dt']
        sim_mat = vdict['sim_mat']
    else:
        # estimate shifts for causal and acausal part individually and avarage
        # to avoid apparent shift from velocity change and asymmetric
        # amplitudes
        lvdict = velocity_change_estimete(mat, tw, ref_shift,
                                          shifts,
                                          sides='left',
                                          return_sim_mat=True)
        lcorr = lvdict['corr']
        lshift = lvdict['dt']
        lsim_mat = lvdict['sim_mat']

        rvdict = velocity_change_estimete(mat, tw, ref_shift,
                                          shifts,
                                          sides='right',
                                          return_sim_mat=True)
        rcorr = rvdict['corr']
        rshift = rvdict['dt']
        rsim_mat = rvdict['sim_mat']

        shift = np.zeros_like(lshift)
        corr = np.zeros_like(lshift)
        sim_mat = np.zeros_like(lsim_mat)
        for ii in range(len(tw)):
            corr[ii] = (lcorr[ii] + rcorr[ii]) / 2.
            shift[ii] = (lshift[ii] + rshift[ii]) / 2.
        sim_mat = (lsim_mat + rsim_mat) / 2.

    # create the result dictionary
    dt = {'corr': corr.T, 'shift': shift.T, 'sim_mat': sim_mat}

    return dt


class _time_shift_estimate_view(HasTraits):

    shift_range = Float(10.0)
    shift_steps = Int(100)
    single_sided = Bool(False)

    trait_view = View(Item('shift_range'),
                      Item('shift_steps'),
                      Item('single_sided'))


def time_shift_apply(corr_data, shift):
    """ Apply time shift to traces.

    Apply time shifts to traces e.g. to align them to a common time base.
    Such shifts can occur in corrlation traces in case of a drifting clock.
    This function ``applies`` the shifts. To correct for shift estimated with
    :class:`~miic.core.stretch_mod.time_shift_estimate` you need to apply
    negative shifts.
    Shifting is done in frequency domain with 5% tapering.

    :type corr_data: :py:class:`~numpy.ndarray`
    :param corr_data: 2d ndarray containing the correlation functions that are
        to be shifted.
        One for each row.
    :type shift: :py:class:`~numpy.ndarray`
    :param shift: ndarray with shift.shape[0] = corr_data.shape[0] containing
        the shifts in units of the sampling interval by which the trace are to
        be shifted

    :rtype: :py:class:`~numpy.ndarray`
    :return: **shifted_mat**: shifted version of the input matrix
    """
    mat = corr_data
    # check input
    # shift is just a 1d array
    if len(shift.shape) == 1:
        t_shift = np.zeros([shift.shape[0], 1])
        t_shift[:, 0] = shift
        shift = t_shift
    # shift has the wrong length
    elif shift.shape[0] != mat.shape[0]:
        print 'InputError: shift.shape[0] must be equal corr_data.shape[0]'
        return 0
    # shift has multiple columns (multiple measurements for the same time)
    if shift.shape[1] > 1:
        shift = np.delete(shift, np.arange(1, shift.shape[1]), axis=1)

    # taper the reference matrix to avoid interpolation
    taper = cosTaper(mat.shape[1], 0.05)
    mat *= np.tile(taper, [mat.shape[0], 1])

    # find a suitable length for the FFT
    N = nextpow2(2 * mat.shape[1])
    w = np.zeros([1, N / 2 + 1])

    # original and shifted phase
    w[0, :] = np.linspace(0, np.pi, N / 2 + 1)
    pha = np.exp(-1j * (shift) * w)

    # Fourier Transform
    F = np.fft.rfft(mat, N, 1)

    # apply the phase shift
    sF = F * pha

    # transform to time domain
    smat = np.fft.irfft(sF)

    # cut to original size
    shifted_mat = smat[:, 0:mat.shape[1]]
    return shifted_mat


class _time_shift_correct_view(HasTraits):
    shift = List()
    corr_data = List()
    trait_view = View(Item('shift'), Item('corr_data'))


def time_stretch_estimate(corr_data, ref_trc=None, tw=None, stretch_range=0.1,
                          stretch_steps=100, sides='both'):
    """ Time shift estimate through shifting and comparison.

    This function estimates stretching of the time axis of traces as it can
    occur if the propagation velocity changes.

    Time stretching is estimated comparing each correlation function stored
    in the ``corr_data`` matrix (one for each row) with ``stretch_steps``
    stretched versions  of reference trace stored in ``ref_trc``.
    The maximum amount of stretching may be passed in ``stretch_range``. The
    time axis is multiplied by exp(stretch).
    The best match (stretching amount and corresponding correlation value) is
    calculated on different time windows. If ``tw = None`` the stretching is
    estimated on the whole trace.

    :type corr_data: :class:`~numpy.ndarray`
    :param corr_data: 2d ndarray containing the correlation functions.
        One for each row.
    :type ref_trc: :class:`~numpy.ndarray`
    :param ref_trc: 1D array containing the reference trace to be shifted and
        compared to the individual traces in ``mat``
    :type tw: list of :class:`~numpy.ndarray` of int
    :param tw: list of 1D ndarrays holding the indices of sampels in the time
        windows to be use in the time shift estimate. The sampels are counted
        from the zero lag time with the index of the first sample being 0. If
        ``tw = None`` the full time range is used.
    :type stretch_range: scalar
    :param stretch_range: Maximum amount of relative stretching.
        Stretching and compression is tested from ``-stretch_range`` to
        ``stretch_range``.
    :type stretch_steps: scalar`
    :param stretch_steps: Number of shifted version to be tested. The
        increment will be ``(2 * stretch_range) / stretch_steps``
    :type single_sided: bool
    :param single_sided: if True zero lag time is on the first sample. If
        False the zero lag time is in the center of the traces.
    :type sides: str
    :param sides: Side of the reference matrix to be used for the stretching
        estimate ('both' | 'left' | 'right' | 'single') ``single`` is used for
        one-sided signals from active sources with zero lag time is on the
        first sample. Other options assume that the zero lag time is in the
        center of the traces.


    :rtype: dictionary
    :return: **stretch_result**: dictionary with the following key-value pairs
        *corr*: :class:`~numpy.ndarray` 2d ndarray containing the correlation
        value for the best match for each row of ``mat`` and for each time
        window.
        Its dimension is: :py:func:`(len(tw),mat.shape[1])`

        *stretch*: :class:`~numpy.ndarray` 2d ndarray containing the amount
        of stretching corresponding to the best match for each row of ``mat``
        and for each time window. Stretch is a relative value corresponding to
        the negative relative velocity change -dv/v
        Its dimension is: :py:func:`(len(tw),mat.shape[1])`
    """

    mat = corr_data

    # generate the reference trace if not given (use the whole time span)
    if ref_trc is None:
        ref_trc = np.nansum(mat, axis=0) / mat.shape[0]

    # generate time window if not given (use the full length of the correlation
    # trace)
    if tw is None:
        tw = time_windows_creation([0], [int(np.floor(mat.shape[1] / 2.))])

    # taper and extend the reference trace to avoid interpolation
    # artefacts at the ends of the trace
    taper = cosTaper(len(ref_trc), 0.05)
    ref_trc *= taper

    # different values of shifting to be tested
    stretchs = np.linspace(-stretch_range, stretch_range, stretch_steps)
    time_facs = np.exp(-stretchs)

    # time axis
    if sides is not 'single':
        time_idx = np.arange(len(ref_trc)) - (len(ref_trc) - 1.) / 2.
    else:
        time_idx = np.arange(len(ref_trc))

    # create the array to hold the shifted traces
    ref_stretch = np.zeros((len(stretchs), len(ref_trc)))

    # create a spline object for the reference trace
    ref_tr_spline = UnivariateSpline(time_idx, ref_trc, s=0)

    # evaluate the spline object at different points and put in the prepared
    # array
    for (k, this_fac) in enumerate(time_facs):
        ref_stretch[k, :] = ref_tr_spline(time_idx * this_fac)

    # search best fit of the crosscorrs to one of the stretched ref_traces
    dv = velocity_change_estimete(mat, tw, ref_stretch,
                                     stretchs, sides=sides,
                                     return_sim_mat=True)

    dv['corr'] = dv['corr'].T
    dv.update({'stretch': dv['dt'].T})
    del dv['dt']
    dv.update({'stretch_vec': stretchs})

    return dv


class _time_stretch_estimate_view(HasTraits):

    stretch_range = Float(0.01)
    stretch_steps = Int(100)
    sides = Enum('both', 'left', 'right', 'sinlge')

    trait_view = View(Item('stretch_range'),
                      Item('stretch_steps'),
                      Item('sides'))


def time_stretch_apply(corr_data, stretch, single_sided=False):
    """ Apply time axis stretch to traces.

    Stretch the time axis of traces e.g. to compensate a velocity shift in the
    propagation medium.
    Such shifts can occur in corrlation traces in case of a drifting clock.
    This function ``applies`` the stretches. To correct for stretching
    estimated with :class:`~miic.core.stretch_mod.time_stretch_estimate`you
    need to apply negative stretching.

    :type corr_data: :class:`~numpy.ndarray`
    :param corr_data: 2d ndarray containing the correlation functions that are
        to be shifted.
        One for each row.
    :type stretch: :class:`~numpy.ndarray`
    :param stretch: ndarray with stretch.shape[0] = corr_data.shape[0]
        containing the stretches relative units.

    :rtype: :class:`~numpy.ndarray`
    :return: **stretched_mat**: stretched version of the input matrix
    """
    mat = corr_data
    # check input
    # stretch is just a 1d array
    if len(stretch.shape) == 1:
        t_stretch = np.zeros([stretch.shape[0], 1])
        t_stretch[:, 0] = stretch
        stretch = t_stretch
    # stretch has the wrong length
    elif stretch.shape[0] != mat.shape[0]:
        print 'InputError: shift.shape[0] must be equal corr_data.shape[0]'
        return 0
    # shift has multiple columns (multiple measurements for the same time)
    if stretch.shape[1] > 1:
        stretch = np.delete(stretch, np.arange(1, stretch.shape[1]), axis=1)

    # taper and extend the reference trace to avoid interpolation
    # artefacts at the ends of the trace
    taper = cosTaper(mat.shape[1], 0.05)
    mat *= np.tile(taper, [mat.shape[0], 1])

    # time axis
    if single_sided:
        time_idx = np.arange(mat.shape[1])
    else:
        time_idx = np.arange(mat.shape[1]) - (mat.shape[1] - 1.) / 2.

    # allocate space for the result
    stretched_mat = np.zeros_like(mat)

    # stretch every line
    for (ii, line) in enumerate(mat):
        s = UnivariateSpline(time_idx, line, s=0)
        stretched_mat[ii, :] = s(time_idx * np.exp(-stretch[ii]))

    return stretched_mat


class _time_stretch_apply_view(HasTraits):
    shift = List()
    corr_data = List()
    trait_view = View(Item('shift'), Item('corr_data'))


def multi_ref_creation(corr_mat,
                       rtime,
                       freq=30,
                       use_break_point=False,
                       break_point=None):
    """ Create the multi-reference traces

    This function creates multi-reference traces according with the given
    frequency.
    In case of a break-point is passed, the intervals to consider for the
    reference traces creation are symmetric respect to it.

    :type corr_mat: :class:`~numpy.ndarray`
    :param corr_mat: Correlation matrix with one correlation function on each
        row
    :type rtime: :class:`~numpy.array` of :class:`~datetime.datetime` objects
    :param rtime: Time vector associated to the given correlation matrix. Its
        lenght must be equal to the numer of columns of the `corr_mat`
        parameter
    :type freq: int
    :param freq: One reference trace every `freq` days
    :type use_break_point: bool
    :param use_break_point: If `True` the reference traces are calculated in
        different intervals of `freq` days symmetric respect to the
        `break_point`
    :type break_point: string
    :param break_point: Brake point expressed as "YYYY-MM-DD"
    """

    if use_break_point and break_point == None:
        print "Error: A break point must be passed!"
        return None

    if use_break_point and type(break_point) != str:
        print "Error: wrong break_point format!\nCheck the docs:\n\n"
        print __doc__
        return None

    if use_break_point:
        bp = from_str_to_datetime(break_point, datetimefmt=True)

        f_frw = "%iD" % int(freq)
        f_bck = "-%iD" % int(freq)

        # Time "backward" intervals starting from the break_point and going
        # back to the first day available in the data.
        dr = date_range(rtime[rtime <= bp].max(),
                        rtime[rtime < bp].min(),
                        freq=f_bck)[::-1]

        # Time "forward" intervals starting from the break_point and going
        # ahead to the last day available in the data.
        dr1 = date_range(bp, rtime.max(), freq=f_frw)[1:]  # break_point must
                                                            # be removed

        dr = dr.append(dr1)
    else:
        f = "%iD" % int(freq)
        dr = date_range(np.min(rtime), np.max(rtime), freq=f)

    # DataFrame creation
    df = DataFrame(corr_mat, index=rtime)

    # GroupBy the given intervals
    dfg = df.groupby(lambda x: np.sum(np.ones(dr.shape)[dr <= x]))

    # Calculate the reference traces averaging the traces on each interval
    df_ref = dfg.mean()

    # Take the raw output
    ref_mat = df_ref.values

    return ref_mat


def multi_ref_vchange_and_align(corr_data,
                      ref_trs,
                      tw=None,
                      stretch_range=0.1,
                      stretch_steps=100,
                      sides='both',
                      return_sim_mat=False):
    """ Multi-reference dv estimate and alignment

    :type corr_data: :class:`~numpy.ndarray`
    :param corr_data: 2d ndarray containing the correlation functions.
        One for each row.
    :type ref_trc: :class:`~numpy.ndarray`
    :param ref_trc: 1D array containing the reference trace to be shifted and
        compared to the individual traces in ``mat``
    :type tw: list of :class:`~numpy.ndarray` of int
    :param tw: list of 1D ndarrays holding the indices of sampels in the time
        windows to be use in the time shift estimate. The sampels are counted
        from the zero lag time with the index of the first sample being 0. If
        ``tw = None`` the full time range is used.
    :type stretch_range: scalar
    :param stretch_range: Maximum amount of relative stretching.
        Stretching and compression is tested from ``-stretch_range`` to
        ``stretch_range``.
    :type stretch_steps: scalar`
    :param stretch_steps: Number of shifted version to be tested. The
        increment will be ``(2 * stretch_range) / stretch_steps``
    :type single_sided: bool
    :param single_sided: if True zero lag time is on the first sample. If
        False the zero lag time is in the center of the traces.
    :type sides: str
    :param sides: Side of the reference matrix to be used for the stretching
        estimate ('both' | 'left' | 'right' | 'single') ``single`` is used for
        one-sided signals from active sources with zero lag time is on the
        first sample. Other options assume that the zero lag time is in the
        center of the traces.
    :type return_sim_mat: bool
    :param return_sim_mat: If `True` the returning dictionary contains also the
        similarity matrix `sim_mat'.


    :rtype: dictionary
    :return: **dv** that contains those (key,value) pairs:
        **corr**: 2d ndarray containing the correlation value for the best
            match for each row of ``mat`` and for each time window.
            Its dimension is: :func:(len(tw),mat.shape[1])

        **dt**: 2d ndarray containing the stretch amount corresponding to
            the best match for each row of ``mat`` and for each time window.
            Its dimension is: :func:(len(tw),mat.shape[1])
        **sim_mat**: 3d ndarray containing the similarity matrix that
            indicate the correlation coefficient with the reference for the
            specific time windows, different times and different amount of
            stretching.
            Its dimension is: :py:func:`(mat.shape[1],len(strvec),1)`
    """

    if tw and len(tw) > 1:
        print " The multi-reference vchange evaluation doesn't handle multiple\
                time windows. Only the first time-window will be used"
        tw = tw[0]

    multi_ref_panel = multi_ref_vchange(corr_data,
                                        ref_trs,
                                        tw=tw,
                                        stretch_range=stretch_range,
                                        stretch_steps=stretch_steps,
                                        sides=sides)

    dv = estimate_reftr_shifts_from_dt_corr(multi_ref_panel,
                                            return_sim_mat=return_sim_mat)

    return dv


class _multi_ref_vchange_and_align_view(HasTraits):

    stretch_range = Float(0.01)
    stretch_steps = Int(100)
    sides = Enum('both', 'left', 'right', 'sinlge')
    return_sim_mat = Bool(False)

    trait_view = View(Item('stretch_range'),
                      Item('stretch_steps'),
                      Item('sides'),
                      Item('return_sim_mat'))


def multi_ref_vchange(corr_data,
                      ref_trs,
                      tw=None,
                      stretch_range=0.1,
                      stretch_steps=100,
                      sides='both'):
    """ Velocity change estimate with single or multiple reference traces.

    This function estimates the velocity change corresponding to each row of
    the ``corr_data`` matrix respect to the reference trace/s passed in
    ``ref_trs``.

    The velocity change is estimated comparing each correlation function stored
    in the ``corr_data`` matrix (one for each row) with ``stretch_steps``
    stretched versions of reference/s trace stored in ``ref_trs``.
    The maximum amount of stretching may be passed in ``stretch_range``.
    The best match (stretching amount and corresponding correlation value) is
    calculated on different time windows. If ``tw = None`` the stretching is
    estimated on the whole trace.

    The output is a dictionary with keys of the form ``"reftr_%d" % i``: One
    for each reference trace. The corresponding ``value`` is aslo a dictionary
    that has a structure conforming with
    :py:class:`~miic.core.stretch_mod.time_stretch_estimate` output.

    :type corr_data: :class:`~numpy.ndarray`
    :param corr_data: 2d ndarray containing the correlation functions.
        One for each row.
    :type ref_trc: :class:`~numpy.ndarray`
    :param ref_trc: 1D array containing the reference trace to be shifted and
        compared to the individual traces in ``mat``
    :type tw: list of :class:`~numpy.ndarray` of int
    :param tw: list of 1D ndarrays holding the indices of sampels in the time
        windows to be use in the time shift estimate. The sampels are counted
        from the zero lag time with the index of the first sample being 0. If
        ``tw = None`` the full time range is used.
    :type stretch_range: scalar
    :param stretch_range: Maximum amount of relative stretching.
        Stretching and compression is tested from ``-stretch_range`` to
        ``stretch_range``.
    :type stretch_steps: scalar`
    :param stretch_steps: Number of shifted version to be tested. The
        increment will be ``(2 * stretch_range) / stretch_steps``
    :type single_sided: bool
    :param single_sided: if True zero lag time is on the first sample. If
        False the zero lag time is in the center of the traces.
    :type sides: str
    :param sides: Side of the reference matrix to be used for the stretching
        estimate ('both' | 'left' | 'right' | 'single') ``single`` is used for
        one-sided signals from active sources with zero lag time is on the
        first sample. Other options assume that the zero lag time is in the
        center of the traces.


    :rtype: dictionary
    :return: **multi_ref_panel**: It is a dictionary with one (key,value) pair
        for each reference trace. The key format is ``"reftr_%d" % i`` and the
        corresponding value is also a dictionary with the structure described
        in :py:class:`~miic.core.stretch_mod.time_stretch_estimate`
    """

    # remove 1-dimensions
    ref_trs = np.squeeze(ref_trs)

    # check how many reference traces have been passed
    try:
        reftr_count, _ = ref_trs.shape
    except ValueError:  # An array is passed
        reftr_count = 1

    # Distionary that will hold all the results
    multi_ref_panel = {}

    # When there is just 1 reference trace no loop is necessary
    if reftr_count == 1:
        key = "reftr_0"
        value = time_stretch_estimate(corr_data,
                                      ref_trc=ref_trs,
                                      tw=tw,
                                      stretch_range=stretch_range,
                                      stretch_steps=stretch_steps,
                                      sides=sides)
        multi_ref_panel.update({key: value})
    else:  # For multiple-traces loops
        for i in range(reftr_count):
            ref_trc = ref_trs[i]
            key = "reftr_%d" % int(i)
            value = time_stretch_estimate(corr_data,
                                          ref_trc=ref_trc,
                                          tw=tw,
                                          stretch_range=stretch_range,
                                          stretch_steps=stretch_steps,
                                          sides=sides)
            multi_ref_panel.update({key: value})

    return multi_ref_panel


class _multi_ref_vchange_view(HasTraits):

    stretch_range = Float(0.01)
    stretch_steps = Int(100)
    sides = Enum('both', 'left', 'right', 'sinlge')

    trait_view = View(Item('stretch_range'),
                      Item('stretch_steps'),
                      Item('sides'))


def est_shift_from_dt_corr(dt1, dt2, corr1, corr2):
    """ Estimation of a baseline shift between velocity-change measurements
    preformed with different references.

    The use of different reference traces obtaind from different reference
    periods will result in a shift of the velocity-change curves that ideally
    characterizes the velocity variation between the two reference periods.
    Instead of directly measuring this velocity change from the two reference
    traces it is calulated here as the weighted average of the point
    differences between the two velocity-change curves weighted by their
    inverse variance according to Weaver et al. GJI 2011 (On the precision of
    noise correlation interferometry)

    Input vertors must all be of the same lenth.

    :type dt1: :class:`~numpy.ndarray`
    :pram dt1: Velocity variation measured for reference A
    :type dt2: :class:`~numpy.ndarray`
    :pram dt2: Velocity variation measured for reference B
    :type corr1: :class:`~numpy.ndarray`
    :pram corr1: Correlation between velocity corrected trace and reference A
    :type corr2: :class:`~numpy.ndarray`
    :pram corr2: Correlation between velocity corrected trace and reference B
    """

    # Remove the points where the correlation is 0
    no_zero = (corr1 > 0) & (corr2 > 0)
    corr1 = corr1[no_zero]
    corr2 = corr2[no_zero]

    # Estimate the point-variance for the two curves
    var1 = (1 - corr1 ** 2) / (4 * corr1 ** 2)
    var2 = (1 - corr2 ** 2) / (4 * corr2 ** 2)

    # Calculate the point-weight
    wgt = 1 / (var1 + var2)
    mask = (corr1 > 0.999) & (corr2 > 0.999)
    wgt = wgt[~mask]

    # Calculate the shifth and the total weight as a cumulative sum of the
    # weighted average of the two curves
    shift = np.sum((dt1[~mask] - dt2[~mask]) * wgt) / np.sum(wgt)
    wgt = np.sum(wgt)

    return wgt, shift


def estimate_reftr_shifts_from_dt_corr(multi_ref_panel, return_sim_mat=False):
    """ Combine velocity-change measurements of the same data performed with
    different references to a single curve.

    For a set of velocity-change measurements performed with different
    references this function estimates the relative offsets between all pairs
    of the measurements as a weighted average of their difference with the
    function :py:class:`~miic.core.stretch_mod.est_shift_from_dt_corr`.
    A least squares solution in computed that combines the pairwise
    differences to a consistent set of reference shifts. These shifts should
    be similar to the velocity variations measured between the reference
    traces. The consistent set of reference shifts is used to correct i.e.
    shift the similarity matricies to a common reference. Finally the
    corrected similarity matrices are averaged resulting in a single matrix
    that is interpreted as before. The position of the crest is the combined
    velocity change and the height of the crest is the correlation value.

    :type multi_ref_panel: dictionay
    :param multi_ref_panel: It is a dictionary with one (key,value) pair
        for each reference trace. Its structure is described
        in :py:class:`~miic.core.stretch_mod.multi_ref_vchange`
    :type return_sim_mat: bool
    :param return_sim_mat: If `True` the returning dictionary contains also the
        similarity matrix `sim_mat'.

    """

    # Vector with the stretching amount
    stretch_vect = multi_ref_panel['reftr_0']['stretch_vec']
    delta = stretch_vect[1] - stretch_vect[0]

    n_ref = len(multi_ref_panel.keys())

    corr = []
    shift = []

    if n_ref > 1:

        # Loop over reftr
        for reftr1 in np.sort(multi_ref_panel.keys()):
            ref_idx = [reftr for reftr in np.sort(multi_ref_panel.keys())
                       if reftr != reftr1]
            for reftr2 in ref_idx:
                ccorr, sshift = est_shift_from_dt_corr(
                            np.squeeze(multi_ref_panel[reftr1]['stretch']),
                            np.squeeze(multi_ref_panel[reftr2]['stretch']),
                            np.squeeze(multi_ref_panel[reftr1]['corr']),
                            np.squeeze(multi_ref_panel[reftr2]['corr']))
                corr.append(ccorr)
                shift.append(sshift)

        G = _create_G(len(multi_ref_panel.keys()))
        W = np.diag(np.array(corr))
        D = np.array(shift)

        left_op = np.linalg.inv(np.dot(G.T, np.dot(W, G)))
        right_op = np.dot(W, D)

        m = np.dot(left_op, np.dot(G.T, right_op))
        m = np.hstack((0, m))
        m = m - np.mean(m)

        row, col = np.squeeze(multi_ref_panel['reftr_0']['sim_mat']).shape

        stmp = np.zeros((row, col, n_ref))
        for (i, reftr) in enumerate(np.sort(multi_ref_panel.keys())):
            stmp[:, :, i] = \
                np.roll(np.squeeze(multi_ref_panel[reftr]['sim_mat']),
                                    int(np.round(m[i] / delta)), axis=1)

        bsimmat = np.mean(stmp, axis=2)

        corr = np.max(bsimmat, axis=1)
        dt = np.argmax(bsimmat, axis=1)

        dt = stretch_vect[dt]

        ret_dict = {'dt': dt, 'corr': corr, 'stretch_vect': stretch_vect,
                    'dv_type': 'multi_ref'}

        if return_sim_mat:
            ret_dict.update({'sim_mat': bsimmat})

        return ret_dict
    else:
        print "For a single reference trace use the appropirate funtion"
        return None


def time_windows_creation(starting_list, t_width):
    """ Time windows creation.

    A matrix containing one time window for each row is created. The starting
    samples of each one of them are passed in the ``starting_list`` parameter.
    The windows length ``t_width`` can be scalar or a list of values.
    In the latter case both lists ``starting_list`` and ``t_width`` must
    have the same length.

    :type starting_list: list
    :param starting_list: List of starting points
    :type t_width: int or list of int
    :param t_width: Windows length

    :rtype: :class:`~numpy.ndarray`
    :return: **tw_mat**: 2d ndarray containing the indexes of one time window
        for each row
    """

    if not np.isscalar(starting_list):
        if not np.isscalar(t_width) and len(t_width) != len(starting_list):
            raise ValueError("t_width must be a scalar or list of scalars of\
                            the same length as starting_list")

    tw_list = []

    if np.isscalar(starting_list):
        if np.isscalar(t_width):
            wlen = t_width
        else:
            wlen = t_width[0]
        tw_list.append(np.arange(starting_list, starting_list + wlen, 1))
    else:
        for (ii, cstart) in enumerate(starting_list):
            if np.isscalar(t_width):
                wlen = t_width
            else:
                wlen = t_width[ii]
            tw_list.append(np.arange(cstart, cstart + wlen, 1))

    return tw_list


class _time_windows_creation_view(HasTraits):
    starting_list = List(Int)
    t_width = List(Int(50))

    trait_view = View(Tabbed(Item('starting_list',
                                  height=150,
                                  width=80),
                             Item('t_width',
                                  label='Win width in samples',
                                  height=150,
                                  width=80)))


def _create_G(n_ref):
    """ Create the G matrix for the multi-trace alignment
    """

    G = None
    for jj in range(n_ref):
        line = range(n_ref)
        tline = [i for i in line if i != jj]
        tG = np.zeros((len(tline), len(tline)))
        if jj > 0:
            tG[:, jj - 1] = -1
        for ii in range(len(tline)):
            if tline[ii] > 0:
                tG[ii, tline[ii] - 1] = 1
        if G is None:
            G = tG
        else:
            G = np.vstack((G, tG))
    return G

# EOF
