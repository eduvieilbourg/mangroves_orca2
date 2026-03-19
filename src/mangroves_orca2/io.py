#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Input/Output utilities for ORCA2 regridding.

This module handles:
- loading ORCA2 mesh files (NetCDF)
- exporting results to NetCDF format

Supports multiple mesh conventions:
- glamt/gphit
- nav_lon/nav_lat

Author
------
Eric Duvieilbourg (CNRS / LEMAR)

License
-------
MIT
"""
# src/mangroves_orca2/io.py

import numpy as np
import xarray as xr

def load_mesh(mesh_path):
    """
    Load ORCA2 mesh grid from NetCDF file.

    Parameters
    ----------
    mesh_path : str
        Path to mesh_mask NetCDF file.

    Returns
    -------
    lon_grid : ndarray
    lat_grid : ndarray
    tmask : ndarray
    depths : ndarray

    Raises
    ------
    ValueError
        If required variables are not found.
    """
    mesh = xr.open_dataset(mesh_path)

    if "glamt" in mesh:
        lon_grid = mesh["glamt"].values.squeeze()
        lat_grid = mesh["gphit"].values.squeeze()
    elif "nav_lon" in mesh:
        lon_grid = mesh["nav_lon"].values
        lat_grid = mesh["nav_lat"].values
    else:
        raise ValueError("Impossible de trouver glamt/gphit ou nav_lon/nav_lat")

    if "tmask" in mesh:
        tmask = mesh["tmask"].values.squeeze()
    else:
        mask_var = next((v for v in mesh.variables if "mask" in v.lower()), None)
        if mask_var:
            tmask = mesh[mask_var].values.squeeze()
        else:
            tmask = np.ones_like(lon_grid, dtype=np.int8)

    if "gdepw_0" in mesh:
        depths = mesh["gdepw_0"].values.squeeze()
    elif "gdept_0" in mesh:
        depths = mesh["gdept_0"].values.squeeze()
    else:
        depths = np.array([0.0], dtype=float)

    return lon_grid, lat_grid, tmask, depths


def save_netcdf(out_path, VAR_NAME, fer, xsum, lon_grid, lat_grid, depths, nt):
    """
    Save regridded data to NetCDF file.

    Parameters
    ----------
    out_path : str
        Output file path.
    VAR_NAME : str
        Name of the variable (from CSV column).
    fer : ndarray
        Regridded values.
    xsum : ndarray
        Counts per grid cell.
    lon_grid, lat_grid : ndarray
        Grid coordinates.
    depths : ndarray
        Vertical levels.
    nt : int
        Number of time steps.

    Returns
    -------
    str
        Backend used ("netCDF4" or "scipy fallback").
    """
    coords = {"lon": (["y", "x"], lon_grid),
              "lat": (["y", "x"], lat_grid),
              "depth": (["z"], depths),
              "time": (["t"], np.arange(nt)),}

    ds_out = xr.Dataset({VAR_NAME: (["x", "y", "z", "t"], fer),
                         "xsum":     (["x", "y", "z", "t"], xsum),},
                         coords=coords)

    encoding = {VAR_NAME: {"dtype": "float32", "_FillValue": 1e20},
                "xsum":     {"dtype": "float32", "_FillValue": 1e20},}

    try:
        ds_out.to_netcdf(out_path, engine="netcdf4", encoding=encoding)
        return "netCDF4"
    except Exception:
        ds_out.to_netcdf(out_path, engine="scipy", encoding=encoding)
        return "scipy fallback"