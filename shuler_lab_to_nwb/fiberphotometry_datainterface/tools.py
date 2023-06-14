from typing import Optional
import pandas as pd
from hdmf.backends.hdf5 import H5DataIO
from hdmf.common import DynamicTableRegion
from ndx_photometry import FibersTable, FiberPhotometry, ExcitationSourcesTable, PhotodetectorsTable, FluorophoresTable
from pynwb import NWBFile
from pynwb.ophys import RoiResponseSeries


def read_fp_file(file_path: str) -> pd.DataFrame:
    """Reads a fiber photometry file (csv) and returns a pandas DataFrame."""
    df = pd.read_csv(
        file_path,
        sep=" ",
        header=None,
        names=["timestamp", "unknown", "GFP_first_branch", "RFP_first_branch", "GFP_second_branch", "RFP_second_branch"],
        index_col=False
    )
    df = df.drop(columns=["unknown"])
    df["timestamp"] = df["timestamp"] / 1000

    # Separate signal and isosbestic dataframes using the mask: True for signal rows, False for isosbestic rows
    mask = df.index % 2 == 0
    df_signal = df[mask]
    df_isosbestic = df[~mask]
    df_signal = df_signal.reset_index(drop=True)
    df_isosbestic = df_isosbestic.reset_index(drop=True)

    # Rename isosbestic columns to include _isosbestic
    df_isosbestic = df_isosbestic.rename(columns={
        "GFP_first_branch": "GFP_first_branch_isosbestic", 
        "RFP_first_branch": "RFP_first_branch_isosbestic", 
        "GFP_second_branch": "GFP_second_branch_isosbestic", 
        "RFP_second_branch": "RFP_second_branch_isosbestic"
    })
    return df_signal, df_isosbestic


def add_photometry(
    photometry_dataframe: pd.DataFrame, 
    isosbestic_dataframe: pd.DataFrame,
    nwbfile: NWBFile, 
    metadata: dict,
):
    # Create the ExcitationSourcesTable that holds metadata for the LED sources
    excitation_sources_table = ExcitationSourcesTable(description=metadata["FiberPhotometry"]["ExcitationSourcesTable"]["description"])
    for source_metadata in metadata["FiberPhotometry"]["ExcitationSourcesTable"]["items"]:
        excitation_sources_table.add_row(
            peak_wavelength=source_metadata["peak_wavelength"],
            source_type=source_metadata["source_type"],
        )

    # Create the PhotodetectorsTable that holds metadata for the photodetector.
    photodetectors_table = PhotodetectorsTable(description=metadata["FiberPhotometry"]["PhotodetectorsTable"]["description"])
    for photodetector_metadata in metadata["FiberPhotometry"]["PhotodetectorsTable"]["items"]:
        photodetectors_table.add_row(
            type=photodetector_metadata["type"],
            peak_wavelength=photodetector_metadata["peak_wavelength"],
        )

    # Create the FluorophoresTable that holds metadata for the fluorophores.
    fluorophores_table = FluorophoresTable(description=metadata["FiberPhotometry"]["FluorophoresTable"]["description"])
    for fluorophore_metadata in metadata["FiberPhotometry"]["FluorophoresTable"]["items"]:
        fluorophores_table.add_row(
            label=fluorophore_metadata["label"],
            location=fluorophore_metadata["location"],
            coordinates=fluorophore_metadata["coordinates"],
        )

    # Create the FibersTable that holds metadata for fibers
    fibers_table = FibersTable(description=metadata["FiberPhotometry"]["FibersTable"]["description"])

    # Add the metadata tables to the metadata section of the NWBFile
    fiber_photometry = FiberPhotometry(
        fibers=fibers_table,
        excitation_sources=excitation_sources_table,
        photodetectors=photodetectors_table,
        fluorophores=fluorophores_table,
    )
    nwbfile.add_lab_meta_data(fiber_photometry)

    # Important: we add the fibers to the fibers table _after_ adding the metadata
    # This ensures that we can find this data in their tables of origin
    for fiber_metadata in metadata["FiberPhotometry"]["FibersTable"]["items"]:
        fibers_table.add_fiber(
            location=fiber_metadata["location"],
            notes=fiber_metadata["notes"],
            excitation_source=fiber_metadata["excitation_source"],
            photodetector=fiber_metadata["photodetector"],
            fluorophores=fiber_metadata["fluorophores"],
        )

    # # Create the RoiResponseSeries that holds the intensity values
    # for photometry_metadata in metadata["FiberPhotometry"]["RoiResponseSeries"]:
    #     # Create reference for fibers
    #     rois = DynamicTableRegion(
    #         name="rois",
    #         data=[photometry_metadata["rois"]],
    #         description="source fibers",
    #         table=fibers_table,
    #     )
    #     column = photometry_metadata["name"]
    #     if "_isosbestic" in column:
    #         data = H5DataIO(isosbestic_dataframe[column].values, compression=True)
    #     else:
    #         data = H5DataIO(photometry_dataframe[column].values, compression=True)
    #     roi_response_series = RoiResponseSeries(
    #         name=photometry_metadata["name"],
    #         description=photometry_metadata["description"],
    #         data=data,
    #         unit=photometry_metadata["unit"],
    #         timestamps=H5DataIO(photometry_dataframe["timestamp"].values, compression=True),
    #         rois=rois,
    #     )
    #     nwbfile.add_acquisition(roi_response_series)
    
    return nwbfile