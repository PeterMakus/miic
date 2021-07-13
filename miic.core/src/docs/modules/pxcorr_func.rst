Efficient parallel correlation of traces
========================================

This module implements a suite of functions that allow 


.. currentmodule:: miic.core.pxcorr_func
.. automodule:: miic.core.pxcorr_func

    .. comment to end block

    Time domain preprocessing
    -------------------------
    .. autosummary::
        :toctree: autogen
        :nosignatures:
        
        ~detrend
        ~TDnormalization
        ~taper
        ~clip
        ~mute
        ~TDfilter
        ~normalizeStandardDeviation
        ~signBitNormalization
        ~zeroPadding
        
    Frequency domain preprocessing
    ------------------------------
    .. autosummary::
        :toctree: autogen
        :nosignatures:
        
        ~spectralWhitening
        ~FDsignBitNormalization
        
        
    Correlation
    -----------
    .. autosummary::
        :toctree: autogen
        :nosignatures:

        ~calc_cross_combis
        ~stream_pxcorr
        ~rotate_multi_corr_stream

