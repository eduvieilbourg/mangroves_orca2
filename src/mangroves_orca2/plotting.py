#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plotting utilities for ORCA2 regridded data.

Provides quick visualization of surface fields
using matplotlib.

Author
------
Eric Duvieilbourg (CNRS / LEMAR)

License
-------
MIT
"""
# src/mangroves_orca2/plotting.py

import numpy as np
import matplotlib.pyplot as plt

def save_plot(surface, lon_grid, lat_grid, COL_VAL, img_path):
    """
    Save a 2D surface plot of regridded data.

    Parameters
    ----------
    surface : ndarray
        2D array of surface values.
    lon_grid, lat_grid : ndarray
        Grid coordinates.
    COL_VAL : str
        Variable name (for labeling).
    img_path : str
        Output PNG path.

    Notes
    -----
    - Zero values are masked (set to NaN)
    - Uses pcolormesh
    """
    plt.figure(figsize=(12,6))
    plt.pcolormesh(lon_grid, lat_grid, np.where(surface==0,
                                                np.nan,
                                                surface),
                   shading="auto")
    plt.colorbar(label=f"Moyenne de {COL_VAL} sur grille ORCA2")
    plt.title(f"{COL_VAL} regrillée sur ORCA2 (surface)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    plt.savefig(img_path, dpi=200)
    plt.close()