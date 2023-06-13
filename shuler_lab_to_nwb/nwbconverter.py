from neuroconv import NWBConverter
from neuroconv.datainterfaces import SpikeGLXRecordingInterface

from shuler_lab_to_nwb.behavior_datainterface import ShulerBehaviorInterface
# from shuler_lab_to_nwb.fiberphotometry_datainterface import FiberPhotometryInterface


class ShulerNWBConverter(NWBConverter):
    """Primary conversion class for Shuler lab datasets."""

    data_interface_classes = dict(
        Recording=SpikeGLXRecordingInterface,
        Behavior=ShulerBehaviorInterface,
        # FiberPhotometry=FiberPhotometryInterface,
    )