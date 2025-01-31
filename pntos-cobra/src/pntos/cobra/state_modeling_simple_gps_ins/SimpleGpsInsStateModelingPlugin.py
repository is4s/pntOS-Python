import builtins
from typing import cast

import numpy as np
from numpy import float64
from numpy.typing import NDArray
from pntos.api.plugins.common import LoggingLevel, Mediator
from pntos.api.plugins.fusion import StandardFusionEngine, VirtualStateBlock
from pntos.api.plugins.state_modeling import (
    StandardStateModelProvider,
    StateModelingPlugin,
    StateModelProviderType,
)
from pntos.cobra.utils import ImuModel

from .Pinson15NedBlock import Pinson15NedBlock
from .PinsonPositionMeasurementProcessor import (
    PinsonPositionMeasurementProcessor,
)


class SimpleGpsInsStateModelProvider(StandardStateModelProvider):
    """StandardStateModelProvider that offers a 15-state pinson state block and a position measurement processor."""

    _mediator: Mediator

    def __init__(self, mediator: Mediator):
        self._mediator = mediator
        self.processor_identifiers = ['pinson_position']
        self.block_identifiers = ['pinson15']
        self.virtual_block_identifiers = []

    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str,
    ) -> PinsonPositionMeasurementProcessor | None:
        """
        Generate a new StandardMeasurementProcessor that describes the relationship between a measurement and a set of states.

        Args:
            processor_index (int): Index into self.processor_identifiers used to select the desired type of measurement processor.
                - Index 0 corresponds to a PinsonPositionMeasurementProcessor.
                - All other indices will result in a return value of None.
            engine (StandardFusionEngine | None): An optional parameter that may be provided to the
                new processor, such that the processor may interact with the fusion engine it
                is being used in (for example, to add/remove states). Set it to
                ``None`` when no engine is available for the processor to use.
            label (str): A string which will be used to populate the ``label`` field
                of the newly created processor. This ``label`` will be the unique
                name for the returned instance of a processor, and used to
                track the processor throughout its lifecycle. Note that it
                differs from :attr:`processor_identifiers` which is the model's mechanism
                for selecting the *type* of processor to create.
            config_group (str): Indicates which (if any) parameter group in the
                registry may be used to obtain additional configuration values to
                generate the new processor. If the processor requires no
                outside configuration, ``config_group`` may be ``None``.

        Returns:
            StandardMeasurementProcessor | None: The newly created StandardMeasurementProcessor or ``None`` when no processor can be produced
            with the given ``processor_index``, ``engine``, and ``config_group``.
        """
        if processor_index == 0:
            batch = self._mediator.registry.batch_start(config_group)
            l_ps_p = batch.get_value('lever_arm', np.ndarray)
            C_platform_to_sensor = batch.get_value('orientation', np.ndarray)
            assert C_platform_to_sensor is not None
            assert l_ps_p is not None
            return PinsonPositionMeasurementProcessor(
                label,
                state_block_labels,
                self._mediator,
                l_ps_p,
                C_platform_to_sensor,
            )

        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid processor index of {processor_index}. SimpleGpsInsStateModelProvider provides {len(self.processor_identifiers)} processors.',
        )
        return None

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str,
    ) -> Pinson15NedBlock | None:
        """
        Generate a new StandardStateBlock that describes a set of states and how they propagate over time.

        Args:
            block_index (int): Index into self.block_identifiers used to select the desired type of state block.
                - Index 0 corresponds to a Pinson15NedBlock.
                - All other indices will result in a return value of None.
            engine (StandardFusionEngine | None): An optional parameter that may be provided to the
                new block, such that the block may interact with the fusion engine it
                is being used in (for example, to add/remove states). Set it to
                ``None`` when no engine is available for the block to use.
            label (str): A string which will be used to populate the ``label`` field
                of the newly created state block. This ``label`` will be the unique
                name for the returned instance of a state block, and used to
                track the state block throughout its lifecycle. Note that it
                differs from :attr:`block_identifiers` which is the model's mechanism
                for selecting the *kind* of state block to create.
            config_group (str): Indicates which (if any) parameter group in the
                registry may be used to obtain additional configuration values to
                generate the new state block. If the state block requires no
                outside configuration, ``config_group`` may be ``None``.

        Returns:
            StandardStateBlock | None: The newly created StandardStateBlock or ``None`` when no state block can be produced
            with the given ``block_index``, ``engine``, and ``config_group``.
        """
        if block_index == 0:
            batch = self._mediator.registry.batch_start(config_group)
            accel_bias_sigma = batch.get_value('accel_bias_sigma', np.ndarray)
            accel_bias_tau = batch.get_value('accel_bias_tau', np.ndarray)
            accel_rw_sigma = batch.get_value('accel_rw_sigma', np.ndarray)
            gyro_bias_sigma = batch.get_value('gyro_bias_sigma', np.ndarray)
            gyro_bias_tau = batch.get_value('gyro_bias_tau', np.ndarray)
            gyro_rw_sigma = batch.get_value('gyro_rw_sigma', np.ndarray)
            batch.batch_end()

            # TODO: would be nice to not have to check for None returns
            assert accel_bias_sigma is not None
            assert accel_bias_tau is not None
            assert accel_rw_sigma is not None
            assert gyro_bias_sigma is not None
            assert gyro_bias_tau is not None
            assert gyro_rw_sigma is not None

            return Pinson15NedBlock(
                label,
                self._mediator,
                ImuModel(
                    accel_bias_sigma,
                    accel_bias_tau,
                    accel_rw_sigma,
                    gyro_bias_sigma,
                    gyro_bias_tau,
                    gyro_rw_sigma,
                ),
            )

        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid block index of {block_index}. SimpleGpsInsStateModelProvider provides {len(self.block_identifiers)} state blocks.',
        )
        return None

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str,
    ) -> VirtualStateBlock | None:
        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid virtual block index of {virtual_block_index}. SimpleGpsInsStateModelProvider provides {len(self.virtual_block_identifiers)} virtual state blocks.',
        )
        return None


class SimpleGpsInsStateModelingPlugin(StateModelingPlugin):
    """StateModelingPlugin that generates a SimpleGpsInsStateModelProvider."""

    _mediator: Mediator

    def __init__(self, identifier: str):
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        assert mediator is not None
        self._mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def new_state_model_provider(
        self, type: type[StateModelProviderType]
    ) -> StateModelProviderType | None:
        if not self.is_fusion_type_supported(type):
            return None

        return SimpleGpsInsStateModelProvider(self._mediator)

    def is_fusion_type_supported(self, type: StateModelProviderType) -> bool:
        return type is StandardStateModelProvider
