import pandas as pd
from dateutil import tz
from pynwb import NWBHDF5IO
from neuroconv.datainterfaces import SpikeGLXRecordingInterface


def run_conversion(
    spikeglx_file_path: str,
    trials_file_path: str,
    output_nwb_file: str
):

    # Instantiate SpikeGLX interface
    interface = SpikeGLXRecordingInterface(file_path=spikeglx_file_path, verbose=False)

    # Extract what metadata we can from the source files
    metadata = interface.get_metadata()
    session_start_time = metadata["NWBFile"]["session_start_time"].replace(tzinfo=tz.gettz("US/Pacific"))
    metadata["NWBFile"].update(session_start_time=session_start_time)

    # Run the ecephys conversion
    interface.run_conversion(nwbfile_path=output_nwb_file, metadata=metadata)

    # Read trials data
    df_0 = pd.read_csv(trials_file_path)
    df_trials = df_0.loc[df_0.key == "trial"][["session_time", "task", "phase", "port", "value", "trial"]]

    df_trials_start = df_trials.loc[df_trials.value == 1.0]
    df_trials_start = df_trials_start.drop(labels=["value"], axis=1)
    df_trials_start = df_trials_start.rename(columns={"session_time": "start_time"})
    df_trials_start = df_trials_start.reset_index(drop=True)

    df_trials_stop = df_trials.loc[df_trials.value == 0.0]
    df_trials_stop = df_trials_stop.drop(labels=["value", "phase", "port", "value", "task"], axis=1)
    df_trials_stop = df_trials_stop.rename(columns={"session_time": "stop_time"})
    last_stop_time = df_0.iloc[-1]["session_time"]
    d = {"stop_time": [last_stop_time], "trial": [len(df_trials_start)]}
    df_trials_stop = pd.concat([df_trials_stop, pd.DataFrame(d)])
    df_trials_stop = df_trials_stop.reset_index(drop=True)

    df_merged = pd.merge(df_trials_start, df_trials_stop, on='trial', how='outer')
    df_merged["trial"] = df_merged["trial"].astype("int")

    # Add trials information to nwb file
    with NWBHDF5IO(output_nwb_file, mode='r+') as io:
        nwbfile = io.read()

        for cn in ["task", "phase", "port", "trial"]:
            nwbfile.add_trial_column(name=cn, description="no description")

        for r in df_merged.iterrows():
            nwbfile.add_trial(**r[1].to_dict())

        # Write the modified NWB file
        io.write(nwbfile)