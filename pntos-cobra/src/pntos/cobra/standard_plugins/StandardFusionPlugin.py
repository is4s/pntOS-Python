"""Python API of pntOS."""

import copy
from dataclasses import dataclass

import numpy as np
from aspn23 import TypeTimestamp
from numpy import float64
from numpy.typing import NDArray
from pntos import api
from pntos.api import (
    CrossCovariances,
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    FusionEngineType,
    FusionPlugin,
    LoggingLevel,
    Mediator,
    Message,
    StandardDynamicsModel,
    StandardFusionStrategy,
    StandardMeasurementModel,
    StandardMeasurementProcessor,
    StandardStateBlock,
    VirtualStateBlock,
)
from pntos.cobra.utils import validate_array


@dataclass
class stateblock_info:
    num_states: int
    start_index: int
    stop_index: int
    block: StandardStateBlock


class StandardFusionEngine(api.StandardFusionEngine):
    """
    A simple fusion engine designed to use data from multiple sensors and output a unified state estimate.
    """

    def __init__(self, mediator: Mediator) -> None:
        """
        A Simple Fusion Engine

        Args:
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
        """
        self._time: TypeTimestamp = TypeTimestamp(0)  # property
        self._sb: dict[
            str, stateblock_info
        ] = {}  # Dictionary of stateblock information
        self._mp: dict[
            str, StandardMeasurementProcessor
        ] = {}  # Dictionary of measurement processors
        self._num_states = 0
        self._mediator = mediator
        self._strategy: StandardFusionStrategy | None = None

    @property
    def time(self) -> TypeTimestamp:
        """The current time of the filter."""
        return self._time

    @time.setter
    def time(self, timestamp: TypeTimestamp) -> None:
        self._time = timestamp

    @property
    def strategy(self) -> StandardFusionStrategy | None:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: StandardFusionStrategy | None) -> None:
        self._strategy = strategy

    def _re_index_stateblocks(self) -> None:
        """
        Re-indexes the stateblocks, using the num_states field and the order to
        determine indices (zero-indexed).  This can be used whenever a dictionary
        entry (stateblock) is removed to correct the indexes to account for the
        removed stateblock.
        """
        # Get list of current stateblock labels
        sb_list = list(self._sb.keys())

        # Iterate through the stateblocks and use the num_states
        # field to calculate the new index values
        i_next = 0
        for this_key in sb_list:
            self._sb[this_key].start_index = i_next
            self._sb[this_key].stop_index = i_next + self._sb[this_key].num_states - 1
            i_next = i_next + self._sb[this_key].num_states

    @property
    def num_states(self) -> int:
        return self._num_states

    @property
    def state_block_labels(self) -> list[str] | None:
        if self._num_states > 0:
            return list(self._sb.keys())
        self._mediator.log_message(LoggingLevel.WARN, 'No state blocks added.')
        return None

    def add_state_block(
        self,
        block: StandardStateBlock,
        initial_estimate_covariance: EstimateWithCovariance,
        cross_covariances: CrossCovariances | None = None,
    ) -> None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        # Verify that the initial estimate and covariance are generic (standard),
        # because that's the only one currently supported
        if initial_estimate_covariance.type != EstimateWithCovarianceType.EWC_GENERIC:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Current implementation of add_state_block only supports \
                    EstimateWithCovarianceType.EWC_GENERIC.  Attempted to \
                    insert an estimate with covariance of type \
                        {initial_estimate_covariance.type}.',
            )
            return  # Abort adding

        ###########################################################################
        # First, generate the new stateblock descriptor for the states we're adding
        ###########################################################################

        num_new_states = len(initial_estimate_covariance.estimate)

        # Index of the start of the new stateblock is the same as the number of current
        # states due to zero indexing
        num_cur_states = self._strategy.num_states
        new_sb = stateblock_info(
            block=block,
            num_states=num_new_states,
            start_index=num_cur_states,
            stop_index=num_cur_states + num_new_states,
        )

        ################################################
        # Calculate cross covariance matrix if necessary
        ################################################

        cross_cov_mat = None
        if cross_covariances is not None:
            # Initialize cross covariance matrix with zeros (upper diagonal portion)
            cross_cov_mat = np.zeros([num_cur_states, num_new_states])

            # Populate with the cross covariances provided
            for j in range(len(cross_covariances.block_labels)):
                cc_sb_label = cross_covariances.block_labels[j]

                if cc_sb_label in self._sb:
                    # Get stateblock descriptor for cross covariance stateblock
                    cross_sb = self._sb[cc_sb_label]

                    # Populate the part of the cross covariance matrix that corresponds
                    # with this stateblock label

                    # TODO: Is this not populating only the upper right terms?
                    # After looking how the strategy uses this cross covariance variable, it is only the upper right term,
                    # But I do not think that is clear in the add_state_block() description or in comments here either
                    cross_cov_mat[
                        cross_sb.start_index : cross_sb.stop_index,
                        new_sb.start_index : new_sb.stop_index,
                    ] = cross_covariances.cross_covariances[j]

                else:
                    self._mediator.log_message(
                        LoggingLevel.WARN,
                        f'Cross covariance label ({cc_sb_label}) requested in \
                        add_state_block does not exist.  No action taken.',
                    )

        #############################################################################################
        # Finally, add the new states using the fusion strategy and add the new stateblock descriptor
        #############################################################################################

        self._strategy.add_states(
            initial_estimate=initial_estimate_covariance.estimate,
            initial_covariance=initial_estimate_covariance.covariance,
            cross_covariance=cross_cov_mat,
        )

        self._num_states = self._num_states + num_new_states

        self._sb[block.label] = (
            new_sb  # Adds this sb descriptor to the end of the current list of stateblocks
        )

    def get_state_block_estimate(self, block_label: str) -> NDArray[float64] | None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        if block_label not in self._sb:
            return None

        # Get the full state vector and extract the part needed
        full_estimate = self._strategy.estimate
        if full_estimate is None:
            self._mediator.log_message(
                LoggingLevel.ERROR, 'Unable to get estimate from strategy.'
            )
            return None

        this_sb = self._sb[block_label]

        return full_estimate[this_sb.start_index : this_sb.stop_index]

    def get_state_block_covariance(self, block_label: str) -> NDArray[float64] | None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        if block_label not in self._sb:
            return None

        # Get the full state vector and extract the part needed
        full_covariance = self._strategy.covariance
        if full_covariance is None:
            self._mediator.log_message(
                LoggingLevel.ERROR, 'Unable to get covariance from strategy.'
            )
            return None

        this_sb = self._sb[block_label]
        return full_covariance[
            this_sb.start_index : this_sb.stop_index,
            this_sb.start_index : this_sb.stop_index,
        ]

    def get_state_block_cross_covariance(
        self, block_label1: str, block_label2: str
    ) -> NDArray[float64] | None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        if not (block_label1 in self._sb and block_label2 in self._sb):
            return None

        # Get the full state vector and extract the part needed
        full_covariance = self._strategy.covariance
        if full_covariance is None:
            self._mediator.log_message(
                LoggingLevel.ERROR, 'Unable to get covariance from strategy.'
            )
            return None

        sb1 = self._sb[block_label1]
        sb2 = self._sb[block_label2]
        return full_covariance[
            sb1.start_index : sb1.stop_index, sb2.start_index : sb2.stop_index
        ]

    def set_state_block_estimate(
        self, block_label: str, estimate: NDArray[float64]
    ) -> None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        validate_array(estimate, self._mediator, dims=2, cols=1)

        if block_label not in self._sb:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'block label ({block_label}) requested in \
                    set_state_block_estimate does not exist. No action taken.',
            )
            return

        # Get the desired stateblock descriptor
        this_sb = self._sb[block_label]

        if this_sb.num_states != len(estimate):
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'Size mismatch: The number of states in the stateblock with label \
                    ({block_label}) is {this_sb.num_states}, but the provided new \
                    estimate is of length {this_sb.num_states}. No action taken.',
            )
            return

        # Make the change
        self._strategy.set_estimate_slice(estimate, this_sb.start_index)

    def set_state_block_covariance(
        self, block_label: str, covariance: NDArray[float64]
    ) -> None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        if block_label not in self._sb:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'block label ({block_label}) requested in \
                set_state_block_covariance does not exist. No action taken.',
            )
            return
        # Get the desired stateblock descriptor
        this_sb = self._sb[block_label]

        validate_array(
            covariance,
            self._mediator,
            dims=2,
            rows=this_sb.num_states,
            cols=this_sb.num_states,
        )

        # Make the change
        self._strategy.set_covariance_slice(
            new_covariance=covariance,
            first_row=this_sb.start_index,
        )

    def set_state_block_cross_covariance(
        self, block_label1: str, block_label2: str, covariance: NDArray[float64]
    ) -> None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        if block_label1 not in self._sb:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'block_label1 ({block_label1}) requested in \
                set_state_block_cross_covariance does not exist. No action taken.',
            )
            return
        # Get the desired stateblock descriptor
        sb1 = self._sb[block_label1]

        if block_label2 not in self._sb:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'block_label2 ({block_label2}) requested in \
                set_state_block_cross_covariance does not exist. No action taken.',
            )
            return
        # Get the desired stateblock descriptor
        sb2 = self._sb[block_label2]

        validate_array(
            covariance, self._mediator, dims=2, rows=sb1.num_states, cols=sb2.num_states
        )

        # Change the part that is the shape of the covariance matrix
        self._strategy.set_covariance_slice(
            new_covariance=covariance,
            first_row=sb1.start_index,
            first_col=sb2.start_index,
        )

        # Change the transpose of that
        self._strategy.set_covariance_slice(
            new_covariance=covariance.T,
            first_row=sb2.start_index,
            first_col=sb1.start_index,
        )

    def remove_state_block(self, block_label: str) -> None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        if block_label not in self._sb:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'Stateblock to be removed ({block_label}) does not exist.  No action taken.',
            )
            return

        # Remove the states from the fusion engine
        self._strategy.remove_states(
            first_index=self._sb[block_label].start_index,
            count=self._sb[block_label].num_states,
        )

        # Adjust the total number of states
        self._num_states = self._num_states - self._sb[block_label].num_states

        # Remove the stateblock descriptor from the sb dictionary
        del self._sb[block_label]

        # Re-index the stateblock dictionary indexes
        self._re_index_stateblocks()

    @property
    def virtual_state_block_target_labels(self) -> list[str] | None:
        return None

    def has_virtual_state_block(self, vsb_target_label: str) -> bool:
        return False

    def add_virtual_state_block(self, virtual_state_block: VirtualStateBlock) -> None:
        pass

    def remove_virtual_state_block(self, vsb_target_label: str) -> None:
        pass

    @property
    def measurement_processor_labels(self) -> list[str] | None:
        if not self._mp.keys():
            return None
        return list(self._mp.keys())

    def add_measurement_processor(
        self, processor: StandardMeasurementProcessor
    ) -> None:
        if processor.label in self._mp:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'Stateblock to be added ({processor.label}) already exists.  No action taken.',
            )
            return

        self._mp[processor.label] = processor

    def remove_measurement_processor(self, processor_label: str) -> None:
        if processor_label not in self._mp:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'Measurement processor to be removed ({processor_label}) \
                does not exist.  No action taken.',
            )
            return

        del self._mp[processor_label]

    def propagate(self, time: TypeTimestamp) -> None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        if time.elapsed_nsec < self.time.elapsed_nsec:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'Attempted to propagate backwards in time.  propagate_time = {time.elapsed_nsec / 1e9:.9f}, \
                    filter_time = {self.time.elapsed_nsec / 1e9:.9f}s.  No action taken.',
            )
            return

        if time.elapsed_nsec == self.time.elapsed_nsec:
            # No action needed, but we expect this to happen often, so no logging needed.
            return

        if self._num_states == 0:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'Attempted to propagate a filter with zero states. No action taken.',
            )
            return

        # Generate the large matrices to be populated
        big_Phi = np.zeros([self._num_states, self._num_states])
        big_Qd = np.zeros([self._num_states, self._num_states])

        # loop through the stateblocks and generate the dynamics model and save off
        dynamics_model: dict[str, StandardDynamicsModel] = {}
        for label, sb_data in self._sb.items():
            ewc = self.generate_x_and_p([label])
            if ewc is None:
                self._mediator.log_message(
                    LoggingLevel.ERROR,
                    'Unable to generate estimate with covariance during propagate.',
                )
                return
            dynamics = self._sb[label].block.generate_dynamics(
                x_and_p=ewc, time_from=self.time, time_to=time
            )
            if dynamics is None:
                self._mediator.log_message(
                    LoggingLevel.ERROR,
                    'Unable to generate dynamics model during propagate.',
                )
                return
            dynamics_model[label] = dynamics

            # Populate the big_Phi portion
            big_Phi[
                sb_data.start_index : sb_data.stop_index,
                sb_data.start_index : sb_data.stop_index,
            ] = dynamics_model[label].Phi
            big_Qd[
                sb_data.start_index : sb_data.stop_index,
                sb_data.start_index : sb_data.stop_index,
            ] = dynamics_model[label].Qd

        # Now, make the full propagation function big_g(x) as a combination of all of the small
        # propagation functions g(x)
        def big_g(x_in: NDArray[float64]) -> NDArray[float64]:
            x_out = np.zeros(x_in.shape, dtype=float64)

            # Iterate through all of the stateblocks and propagate the states just for
            # that stateblock
            for label, sb_data in self._sb.items():
                x_out[sb_data.start_index : sb_data.stop_index] = dynamics_model[
                    label
                ].g(x_in[sb_data.start_index : sb_data.stop_index])

            return x_out

        # Assemble the dynamics model for all of the states together
        big_dynamics_model = StandardDynamicsModel(g=big_g, Phi=big_Phi, Qd=big_Qd)

        # Propagate using the fusion strategy
        self._strategy.propagate(big_dynamics_model)
        self.time = time

    def update(self, processor_label: str, message: Message) -> None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        # Verify processor exists
        if processor_label not in self._mp:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Attempted process measurement, but measurement processor \
                      ({processor_label}) does not exist. No action taken.',
            )
            return

        # Call propagate, which handles the error handling and figures out if
        # propagation is needed
        assert hasattr(message.wrapped_message, 'time_of_validity')
        self.propagate(message.wrapped_message.time_of_validity)

        # Get the measurement model that only applies to just the states identified by the
        # measurement processor's state_block_labels
        x_and_p = self.generate_x_and_p(
            block_labels=self._mp[processor_label].state_block_labels
        )
        if x_and_p is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'Unable to generate estimate with covariance during update.',
            )
            return

        measurement_model = self._mp[processor_label].generate_model(
            message=message, x_and_p=x_and_p
        )
        if measurement_model is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'Unable to generate measurement model during update.',
            )
            return

        # Make full size H matrix
        big_H = np.zeros([measurement_model.H.shape[0], self._num_states])

        # Populate the full size H matrix from the values in the measurement processors's H
        # Also calculate the total number of states included in the measurement processor's
        # state_block_labels.
        mp_num_states = 0
        for label in self._mp[processor_label].state_block_labels:
            stop_index = mp_num_states + self._sb[label].num_states
            big_H[:, self._sb[label].start_index : self._sb[label].stop_index] = (
                measurement_model.H[:, mp_num_states:stop_index]
            )
            mp_num_states = stop_index

        # Make the h(x) function that operates on the full x rather than just the
        # x specified by the measurement processor's state_block_labels
        def big_h(full_x: NDArray[float64]) -> NDArray[float64]:
            # Make the x matrix that the measurement processor h(x) is expecting
            x_mp = np.zeros([mp_num_states, 1], dtype=float64)
            start_index = 0  # start index of the next stateblock
            for label in self._mp[processor_label].state_block_labels:
                # Pull out the relevant portions of the full x matrix and insert
                # them into the x_mp
                x_mp[start_index : start_index + self._sb[label].num_states] = full_x[
                    self._sb[label].start_index : self._sb[label].stop_index
                ]
                start_index += self._sb[label].num_states

            # Calculate and return the h(x) output
            return measurement_model.h(x_mp)

        # From the above, generate the measurement model that operates on all of the states
        big_measurement_model = StandardMeasurementModel(
            z=measurement_model.z, h=big_h, H=big_H, R=measurement_model.R
        )

        # Use the fusion strategy to update the states
        self._strategy.update(measurement_model=big_measurement_model)

    def peek_ahead(
        self, time: TypeTimestamp, block_labels: list[str]
    ) -> EstimateWithCovariance | None:
        # Check that time is not before filter time
        if time.elapsed_nsec < self.time.elapsed_nsec:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'Peek ahead time ({time.elapsed_nsec / 1e9:.9f}s) is before filter time\
                      ({self.time.elapsed_nsec / 1e9:.9f}s).',
            )
            return None

        # Make sure there is at least one block_label
        if len(block_labels) == 0:
            self._mediator.log_message(
                LoggingLevel.WARN, f'No block labels for peek_ahead().'
            )
            return None

        # Verify that all of the block labels correspond to a state block that has been
        # added to the fusion engine
        for label in block_labels:
            if label not in self._sb:
                self._mediator.log_message(
                    LoggingLevel.WARN,
                    f'In peek_ahead(), the state block label "{label}" does not match any \
                      stateblock loaded into the fusion engine.',
                )
                return None

        # Make a copy of the the fusion engine (which includes the strategy)
        peekahead_fusion = copy.deepcopy(self)

        # Propagate
        peekahead_fusion.propagate(time=time)

        # Pull out the desired states
        return peekahead_fusion.generate_x_and_p(block_labels=block_labels)

    def generate_x_and_p(
        self, block_labels: list[str]
    ) -> EstimateWithCovariance | None:
        assert self._strategy is not None, 'FusionStrategy has not been set'
        # Make sure there is at least one block_label
        if len(block_labels) == 0:
            self._mediator.log_message(
                LoggingLevel.WARN, f'No block labels for generate_x_and_p().'
            )
            return None

        # Verify that all of the block labels correspond to a state block that has been
        # added to the fusion engine
        for label in block_labels:
            if label not in self._sb:
                self._mediator.log_message(
                    LoggingLevel.WARN,
                    f'In generate_x_and_p(), the state block label "{label}" does not match any \
                      stateblock loaded into the fusion engine.',
                )
                return None

        # make an array of the indices that we want to keep
        i_keep = np.zeros([0], dtype=int)
        for label in block_labels:
            i_to_add = np.arange(
                self._sb[label].start_index, self._sb[label].stop_index
            )
            i_keep = np.append(i_keep, i_to_add)

        # Retrieve the full estimate (x) and covariance (P)
        x = self._strategy.estimate
        P = self._strategy.covariance
        if x is None or P is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'Unable to generate estimate and covariance from current strategy.',
            )
            return None

        # Use the i_keep index to extract and return the desired portions of the large x and P
        return EstimateWithCovariance(
            type=EstimateWithCovarianceType.EWC_GENERIC,
            estimate=x[i_keep],
            covariance=P[i_keep, :][:, i_keep],
        )

    def give_state_block_aux_data(self, block_label: str, aux: list[Message]) -> None:
        if block_label not in self._sb:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'State block ({block_label}) identified in give_state_block_aux_data() \
                    does not exist .',
            )
            return

        self._sb[block_label].block.receive_aux_data(aux)

    def give_measurement_processor_aux_data(
        self, processor_label: str, aux: list[Message]
    ) -> None:
        if processor_label not in self._mp:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'State block ({processor_label}) identified in \
                    give_measurement_processor_aux_data() does not exist .',
            )
            return

        self._mp[processor_label].receive_aux_data(aux)

    def give_virtual_state_block_aux_data(
        self, target_label: str, aux: list[Message]
    ) -> None:
        pass


class StandardFusionPlugin(FusionPlugin):
    """
    A fusion plugin that provides instances of fusion engines.
    """

    _mediator: Mediator

    def __init__(self, identifier: str) -> None:
        """
        A Fusion Plugin

        Args:
            identifier (str): The plugin identifier passed to the
                :meth:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is not None:
            self._mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def is_fusion_type_supported(self, fusion_type: type[FusionEngineType]) -> bool:
        return fusion_type == api.StandardFusionEngine

    def new_fusion_engine(
        self, fusion_type: type[FusionEngineType]
    ) -> FusionEngineType | None:
        if self.is_fusion_type_supported(fusion_type):
            return StandardFusionEngine(mediator=self._mediator)
        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Fusion strategy type {fusion_type.__name__} not currently supported. '
            + 'Make sure to call FusionPlugin.is_fusion_type_supported before '
            + 'requesting a new fusion strategy.',
        )
        return None
