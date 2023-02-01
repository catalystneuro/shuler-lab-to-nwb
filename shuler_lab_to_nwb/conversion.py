import pandas as pd
import numpy as np
import json
import datetime
from dateutil import tz
import pynwb
from neuroconv.datainterfaces import SpikeGLXRecordingInterface


def align_by_interpolation(timestamps, reference_aligned_timestamps, reference_unaligned_timestamps):
    return np.interp(
        x=timestamps, 
        xp=reference_unaligned_timestamps, 
        fp=reference_aligned_timestamps
    )


def run_conversion(
    spikeglx_file_path: str,
    trials_file_path: str,
    reference_timestamps_file_path: str,
    subject_metadata_file_path: str,
    output_nwb_file: str
):

    # Instantiate SpikeGLX interface
    interface = SpikeGLXRecordingInterface(file_path=spikeglx_file_path, verbose=False)

    # Extract what metadata we can from the source files
    metadata = interface.get_metadata()
    session_start_time = metadata["NWBFile"]["session_start_time"].replace(tzinfo=tz.gettz("US/Pacific"))
    metadata["NWBFile"].update(session_start_time=session_start_time)

    # TODO - add Subject metadata
    with open(subject_metadata_file_path, "r") as f:
        subject_metadata = json.load(f)
    subject_metadata["date_of_birth"] = datetime.datetime.strptime(subject_metadata["date_of_birth"], "%m-%d-%Y").replace(tzinfo=tz.gettz("US/Pacific"))
    metadata["Subject"] = subject_metadata

    # Run the ecephys conversion
    interface.run_conversion(nwbfile_path=output_nwb_file, metadata=metadata)

    # Read trials data
    df_0 = pd.read_csv(trials_file_path)

    # Read reference_aligned_timestamps
    df_reference_aligned_timestamps = pd.read_csv(reference_timestamps_file_path, names=["timestamp"])
    reference_aligned_timestamps = df_reference_aligned_timestamps["timestamp"].values

    # Get reference_unaligned_timestamps
    df_reference_unaligned_timestamps = df_0.loc[(df_0.key == "camera") & (df_0.value == 1.0)][-len(df_reference_aligned_timestamps):]
    reference_unaligned_timestamps = df_reference_unaligned_timestamps["session_time"].values

    # Remove timestamps from before the start and after the end of spikeglx recording
    df_1 = df_0[(df_0.session_time >= reference_unaligned_timestamps[0]) & (df_0.session_time <= reference_unaligned_timestamps[-1])]

    # Align timestamps
    df_1["session_time_sync"] = align_by_interpolation(
        timestamps=df_1["session_time"].values, 
        reference_aligned_timestamps=reference_aligned_timestamps, 
        reference_unaligned_timestamps=reference_unaligned_timestamps
    )

    # Extract behavioral events and add to nwb file
    with pynwb.NWBHDF5IO(output_nwb_file, mode='r+') as io:
        nwbfile = io.read()
        
        behavioral_events = pynwb.behavior.BehavioralEvents(name='BehavioralEvents')

        events_names = ['LED', 'head', 'lick', 'reward', 'forced_switch', 'forced', 'probability']
        for event_name in events_names:
            df_aux = df_1.loc[df_1.key == event_name][["session_time_sync", "value"]]
            df_aux["value"] = df_aux["value"].astype("int")
            behavioral_events.create_timeseries(
                name=event_name,
                timestamps=df_aux["session_time_sync"].values,
                data=df_aux["value"].values,
                unit="no unit",
                continuity="instantaneous"
            )

        behavior_module = nwbfile.create_processing_module(
            name="behavior", description="Processed behavioral data"
        )
        behavior_module.add(behavioral_events)

        # Write the modified NWB file
        io.write(nwbfile)
        
    # Extract trials information
    df_aux = df_1.loc[df_1.key == "trial"][["session_time_sync", "task", "phase", "port", "value", "trial"]]

    df_trials_start = df_aux.loc[df_aux.value == 1.0]
    df_trials_start = df_trials_start.drop(labels=["value"], axis=1)
    df_trials_start = df_trials_start.rename(columns={"session_time_sync": "start_time"})
    df_trials_start = df_trials_start.reset_index(drop=True)

    df_trials_stop = df_aux.loc[df_aux.value == 0.0]
    df_trials_stop = df_trials_stop.drop(labels=["value", "phase", "port", "value", "task"], axis=1)
    df_trials_stop = df_trials_stop.rename(columns={"session_time_sync": "stop_time"})
    last_stop_time = df_1.iloc[-1]["session_time_sync"]
    d = {"stop_time": [last_stop_time], "trial": [len(df_trials_start)]}
    df_trials_stop = pd.concat([df_trials_stop, pd.DataFrame(d)])
    df_trials_stop = df_trials_stop.reset_index(drop=True)

    df_trials = pd.merge(df_trials_start, df_trials_stop, on='trial', how='outer')
    df_trials["trial"] = df_trials["trial"].astype("int")

    # Add trials information to nwb file
    with pynwb.NWBHDF5IO(output_nwb_file, mode='r+') as io:
        nwbfile = io.read()

        for cn in ["task", "phase", "port", "trial"]:
            nwbfile.add_trial_column(name=cn, description="no description")

        for r in df_trials.iterrows():
            nwbfile.add_trial(**r[1].to_dict())

        # Write the modified NWB file
        io.write(nwbfile)