#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main GUI script for ORCA2 regridding.

This script provides a graphical interface to:
- select input CSV point data (longitude, latitude, value)
- select an ORCA2 mesh (NetCDF)
- perform nearest-neighbor regridding
- export results to NetCDF and PNG

Workflow:
    1. File selection (CSV + mesh + output)
    2. Column selection via GUI
    3. Regridding using Numba-accelerated kernel
    4. NetCDF export
    5. Visualization export

Notes
-----
- Designed for non-programmer users (GUI-based)
- Uses chunk processing for large datasets
- Assumes ORCA2 grid structure

Author
------
Eric Duvieilbourg (CNRS / LEMAR)

License
-------
MIT
"""

import os
import math
import numpy as np
import xarray as xr
import polars as pl
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import warnings
from datetime import datetime

from mangroves_orca2.tk_column_selector import ColumnSelector
from mangroves_orca2.regrid import process_chunk
from mangroves_orca2.io import load_mesh, save_netcdf
from mangroves_orca2.plotting import save_plot

warnings.filterwarnings("ignore", message="The input coordinates to pcolormesh")

def select_files(root):
    """
    Open file dialogs to select input and output files.

    This function guides the user through:
    - selecting the input CSV file containing point data
    - selecting the ORCA2 mesh NetCDF file
    - defining the output NetCDF file name and location

    Default directories:
    - input files: ./data_inputs/
    - output files: ./data_outputs/

    Output filename is automatically prefixed with a timestamp:
        YYYYMMDD-HHhMM_

    Parameters
    ----------
    root : tkinter.Tk
        Root Tkinter window.

    Returns
    -------
    csv_path : str or None
        Path to the selected CSV file.
    mesh_path : str or None
        Path to the selected ORCA2 mesh file.
    out_path : str or None
        Path to the output NetCDF file.
    img_path : str or None
        Path to the output PNG visualization.

    Notes
    -----
    If the user cancels any dialog, the function returns (None, None, None, None).
    """
    input_dir = os.path.abspath("./data_inputs")
    output_dir = os.path.abspath("./data_outputs")
    # Create the folders if they do not exist.
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    print("Select the CSV file (occurrences)...", end=' ')
    csv_path = filedialog.askopenfilename(
        initialdir=input_dir,
        title="Select the CSV file (occurrences)",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if not csv_path:
        messagebox.showinfo("Cancelled", "No CSV file selected —> exit!")
        return None, None, None, None
    print("done")
    # MESH
    print("Select the mesh_mask.nc (ORCA2) file...", end=' ')
    mesh_path = filedialog.askopenfilename(
        initialdir=input_dir,
        title="Select the mesh_mask.nc (ORCA2) file",
        filetypes=[("NetCDF files", "*.nc"), ("All files", "*.*")])
    if not mesh_path:
        messagebox.showinfo("Cancelled", "No mesh file selected —> exit!")
        return None, None, None, None
    print("done")

    print("Select and define the NetCDF file (output)...", end=' ')
    csv_base = os.path.splitext(os.path.basename(csv_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d-%Hh%M")
    suggest_name = f"{timestamp}_{csv_base}_to_orca2_nn.nc"

    out_path = filedialog.asksaveasfilename(
        initialdir=output_dir,
        title="Location and name of the output NetCDF file",
        initialfile=suggest_name,
        defaultextension=".nc",
        filetypes=[("NetCDF files", "*.nc"), ("All files", "*.*")])
    if not out_path:
        messagebox.showinfo("Cancelled", "No output file selected — exit.")
        return None, None, None, None
    print("done")

    img_path = os.path.splitext(out_path)[0] + ".png"

    return csv_path, mesh_path, out_path, img_path


def create_progress_bar():
    """
    Create and display a progress window.

    The window contains:
    - a label displaying current processing status
    - a progress bar updated during computation

    Returns
    -------
    progress_win : tkinter.Toplevel
        Window containing the progress UI.
    progress_label : tkinter.ttk.Label
        Label used to display processing status.
    progress_bar : tkinter.ttk.Progressbar
        Progress bar updated during chunk processing.

    Notes
    -----
    The window is set to stay on top of other windows.
    """
    progress_win = tk.Toplevel()
    progress_win.title("Processing — regrilling")

    progress_label = ttk.Label(progress_win, text="Initialization...")
    progress_label.pack(padx=10, pady=(10,0))

    progress_bar = ttk.Progressbar(progress_win, length=400)
    progress_bar.pack(padx=10, pady=10)

    progress_win.attributes("-topmost", True)
    progress_win.update()

    return progress_win, progress_label, progress_bar


def load_csv_and_select(root, csv_path):
    """
    Load CSV data and allow the user to select relevant columns.

    The function:
    - reads the CSV file using Polars
    - displays a GUI to select longitude, latitude, and value columns
    - removes rows with missing values
    - converts selected columns to NumPy arrays

    Parameters
    ----------
    root : tkinter.Tk
        Root Tkinter window.
    csv_path : str
        Path to the CSV file.

    Returns
    -------
    lon_csv : numpy.ndarray
        Array of longitudes (degrees).
    lat_csv : numpy.ndarray
        Array of latitudes (degrees).
    vals_csv : numpy.ndarray
        Array of values associated with each point.
    COL_VAL : str
        Name of the selected value column.

    Notes
    -----
    Returns None if the user cancels column selection.
    """
    print(f"Reading CSV: {csv_path}")

    df_full = pl.read_csv(csv_path)

    available_cols = df_full.columns
    available_col_dtypes = {
        name: str(dtype)
        for name, dtype in zip(df_full.columns, df_full.dtypes)
    }

    selector = ColumnSelector(root, available_cols, available_col_dtypes)
    selection = selector.show()

    if selection is None:
        return None

    COL_LON, COL_LAT, COL_VAL, DEFAULT_VAL = selection

    df = df_full.select([COL_LON, COL_LAT, COL_VAL]).drop_nulls()

    lon_csv = df[COL_LON].to_numpy()
    lat_csv = df[COL_LAT].to_numpy()
    vals_csv = df[COL_VAL].to_numpy()

    return lon_csv, lat_csv, vals_csv, COL_VAL


def run_regridding_loop(lon_csv, lat_csv, vals_csv,
                       lon_grid, lat_grid, tmask,
                       progress_bar, progress_label,
                       progress_win):
    """
    Perform nearest-neighbor regridding using chunk processing.

    This function:
    - converts coordinates to radians
    - iterates over input points in chunks
    - calls a Numba-accelerated kernel (`process_chunk`)
    - accumulates values and counts per grid cell
    - updates the GUI progress bar and status label

    Parameters
    ----------
    lon_csv : numpy.ndarray
        Longitudes of input points (degrees).
    lat_csv : numpy.ndarray
        Latitudes of input points (degrees).
    vals_csv : numpy.ndarray
        Values associated with each input point.
    lon_grid : numpy.ndarray
        ORCA2 grid longitudes (2D array).
    lat_grid : numpy.ndarray
        ORCA2 grid latitudes (2D array).
    tmask : numpy.ndarray
        Land/ocean mask (3D array: depth, y, x).
    progress_bar : tkinter.ttk.Progressbar
        Progress bar widget.
    progress_label : tkinter.ttk.Label
        Label displaying current processing status.
    progress_win : tkinter.Toplevel
        Progress window.

    Returns
    -------
    fer : numpy.ndarray
        Accumulated values per grid cell (shape: nx, ny, nz, nt).
    xsum : numpy.ndarray
        Count of contributions per grid cell.
    nt : int
        Number of time steps (currently 1).

    Notes
    -----
    - Only the surface mask (tmask[0,:,:]) is used.
    - Chunking improves performance and memory usage.
    """
    n_points = len(lon_csv)

    ny, nx = lon_grid.shape
    # nz = 1  mod 20260319-08h09
    nz = tmask.shape[0]
    nt = 1

    fer = np.zeros((nx, ny, nz, nt), dtype=np.float32)
    xsum = np.zeros_like(fer)

    lon_g_rad = np.radians(lon_grid)
    lat_g_rad = np.radians(lat_grid)
    lon_p_rad = np.radians(lon_csv)
    lat_p_rad = np.radians(lat_csv)

    chunk_size = 1000
    n_chunks = math.ceil(n_points / chunk_size)

    progress_bar["maximum"] = n_chunks

    for k in range(n_chunks):
        i0 = k * chunk_size
        i1 = min((k+1) * chunk_size, n_points)

        indices = np.arange(i0, i1)

        process_chunk(indices,
                      lon_g_rad, lat_g_rad, tmask[0,:,:],
                      lon_p_rad, lat_p_rad, vals_csv,
                      fer, xsum)
        progress_bar["value"] = k+1
        # add 20260319
        progress_label.config(
            text=f"Processing chunk {k+1}/{n_chunks} | Points: {i1}/{n_points}")
        progress_win.update_idletasks()
        
        progress_win.update()

    return fer, xsum, nt


def main():
    """
    Main entry point of the GUI application.

    This function orchestrates the full workflow:
    1. Initialize Tkinter environment
    2. Select input/output files
    3. Load CSV data and select columns
    4. Load ORCA2 mesh
    5. Perform nearest-neighbor regridding
    6. Compute averaged values
    7. Save results to NetCDF
    8. Generate and save visualization (PNG)
    9. Display completion message

    Notes
    -----
    - Designed for non-programmer users (GUI-based workflow)
    - Uses chunk processing for scalability
    - Outputs are saved in user-defined locations
    """
    root = tk.Tk()
    root.title("ORCA2 nearest-neighbor regridding")
    root.geometry("400x120")
    root.withdraw()
    root.update_idletasks()
    root.update()

    # files
    csv_path, mesh_path, out_path, img_path = select_files(root)
    if csv_path is None:
        return

    # progress bar
    progress_win, progress_label, progress_bar = create_progress_bar()

    # CSV
    result = load_csv_and_select(root, csv_path)
    if result is None:
        return

    lon_csv, lat_csv, vals_csv, COL_VAL = result
    progress_label.config(text=f"CSV read — {len(lon_csv)} valid points")
    progress_win.update_idletasks()

    # mesh
    lon_grid, lat_grid, tmask, depths = load_mesh(mesh_path)
    progress_label.config(
        text=f"Mesh read ({lon_grid.shape[0]}x{lon_grid.shape[1]})")
    progress_win.update_idletasks()

    # regridding 
    #fer, xsum, nt = run_regridding_loop(
    #    lon_csv, lat_csv, vals_csv,
    #    lon_grid, lat_grid, tmask,
    #    progress_bar, progress_win
    #)
    fer, xsum, nt = run_regridding_loop(
        lon_csv, lat_csv, vals_csv,
        lon_grid, lat_grid, tmask,
        progress_bar, progress_label, progress_win)

    # average
    mask = xsum > 0
    fer[mask] /= xsum[mask]

    # save
    progress_label.config(text="NetCDF writing...")
    progress_win.update_idletasks()
    save_netcdf(out_path, COL_VAL, fer, xsum, lon_grid, lat_grid, depths, nt)

    # plot
    # mod surface = fer.squeeze()[:, :, 0].T
    surface = fer[:, :, 0, 0].T
    progress_label.config(text="Generation figure...")
    progress_win.update_idletasks()
    save_plot(surface, lon_grid, lat_grid, COL_VAL, img_path)
    progress_label.config(text=f"Saved image: {img_path}")
    progress_win.update_idletasks()

    print("Done",
          f"Processing complete.\n"
          f"NetCDF: {out_path}\n"
          f"Image: {img_path}")
    
    messagebox.showinfo("Done",
                        f"Processing complete.\n"
                        f"NetCDF: {out_path}\n"
                        f"Image: {img_path}")
    progress_win.destroy()


if __name__ == "__main__":
    main()