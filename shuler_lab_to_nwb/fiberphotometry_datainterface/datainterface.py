from typing import Optional
import numpy as np
import pandas as pd
from pynwb.file import NWBFile
from neuroconv.utils import load_dict_from_file
from neuroconv.basetemporalalignmentinterface import BaseTemporalAlignmentInterface
from neuroconv.tools.nwb_helpers import make_or_load_nwbfile
from neuroconv.utils import FilePathType, dict_deep_update

from .tools import read_fp_file, add_photometry


class ShulerFiberPhotometryInterface(BaseTemporalAlignmentInterface):
    """Data interface for Shuler lab Fiber Photometry data."""

    def __init__(
        self,
        photometry_file_path: FilePathType,
        metadata_file_path: FilePathType,
        verbose: bool = True,
    ):
        """
        Interface for writing Shuler Fiber Photometry data to NWB.

        Parameters
        ----------
        photometry_file_path : FilePathType
            Path to the file (.csv) containing the photometry time series data.
        metadata_file_path : FilePathType
            Path to the file (.yaml) containing the metadata for the photometry data.
        verbose : bool, default: True
            controls verbosity. ``True`` by default.
        """
        self.verbose = verbose
        super().__init__(
            photometry_file_path=photometry_file_path,
            metadata_file_path=metadata_file_path
        )
    
    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        # metadata_schema["properties"]["FiberPhotometry"] = {
        #     "type": "object",
        #     "properties": {
        #         "area": {"type": "string"},
        #         "reference_max": {"type": "number"},
        #         "signal_max": {"type": "number"},
        #         "signal_reference_corr": {"type": "number"},
        #         "snr": {"type": "number"},
        #     },
        # }
        return metadata_schema
    
    def get_metadata(self) -> dict:
        base_metadata = super().get_metadata()
        metadata = load_dict_from_file(self.source_data["metadata_file_path"])
        metadata = dict_deep_update(base_metadata, metadata)
        return metadata
    
    def get_original_timestamps(self) -> np.ndarray:
        pass

    def get_timestamps(self) -> np.ndarray:
        pass

    def set_aligned_timestamps(self, aligned_timestamps: np.ndarray):
        pass

    def run_conversion(
        self,
        nwbfile_path: Optional[FilePathType] = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        overwrite: bool = False,
    ):
        """
        Run conversion to nwb.

        Parameters
        ----------
        nwbfile_path: FilePathType
            Path for where to write or load (if overwrite=False) the NWBFile.
            If specified, this context will always write to this location.
        nwbfile: NWBFile
            nwb file to which the recording information is to be added
        metadata: dict
            metadata info for constructing the nwb file (optional).
        overwrite: bool, optional
            Whether to overwrite the NWBFile if one exists at the nwbfile_path.
        """
        base_metadata = self.get_metadata()
        if metadata is None:
            metadata = {}
        metadata = dict_deep_update(base_metadata, metadata)

        with make_or_load_nwbfile(
            nwbfile_path=nwbfile_path, 
            nwbfile=nwbfile, 
            metadata=metadata, 
            overwrite=overwrite, 
            verbose=self.verbose
        ) as nwbfile_out:
            # Read fiber photometry data
            self.df_signal, self.df_isosbestic = read_fp_file(file_path=self.source_data["photometry_file_path"])
            # Add photometry data to nwbfile
            nwbfile_out = add_photometry(
                photometry_dataframe=self.df_signal, 
                isosbestic_dataframe=self.df_isosbestic,
                nwbfile=nwbfile_out, 
                metadata=metadata,
            )