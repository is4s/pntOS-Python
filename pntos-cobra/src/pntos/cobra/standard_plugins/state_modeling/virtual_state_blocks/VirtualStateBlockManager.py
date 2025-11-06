from aspn23 import TypeTimestamp
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
    LoggingLevel,
    Mediator,
    Message,
    VirtualStateBlock,
)


class Node:
    """
    A container class for a :class:`pntos.api.VirtualStateBlock` which stores information
    about a VSB as it relates to its relationship to other VSB's.

    Attributes:
        id (str): The unique identifier of the `Node`. If ``block`` contains a VSB,
            this value should match its ``target``.
        parent (str | None): The identifier of the parent of this `Node`. If ``block``
            contains a VSB, this value should match its ``source``. Otherwise the value
            should be `None`  and the `Node` instance is considered to be a root node.
        children (set[str]): The set of `Node.id`s that use this `Node` as a ``parent``.
            If the set is empty, this instance is assumed to be a leaf node.
        block (VirtualStateBlock | None): The :class:`pntos.api.VirtualStateBlock` this
            `Node` instance contains. Allowed to be `None` so root nodes can exist.
    """

    id: str
    parent: str | None
    children: set[str]
    block: VirtualStateBlock | None

    def __init__(
        self, id: str, parent: str | None = None, block: VirtualStateBlock | None = None
    ) -> None:
        """
        Args:
            id (str): The unique identifier of the `Node`.
            parent (str | None, optional): The identifier of the parent of this `Node`.
            block (VirtualStateBlock | None, optional): The :class:`pntos.api.VirtualStateBlock`
                to contain in this instance.
        """
        self.id = id
        self.children = set()
        self.parent = parent
        self.block = block

    def add_child(self, child: str) -> None:
        """
        Adds ``child`` to ``children`` attribute.

        Args:
            child (str): The child identifier to add.
        """
        self.children.add(child)


class VirtualStateBlockManager:
    """
    A utility class that manages :class:`pntos.api.VirtualStateBlock`'s for a :class:`pntos.api.StandardFusionEngine` instance.
    This class will create n-ary trees by instantiating `Node`s to build and maintain the relationship between a
    given VSB and another. The roots of these trees represent 'real' state blocks. If a `Node` has no parent, it is
    assumed to be a root node but there is no way the manager can know if said `Node` is a real block or if it's just
    a virtual state block that has yet to be added.
    """

    mediator: Mediator
    _node_map: dict[str, Node]
    _path_cache: dict[str, list[str]]
    _root_map: dict[str, str]
    _roots: set[str]

    def __init__(self, mediator: Mediator) -> None:
        """
        Args:
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
        """
        self.mediator = mediator
        self._node_map = {}
        self._path_cache = {}
        self._root_map = {}
        self._roots = set()

    def add_virtual_state_block(self, trans: VirtualStateBlock) -> None:
        """
        Registers a :class:`pntos.api.VirtualStateBlock` into the manager. If the VSB's ``source`` matches its ``target``
        or the ``target`` already exists in the manager, a warning will be logged and the VSB won't be added. If the
        ``source`` doesn't exist, a new `Node` will be created and it will be treated as a root node. As VSBs are added,
        this function will adjust the relationships between VSBs accordingly.

        Args:
            trans (VirtualStateBlock): The :class:`pntos.api.VirtualStateBlock` to be added.
        """
        if trans.source == trans.target:
            self.mediator.log_message(
                LoggingLevel.WARN,
                'Source and target tags should not be the same. Virtual state block will not be added.',
            )
            return
        if trans.target in self._node_map:
            targetNode = self._node_map[trans.target]
            if targetNode.parent is not None:
                self.mediator.log_message(
                    LoggingLevel.WARN,
                    'Duplicate virtual state block. Target matches an existing block stored in the VirtualStateBlockManager. Virtual state block will not be added.',
                )
                return
            targetNode.parent = trans.source
            targetNode.block = trans
            if trans.target in self._roots:
                self._roots.remove(trans.target)
        else:
            targetNode = Node(trans.target, trans.source, trans)
            self._node_map[targetNode.id] = targetNode

        if trans.source in self._node_map:
            sourceNode = self._node_map[trans.source]
        else:
            sourceNode = Node(trans.source)
            self._node_map[sourceNode.id] = sourceNode
        sourceNode.add_child(trans.target)
        if sourceNode.parent is None:
            self._roots.add(sourceNode.id)

    def convert(
        self, orig: EstimateWithCovariance, start: str, target: str, time: TypeTimestamp
    ) -> EstimateWithCovariance | None:
        """
        Converts an :class:`pntos.api.EstimateWithCovariance` to a `target` representation if the conversion is possible.

        Args:
            orig (EstimateWithCovariance): The estimate and covariance in the starting format.
            start (str): The label of the starting format.
            target (str): The label that refers to the ending format for the estimate and covariance.
            time (TypeTimestamp): The time of validity for the estimate and covariance.

        Returns:
            :class:`pntos.api.EstimateWithCovariance` if conversion is possible; otherwise returns `None`.
        """
        path = self._get_path(start, target)
        if path is None:
            return None
        ewc = orig
        for node_id in path:
            node = self._node_map[node_id]
            if node.block is None:
                continue
            ewc = node.block.convert(ewc, time)
        return ewc

    def convert_estimate(
        self, orig: NDArray[float64], start: str, target: str, time: TypeTimestamp
    ) -> NDArray[float64] | None:
        """
        Converts an estimate to a `target` representation if the conversion is possible.

        Args:
            orig (NDArray[float64]): The estimate in the starting format.
            start (str): The label of the starting format.
            target (str): The label that refers to the ending format for the estimate.
            time (TypeTimestamp): The time of validity for the estimate.

        Returns:
            NDArray[float64] if conversion is possible; otherwise returns `None`.
        """
        path = self._get_path(start, target)
        if path is None:
            return None
        est = orig
        for node_id in path:
            node = self._node_map[node_id]
            if node.block is None:
                continue
            est = node.block.convert_estimate(est, time)
        return est

    def get_start_block_label(self, target: str) -> tuple[bool, str]:
        """
        Gets the state block label of the starting node which is assumed to be represent a 'real' state block.

        Args:
            target (str): The :class:`pntos.api.VirtualStateBlock` unique identifier to get the starting label for.

        Returns:
            A `tuple[bool, str]`. The boolean will be `True` if there is a valid path back to an assumed 'real' state block.
                The string will be the unique label of that starting state block. Otherwise the boolean will be `False`
                and the string will be empty.
        """
        if target not in self._node_map:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Block {target} has not been added to the VirtualStateBlockManager. No valid starting label exists.',
            )
            return (False, '')
        if target in self._root_map:
            root = self._node_map[self._root_map[target]]
            if root.parent is None:
                return (True, self._root_map[target])
        node = self._node_map[target]
        while node.parent is not None:
            node = self._node_map[node.parent]
        self._root_map[target] = node.id
        return (True, node.id)

    def get_virtual_state_block_labels(self) -> list[str] | None:
        """
        Returns the list of virtual state block labels being tracked by the manager.
        Returns `None` if that list is empty.
        """
        out = list(self._node_map.keys() - self._roots)
        if len(out) == 0:
            return None
        return out

    def give_virtual_state_block_aux_data(
        self, target: str, aux: list[Message | None]
    ) -> None:
        """
        Provides the :class:`pntos.api.VirtualStateBlock` with target label ``target`` with the data in ``aux``.

        Args:
            target (str): The unique label that identifies what :class:`pntos.api.VirtualStateBlock`
            aux (list[Message | None]): The auxiliary data to give to the :class:`pntos.api.VirtualStateBlock`
        """
        if target not in self._node_map:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Block {target} has not been added to or has already been removed from the VirtualStateBlockManager. Cannot give aux data.',
            )
            return
        node = self._node_map[target]
        if node.block is None:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Target {target} does not have a VirtualStateBlock associated with it. It likely has not been added to the manager yet.',
            )
            return
        node.block.receive_aux_data(aux)

    def jacobian(
        self, orig: NDArray[float64], start: str, target: str, time: TypeTimestamp
    ) -> NDArray[float64] | None:
        """
        Obtains the jacobian of an input estimate in the `target` representation if possible.

        Args:
            orig (NDArray[float64]): The estimate in the starting format.
            start (str): The label of the starting format.
            target (str): The label that refers to the ending format for the jacobian.
            time (TypeTimestamp): The time of validity for the input estimate.

        Returns:
            NDArray[float64] if conversion is possible; otherwise returns `None`.
        """
        path = self._get_path(start, target)
        if path is None:
            return None
        est = orig
        for node_id in path:
            node = self._node_map[node_id]
            if node.block is None:
                continue
            est = node.block.jacobian(est, time)
        return est

    def remove_virtual_state_block(self, target: str) -> None:
        """
        Removes the :class:`pntos.api.VirtualStateBlock` matching ``target`` from the manager.
        If this leaves an orphaned branch of nodes it will prune the branch removing all VSB's in that branch as well.

        Args:
            target (str): The unique identifier of the :class:`pntos.api.VirtualStateBlock` to remove
        """
        if target not in self._node_map:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Block {target} has not been added to or has already been removed from the VirtualStateBlockManager. Cannot remove.',
            )
            return
        node = self._node_map.pop(target)
        self.mediator.log_message(
            LoggingLevel.INFO, f'Removed {target} from the VirtualStateBlockManager.'
        )
        if node.id in self._path_cache:
            self._path_cache.pop(target)
        if node.id in self._root_map:
            self._root_map.pop(target)
        if node.parent in self._node_map:
            parent = self._node_map[node.parent]
            parent.children.remove(node.id)
        for child in node.children:
            self.remove_virtual_state_block(child)

    def _get_path(self, start: str, target: str) -> list[str] | None:
        """
        Gets the path between ``start`` and ``target`` and caches it if the path exists.

        Args:
            start (str): The label of the node the path should start at.
            target (str): The label of the node the path should end at.

        Returns:
            A `list[str]` if a path exists, otherwise returns `None`.
        """
        if target not in self._node_map:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Block {target} is not being tracked by the VirtualStateBlockManager.',
            )
            return None
        if target in self._path_cache:
            path = self._path_cache[target]
            if path[0] == start:
                return path
        out = []
        node = self._node_map[target]
        while node.id != start:
            if node.parent is None:
                self.mediator.log_message(
                    LoggingLevel.WARN,
                    f'No path exists from source block {start} to target block {target}.',
                )
                return None
            out.append(node.id)
            node = self._node_map[node.parent]

        out.append(node.id)
        out.reverse()
        self._path_cache[target] = out
        return out
