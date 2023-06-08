from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
from pynwb.file import NWBFile
from neuroconv.basetemporalalignmentinterface import BaseTemporalAlignmentInterface
from neuroconv.tools.nwb_helpers import make_or_load_nwbfile
from neuroconv.utils import FilePathType, dict_deep_update

from .tools import add_behavioral_events, add_trials


class ShulerBehaviorInterface(BaseTemporalAlignmentInterface):
    """Data interface for Shuler lab Behavioral data."""

    def __init__(
        self,
        trials_file_path: FilePathType,
        reference_timestamps_file_path: FilePathType,
        verbose: bool = True,
    ):
        """
        Interface for writing Shuler behavioral data to NWB.

        Parameters
        ----------
        trials_file_path : FilePathType
            Path to the trials file (.csv) containing the behavioral data.
        reference_timestamps_file_path : FilePathType
            Path to the reference timestamps file (.csv) containing the reference timestamps.
        verbose : bool, default: True
            controls verbosity. ``True`` by default.
        """
        self.verbose = verbose
        super().__init__(
            trials_file_path=trials_file_path,
            reference_timestamps_file_path=reference_timestamps_file_path,
        )

    def get_original_timestamps(self) -> np.ndarray:
        pass

    def get_timestamps(self) -> np.ndarray:
        return self.df["session_time"].values

    def set_aligned_timestamps(self, aligned_timestamps: np.ndarray):
        self.df["session_time_sync"] = aligned_timestamps

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
            # Read trials data
            df_0 = pd.read_csv(self.source_data["trials_file_path"])
            # Read reference_aligned_timestamps
            df_reference_aligned_timestamps = pd.read_csv(self.source_data["reference_timestamps_file_path"], names=["timestamp"])
            reference_aligned_timestamps = df_reference_aligned_timestamps["timestamp"].values
            # Get reference_unaligned_timestamps
            df_reference_unaligned_timestamps = df_0.loc[(df_0.key == "camera") & (df_0.value == 1.0)][-len(df_reference_aligned_timestamps):]
            reference_unaligned_timestamps = df_reference_unaligned_timestamps["session_time"].values
            # Remove timestamps from before the start and after the end of spikeglx recording
            self.df = df_0[(df_0.session_time >= reference_unaligned_timestamps[0]) & (df_0.session_time <= reference_unaligned_timestamps[-1])]
            # Align timestamps, update self.df with new timestamps
            self.align_by_interpolation(
                unaligned_timestamps=reference_unaligned_timestamps, 
                aligned_timestamps=reference_aligned_timestamps
            )
            # Add behavioral events
            nwbfile_out = add_behavioral_events(
                df=self.df, 
                nwbfile=nwbfile_out, 
                metadata=metadata
            )
            # Add trials
            nwbfile_out = add_trials(
                df=self.df,
                nwbfile=nwbfile_out,
                metadata=metadata
            )