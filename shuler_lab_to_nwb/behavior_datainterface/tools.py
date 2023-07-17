import pandas as pd
import pynwb


def add_behavioral_events(
    df: pd.DataFrame,
    nwbfile: pynwb.NWBFile,
    metadata: dict
) -> pynwb.NWBFile:
    behavioral_events = pynwb.behavior.BehavioralEvents(name='BehavioralEvents')
    events_names = ['LED', 'head', 'lick', 'reward', 'forced_switch', 'forced', 'probability']
    for event_name in events_names:
        df_aux = df.loc[df.key == event_name][["session_time_sync", "value"]]
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
    return nwbfile


def add_trials(
    df: pd.DataFrame,
    nwbfile: pynwb.NWBFile,
    metadata: dict
) -> pynwb.NWBFile:
    # Extract trials information
    df_aux = df.loc[df.key == "trial"][["session_time_sync", "task", "phase", "port", "value", "trial"]]

    df_trials_start = df_aux.loc[df_aux.value == 1.0]
    df_trials_start = df_trials_start.drop(labels=["value"], axis=1)
    df_trials_start = df_trials_start.rename(columns={"session_time_sync": "start_time"})
    df_trials_start = df_trials_start.reset_index(drop=True)

    df_trials_stop = df_aux.loc[df_aux.value == 0.0]
    df_trials_stop = df_trials_stop.drop(labels=["value", "phase", "port", "value", "task"], axis=1)
    df_trials_stop = df_trials_stop.rename(columns={"session_time_sync": "stop_time"})
    last_stop_time = df.iloc[-1]["session_time_sync"]
    d = {"stop_time": [last_stop_time], "trial": [len(df_trials_start)]}
    df_trials_stop = pd.concat([df_trials_stop, pd.DataFrame(d)])
    df_trials_stop = df_trials_stop.reset_index(drop=True)

    df_trials = pd.merge(df_trials_start, df_trials_stop, on='trial', how='outer')
    df_trials["trial"] = df_trials["trial"].astype("int")

    # Add trials information to nwb file
    for cn in ["task", "phase", "port", "trial"]:
        nwbfile.add_trial_column(name=cn, description="no description")

    for r in df_trials.iterrows():
        nwbfile.add_trial(**r[1].to_dict())