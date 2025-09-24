import numpy as np
from navtk.filtering import hg1700_model
from pntos.cobra import ManualHeadingAlignInitializationPlugin
from pntos.cobra.config import (
    ManualHeadingAlignmentConfig,
    config_to_registry,
    imu_model_to_config,
)

from .utils import check_inertial_align_initialization_plugin, set_up_mediator


def test() -> None:
    # Set up and test plugin.
    mediator = set_up_mediator()
    identifier = 'Cobra static align initialization plugin'
    plugin = ManualHeadingAlignInitializationPlugin(identifier)
    plugin.init_plugin(None, mediator)

    # Set up config.
    static_time = 120.0
    group = 'test/config/static_align'
    imu_config = imu_model_to_config(
        model=hg1700_model(),
        group=group,
    )

    config = ManualHeadingAlignmentConfig(
        static_time=static_time,
        imu_model=imu_config,
        heading=-np.pi / 2,
        heading_sigma=0.017453292519943295,
        group=group,
    )
    config_to_registry(config, mediator)
    check_inertial_align_initialization_plugin(
        plugin, group, config.static_time, identifier, True
    )


if __name__ == '__main__':
    test()
