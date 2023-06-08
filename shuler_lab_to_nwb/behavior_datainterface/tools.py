import pandas as pd
import pynwb


def add_behavioral_events(
    df: pd.DataFrame,
    nwbfile: pynwb.NWBFile,
    metadata: dict
):
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