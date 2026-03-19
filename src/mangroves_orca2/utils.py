#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility functions for ORCA2 regridding.

Includes helper functions for:
- coordinate conversion
- post-processing (averaging)

Author
------
Eric Duvieilbourg (CNRS / LEMAR)

License
-------
MIT
"""

import numpy as np


def to_radians(lon, lat):
    return np.radians(lon), np.radians(lat)


def compute_mean(fer, xsum):
    mask = xsum > 0
    fer[mask] /= xsum[mask]
    return fer
