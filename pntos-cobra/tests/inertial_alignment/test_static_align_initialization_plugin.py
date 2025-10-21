from navtk.filtering import hg1700_model
from pntos.cobra import StaticAlignInitializationPlugin
from pntos.cobra.config import (
    StaticAlignmentConfig,
    config_to_registry,
    imu_model_to_config,
)

from .utils import check_inertial_align_initialization_plugin, set_up_mediator


def test() -> None:
    # Set up and test plugin.
    mediator = set_up_mediator()
    identifier = 'Cobra static align initialization plugin'
    plugin = StaticAlignInitializationPlugin(identifier)
    plugin.init_plugin(None, mediator)

    # Set up config.
    static_time = 120.0
    group = 'test/config/static_align'
    imu_config = imu_model_to_config(
        model=hg1700_model(),
        group=group,
    )
    config = StaticAlignmentConfig(
        static_time=static_time,
        imu_model=imu_config,
        group=group,
    )
    config_to_registry(config, mediator)
    check_inertial_align_initialization_plugin(
        plugin, group, config.static_time, identifier, False
    )


if __name__ == '__main__':
    test()
