#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nearest-neighbor regridding on ORCA2 grid.

This module implements a Numba-accelerated nearest-neighbor
search on a spherical grid using a dot-product metric.

The algorithm:
    - Converts coordinates to radians
    - Computes cosine of angular distance
    - Finds closest grid cell for each point
    - Accumulates values and counts

Notes
-----
- Distance is approximated via spherical dot product
- Only surface layer is processed (z=0)
- Masked grid points are ignored

Functions
---------
process_chunk : core Numba kernel

Author
------
Eric Duvieilbourg (CNRS / LEMAR)

License
-------
MIT
"""
# src/mangroves_orca2/regrid.py

import numpy as np
from numba import njit

@njit
def process_chunk(indices, lon_g, lat_g, mask, lon_p, lat_p, val_p, fer, xsum):
    """
    Process a chunk of input points and map them onto the ORCA2 grid.

    For each input point, the nearest valid grid cell is found
    using a spherical dot-product metric. Values are accumulated
    and counts are tracked for later averaging.

    Parameters
    ----------
    indices : ndarray of int
        Indices of points to process in this chunk.
    lon_g, lat_g : ndarray
        Grid longitudes and latitudes (radians).
    mask : ndarray
        Grid mask (1 = valid, 0 = masked).
    lon_p, lat_p : ndarray
        Point coordinates (radians).
    val_p : ndarray
        Point values.
    fer : ndarray
        Accumulator array (sum of values).
    xsum : ndarray
        Counter array (number of points per cell).

    Notes
    -----
    - Only the surface level (z=0) is used.
    - Uses brute-force search (O(Ngrid)).
    - Optimized with Numba JIT.
    """
    ny, nx = lon_g.shape 
    for idx_i in range(indices.size): 
        n = indices[idx_i] 
        lon0, lat0, val0 = lon_p[n], lat_p[n], val_p[n]
        best, best_i, best_j = -2.0, -1, -1

        for j in range(ny):
            for i in range(nx):
                if mask[j, i] == 0:
                    continue

                xdiff = (np.sin(lat_g[j, i]) * np.sin(lat0) +
                         np.cos(lat_g[j, i]) * np.cos(lat0) *
                         np.cos(lon_g[j, i] - lon0))

                if xdiff > best:
                    best = xdiff
                    best_i = i
                    best_j = j

        if best_i != -1:
            fer[best_i, best_j, 0, 0] += val0
            xsum[best_i, best_j, 0, 0] += 1.0