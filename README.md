# Mangroves ORCA2 Regridding Tool

[![Python](https://img.shields.io/badge/python-3.10--3.11-blue)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green)]()
[![Status](https://img.shields.io/badge/status-active-success)]()

Nearest-neighbor regridding of geospatial point data onto the **ORCA2 ocean model grid**.

**Author:** Eric Duvieilbourg (CNRS / LEMAR)

---

## Overview

This tool provides a **graphical interface (GUI)** to project irregular geospatial observations (e.g. mangrove occurrences) onto a structured ocean model grid.

Designed for:

* scientists
* non-programmers
* reproducible workflows

---

## Software status

* Version: v1.0.1
* Status: stable
* DOI registered (Zenodo)
* Suitable for scientific use and reproducible workflows

---

## Scientific context

This tool enables:

* Data–model comparison
* Spatial aggregation of ecological observations
* Preprocessing for Earth system models

---

## Methodology

Regridding uses a **nearest-neighbor search on the sphere**:

* Coordinates converted to radians
* Distance via **spherical dot product**
* Mapping to closest valid ORCA2 grid cell
* Accumulation + averaging

---

## ORCA2 Grid

* Curvilinear ocean grid
* Variable resolution (finer near poles)
* Land/ocean masking

---

## Workflow

1. Select CSV file (point data)
2. Select ORCA2 mesh (NetCDF)
3. Select columns (lon / lat / value)
4. Run nearest-neighbor regridding
5. Export:

   * NetCDF file
   * PNG visualization

---

## Installation (detailled)

### 1. Install `uv`

Mac / Linux:

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

*If the above fails (e.g., on some Linux distributions), use:*

```bash
sudo snap install astral-uv --classic
```
*Note: The `--classic` flag is required for full functionality*

#### System Dependencies (Linux only)

! Ensure the following packages are installed:

```bash
sudo apt update
sudo apt install -y libssl-dev libffi-dev python3-dev
```

Windows:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

---

### 2. Clone or download repository

If you are using Git, you can do the following:

```bash
git clone https://github.com/eduvieilbourg/mangroves_orca2.git
```

Or, download only the .zip file and then unzip it, select the correct directory using:

```bash
cd mangroves_orca2
```

---

### 3. Install dependencies

```bash
uv sync
```

*This will generate/update the `uv.lock` file if it doesn't exist.* 

---

### 4. Verify `uv.lock`

* If `uv.lock` is missing after `uv sync`, run:
```bash
uv lock
```

---

### 5. Run the tool

```bash
uv run python scripts/run_regridding.py
```

---

## Project structure

```bash
mangroves_orca2/
│
├── src/
│   └── mangroves_orca2/
│       ├── regrid.py
│       ├── io.py
│       ├── plotting.py
│       ├── utils.py
│       └── tk_column_selector.py
│
├── scripts/
│   └── run_regridding.py
│
├── data_inputs/      # input CSV + mesh
├── data_outputs/     # generated NetCDF + PNG
│
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── uv.lock
└── .gitignore
```

---

## Inputs (`data_inputs/`)

* CSV file:

  * longitude
  * latitude
  * variable (numeric or categorical)

* ORCA2 mesh:

  * NetCDF (`mesh_mask.nc`)

---

## Outputs (`data_outputs/`)

* NetCDF:

  * regridded variable
  * count per grid cell

* PNG:

  * 2D surface visualization

* Naming convention:

```text
YYYYMMDD-HHhMN_filename_to_orca2_nn.nc
```

---

## Performance

* Numba-accelerated computation
* Chunk processing
* Scales to large datasets (10⁶+ points)

---

## ⚠Limitations

* Brute-force nearest neighbor → O(Ngrid)
* Surface layer only (z = 0)
* No interpolation (strict NN)

---

## DOI

This software is archived on Zenodo:

https://doi.org/10.5281/zenodo.19129260

Each release is permanently versioned and citable.

---

## HAL record

This software is also referenced in HAL (French open archive).

https://hal.science/view/index/docid/5560796

---

## License

MIT License (see LICENSE file)

---

## Citation

If you use this software, please cite:

```text
Duvieilbourg, E. (2026).
Mangroves ORCA2 Regridding Tool (v1.0.1).
Zenodo. https://doi.org/10.5281/zenodo.19129260
```

Full citation metadata available in `CITATION.cff`.

---
