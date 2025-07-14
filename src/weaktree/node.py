from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from enum import auto, Enum
from typing import Generic, TypeVar, TYPE_CHECKING
from weakref import ref

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import ClassVar


T = TypeVar("T")
IterT = TypeVar("IterT")


class CleanupMode(Enum):
    DEFAULT = auto()
    PRUNE = auto()
    REPARENT = auto()
    NO_CLEANUP = auto()


def _idle(node: WeakTreeNode[T]):
    # Intentionally do nothing.
    pass


def _prune(node: WeakTreeNode[T]):
    if node.trunk:
        node.trunk._branches.discard(node)
    # This will allow the branch to unwind and be gc'd unless the user has another
    # reference to any of the nodes somehwere.
    node._branches.clear()


def _reparent(node: WeakTreeNode[T]):
    if node.trunk:
        node.trunk._branches.discard(node)
    for subnode in node._branches.copy():
        subnode.trunk = node.trunk


def _get_cleanup_method(
    node: WeakTreeNode[T],
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


class WeakTreeNode(Generic[T]):
    """
    An object that allows for the formation of data trees that don't form strong
    references to its data. WeakTreeNodes can be configured to control the result when
    the data in the reference dies.
    """

    # These are here to allow use without needing to import the enum
    DEFAULT: ClassVar[CleanupMode] = CleanupMode.DEFAULT
    PRUNE: ClassVar[CleanupMode] = CleanupMode.PRUNE
    REPARENT: ClassVar[CleanupMode] = CleanupMode.REPARENT
    NO_CLEANUP: ClassVar[CleanupMode] = CleanupMode.NO_CLEANUP

    def __init__(
        self,
        data: T,
        trunk: WeakTreeNode | None = None,
        cleanup_mode: CleanupMode = DEFAULT,
        callback: Callable | None = None,
    ) -> None:
        """
        Create a new node for a weakly-referencing tree.

        :param data: The data to be stored by the new WeakTreeNode
        :param trunk: The previous node in the tree for the new node, defaults to None,
            which indicates a top-level node.
        :param cleanup_mode: An enum indicating how the tree should cleanup after
            itself when the data reference expires, defaults to DEFAULT, which calls
            upon the trunk node, or prune if the root is also DEFAULT.
        :param callback: An optional additional callback function, called when the
            data reference expires. Defaults to None.
        """

        # Create a cleanup callback for our data reference
        def _remove(wr: ref, selfref=ref(self)):
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

        self._trunk: ref[WeakTreeNode[T]] | None = None
        self.trunk = trunk

        self._branches: set[WeakTreeNode[T]] = set()

        self._cleanup_mode: CleanupMode = cleanup_mode

    @property
    def branches(self) -> set[WeakTreeNode[T]]:
        """
        A set of nodes that descend from the current node.
        """
        return self._branches

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
    def trunk(self, node: WeakTreeNode | None):
        if self.trunk:
            self.trunk._branches.discard(self)
        if node:
            self._trunk = ref(node)
            node._branches.add(self)
        else:
            self._trunk = None

    @property
    def data(self) -> T | None:
        """
        The value stored by the node.
        """
        # Dereference our data so the real object can be used.
        return self._data()

    def add_branch(
        self,
        data: T,
        cleanup_mode: CleanupMode = DEFAULT,
        callback: Callable | None = None,
    ) -> WeakTreeNode[T]:
        """
        Creates a new node as a child of the current node, with a weak reference to the
        passed value.

        Returns the new isntance, so this can be chained without intermediate variables.

        :param data: The data to be stored by the new WeakTreeNode
        :param cleanup_mode: An enum indicating how the tree should cleanup after
            itself when the data reference expires, defaults to DEFAULT, which calls
            upon the trunk node, or prune if the root is also DEFAULT.
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


class TreeIterable(ABC, Generic[IterT]):
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

        Order is not guaranteed.
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

        Order is not guaranteed.
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


class NodeIterable(TreeIterable[WeakTreeNode]):
    """
    Variant of TreeIterator that provides the nodes of the tree themselves when
    iterated over.
    """

    def _get_iter_output(self, node: WeakTreeNode[T]) -> WeakTreeNode[T]:
        return node


class ValueIterable(TreeIterable[T | None]):
    """
    Variant of TreeIterator that provides the values of the nodes of the tree when
    iterated over.
    """

    def _get_iter_output(self, node: WeakTreeNode[T]) -> T | None:
        return node.data


class ItemsIterable(TreeIterable[tuple[WeakTreeNode[T], T | None]]):
    """
    Variant of TreeIterable that provides pairs of nodes with their values when
    iterated over.
    """

    def _get_iter_output(self, node: WeakTreeNode) -> tuple[WeakTreeNode, T | None]:
        return node, node.data
