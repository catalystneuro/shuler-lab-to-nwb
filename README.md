# Shuler lab to NWB

NWB conversion scripts for the [Shuler Lab](https://sites.google.com/site/marshallshuler/home) data to the [Neurodata Without Borders](https://www.nwb.org/) data format.


# Installation

Clone this repository and set up a conda environment:

```python
# Clone this repository
git clone https://github.com/catalystneuro/shuler-lab-to-nwb

# Set up a conda environment
conda env create --name env_shuler python=3.8 pip
conda activate env_shuler

# Install package
cd shuler-lab-to-nwb
pip install -e .
```

# NWB Conversion

To convert experimental data to NWB you'll need to provide:

- `spikeglx_file_path`, the path to the SpikeGLX recodings file
- `trials_file_path`, the path to a CSV file containing behavioral events data
- `reference_timestamps_file_path`, the path to the reference timestamps file for synchronization
- `subject_metadata_file_path`, the path to the JSON file containing Subject metadata
- `output_nwb_file`, the path for the resulting NWB file

Example:

```python
from shuler_lab_to_nwb import conversion

conversion.run_conversion(
    spikeglx_file_path="/path_to/ES029_2022-09-14_bot72_0_g0_t0.imec0.ap.bin",
    trials_file_path="/path_to/data_2022-09-14_12-13-31.csv",
    reference_timestamps_file_path="/path_to/ES029_2022-09-14_bot72_0_g0_tcat.imec0.ap.SY_384_6_0.txt",
    subject_metadata_file_path="/path_to/ES029_2022-09-14_bot72_0_g0/subject_metadata.json",
    output_nwb_file="output_file.nwb"
)
```

The trials file `data_2022-09-14_12-13-31.csv` is a CSV file containing formatted data from `data_2022-09-14_12-13-31.txt`.

![csv example](/media/example_csv.png)

The subject metadata file is a simple JSON file, containing metadata following the pynwb standard as described [here](https://pynwb.readthedocs.io/en/stable/pynwb.file.html#pynwb.file.Subject), example:

```json
{
    "subject_id": "ES029",
    "description": "ES029",
    "genotype": "wildtype",
    "sex": "M",
    "species": "black 6",
    "weight": 0.0254,
    "date_of_birth": "10-27-2021"
}
```

You can run this example conversion and visualize the resulting NWB file with the notebook in [examples folder](https://github.com/catalystneuro/shuler-lab-to-nwb/tree/main/examples).


# Spike sorting in the cloud

The infrasctructure documentation, Python scripts and Dockerfile for performing spike sorting in the Cloud are available in the [cloud folder](https://github.com/catalystneuro/shuler-lab-to-nwb/tree/main/cloud).