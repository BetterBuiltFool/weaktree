from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from enum import auto, Enum
from typing import TYPE_CHECKING
from weakref import ref

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import Any, ClassVar


class CleanupMode(Enum):
    DEFAULT = auto()
    PRUNE = auto()
    REPARENT = auto()
    NO_CLEANUP = auto()


def _idle(node: WeakTreeNode[Any]) -> None:
    # Intentionally do nothing.
    pass


def _prune(node: WeakTreeNode[Any]) -> None:
    if node.trunk:
        node.trunk._branches.pop(node, None)
    # This will allow the branch to unwind and be gc'd unless the user has another
    # reference to any of the nodes somehwere.
    node._branches.clear()


def _reparent(node: WeakTreeNode[Any]) -> None:
    if node.trunk:
        node.trunk._branches.pop(node, None)
    for subnode in node._branches.copy():
        subnode.trunk = node.trunk


def _get_cleanup_method(
    node: WeakTreeNode[Any],
    cleanup_mode: CleanupMode,
) -> Callable[[WeakTreeNode], None]:

    match cleanup_mode:
        case CleanupMode.PRUNE:
            return _prune
        case CleanupMode.REPARENT:
            return _reparent
        case CleanupMode.NO_CLEANUP:
            return _idle
        case _:
            trunk = node.trunk
            if not trunk:
                # If we're top level and ask for default, default to pruning.
                return _prune
            # Otherwise, find the trunk's cleanup method.
            return _get_cleanup_method(trunk, trunk._cleanup_mode)


class WeakTreeNode[T]:
    """
    Models data trees that don't form strong references to their data. WeakTreeNodes
    can be configured to control their behavior when the data in the reference dies,
    allowing the tree to be cleaned up by pruning the node's branches, moving them to
    the node's trunk, or leaving the empty node alone.
    """

    # These are here to allow use without the user needing to import the enum
    DEFAULT: ClassVar[CleanupMode] = CleanupMode.DEFAULT
    """
    When the node cleans up, refer to the trunk's cleanup mode, or else prune if the
    root is DEFAULT.
    """
    PRUNE: ClassVar[CleanupMode] = CleanupMode.PRUNE
    """
    Trim the branches of the node when its data expires.
    """
    REPARENT: ClassVar[CleanupMode] = CleanupMode.REPARENT
    """
    Move the branches to the node's trunk.
    """
    NO_CLEANUP: ClassVar[CleanupMode] = CleanupMode.NO_CLEANUP
    """
    Leave the node alone when its data expires.
    """

    def __init__(
        self,
        data: T,
        trunk: WeakTreeNode | None = None,
        cleanup_mode: CleanupMode = DEFAULT,
        callback: Callable[[ref], None] | None = None,
    ) -> None:
        """
        Create a new node for a weakly-referencing tree.

        :param data: The data to be stored by the new WeakTreeNode
        :param trunk: The previous node in the tree for the new node, defaults to None,
            which indicates a top-level node.
        :param cleanup_mode: An enum indicating how the tree should cleanup after
            itself when the data reference expires, defaults to DEFAULT
        :param callback: An optional additional callback function, called when the
            data reference expires. Defaults to None.
        """

        self._callback = callback

        self._data: ref[T]
        self.data = data

        self._trunk: ref[WeakTreeNode[T]] | None = None
        self.trunk = trunk

        self._branches: dict[WeakTreeNode[T], None] = {}

        self._cleanup_mode: CleanupMode = cleanup_mode

    @property
    def branches(self) -> set[WeakTreeNode[T]]:
        """
        A set of nodes that descend from the current node.
        """
        return set(self._branches.keys())

    @property
    def cleanup_mode(self) -> CleanupMode:
        return self._cleanup_mode

    @cleanup_mode.setter
    def cleanup_mode(self, mode: CleanupMode) -> None:
        self._cleanup_mode = mode

    @property
    def data(self) -> T | None:
        """
        The value stored by the node.
        """
        # Dereference our data so the real object can be used.
        return self._data()

    @data.setter
    def data(self, data: T) -> None:

        # Create a cleanup callback for our data reference
        def _remove(wr: ref, selfref=ref(self), callback=self._callback) -> None:
            # selfref gives us access to the instance within the callback without
            # keeping it alive.
            self = selfref()
            # It's fine to keep our user callback alive, though, it shouldn't be bound
            # to anything.
            if callback:
                callback(wr)
            if self:
                _get_cleanup_method(self, self._cleanup_mode)(self)

        self._data = ref(data, _remove)

    @property
    def trunk(self) -> WeakTreeNode[T] | None:
        """
        A node that sits higher in the tree than the current node.
        If None, the current node is considered top-level.
        """
        if self._trunk:
            return self._trunk()
        return None

    @trunk.setter
    def trunk(self, node: WeakTreeNode | None) -> None:
        if self.trunk:
            self.trunk._branches.pop(self)
        if node:
            self._trunk = ref(node)
            node._branches[self] = None
        else:
            self._trunk = None

    def add_branch(
        self,
        data: T,
        cleanup_mode: CleanupMode = DEFAULT,
        callback: Callable[[ref], None] | None = None,
    ) -> WeakTreeNode[T]:
        """
        Creates a new node as a child of the current node, with a weak reference to the
        passed value.

        Returns the new instance, so this can be chained without intermediate variables.

        :param data: The data to be stored by the new WeakTreeNode
        :param cleanup_mode: An enum indicating how the tree should cleanup after
            itself when the data reference expires, defaults to DEFAULT
        :param callback: An optional additional callback function, called when the
            data reference expires. Defaults to None.
        :return: The newly created node.
        """
        return WeakTreeNode(data, self, cleanup_mode, callback)

    def breadth(self) -> Iterator[WeakTreeNode[T]]:
        """
        Provides a generator that performs a breadth-first traversal of the tree
        starting at the current node.

        :yield: The next node in the tree, breadth-first.
        """
        # The .breadth() isn't strictly needed, but could cause an issue if we decide
        # to change what the default iteration mode is.
        yield from NodeIterable(self).breadth()

    def depth(self) -> Iterator[WeakTreeNode[T]]:
        """
        Provides a generator that performs a depth-first traversal of the tree
        starting at the current node.

        :yield: The next node in the tree, depth-first.
        """
        yield from NodeIterable(self).depth()

    def towards_root(self) -> Iterator[WeakTreeNode[T]]:
        """
        Provides a generator that traces the tree back to the furthest trunk.

        :yield: The trunk node of the previous node.
        """

        yield from NodeIterable(self).towards_root()

    def nodes(self) -> NodeIterable:
        """
        Returns an iterable that allows iteration over the nodes of the tree, starting
        from the calling node.
        """
        return NodeIterable(self)

    def values(self) -> ValueIterable[T]:
        """
        Returns an iterable that allows iteration over the values of the tree, starting
        from the calling node.
        """
        return ValueIterable[T](self)

    def items(self) -> ItemsIterable[T]:
        """
        Returns an iterable that allows iteration over both the nodes and values of the
        tree, starting from the calling node.
        """
        return ItemsIterable[T](self)

    def __iter__(self) -> Iterator[WeakTreeNode[T]]:
        """
        Default iteration method, in this case, breadth-first.

        :yield: The next node in the tree, breadth-first.
        """
        yield from self.breadth()

    def __repr__(self) -> str:
        return f"WeakTreeNode({self.data}, {self.trunk})"


class TreeIterable[IterT, T](ABC):
    """
    Generic base class for iterating over trees.
    """

    def __init__(self, starting_node: WeakTreeNode[T]) -> None:
        self._trunk_node = starting_node

    @abstractmethod
    def _get_iter_output(self, node: WeakTreeNode) -> IterT:
        pass

    def breadth(self) -> Iterator[IterT]:
        """
        Provides a generator that performs a breadth-first traversal of the tree
        starting at the trunk node of the iterable.
        """
        queue: deque[WeakTreeNode] = deque([self._trunk_node])
        while queue:
            node = queue.popleft()
            yield self._get_iter_output(node)

            queue.extend(node.branches)

    def depth(self) -> Iterator[IterT]:
        """
        Provides a generator that performs a depth-first traversal of the tree,
        starting from the trunk node of the iterable.
        """
        stack: list[WeakTreeNode] = [self._trunk_node]
        while stack:
            node = stack.pop()
            yield self._get_iter_output(node)

            stack.extend(node.branches)

    def towards_root(self) -> Iterator[IterT]:
        """
        Provides a generator that traces the tree back to the furthest trunk.
        """
        node: WeakTreeNode | None = self._trunk_node
        while node:
            yield self._get_iter_output(node)

            node = node.trunk

    def __iter__(self) -> Iterator[IterT]:
        """
        Provides a default iterator for the node. By default, iterates by breadth-first.
        """
        yield from self.breadth()


class NodeIterable[T](TreeIterable[WeakTreeNode, T]):
    """
    Variant of TreeIterator that provides the nodes of the tree themselves when
    iterated over.
    """

    def _get_iter_output(self, node: WeakTreeNode[T]) -> WeakTreeNode[T]:
        return node


class ValueIterable[T](TreeIterable[T | None, T]):
    """
    Variant of TreeIterator that provides the values of the nodes of the tree when
    iterated over.
    """

    def _get_iter_output(self, node: WeakTreeNode[T]) -> T | None:
        return node.data


class ItemsIterable[T](TreeIterable[tuple[WeakTreeNode[T], T | None], T]):
    """
    Variant of TreeIterable that provides pairs of nodes with their values when
    iterated over.
    """

    def _get_iter_output(self, node: WeakTreeNode) -> tuple[WeakTreeNode, T | None]:
        return node, node.data
