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


def _prune(node: WeakTreeNode[T]):
    if node.root:
        node.root._branches.discard(node)
    node._branches.clear()


def _reparent(node: WeakTreeNode[T]):
    if node.root:
        node.root._branches.discard(node)
    for subnode in node._branches.copy():
        subnode.root = node.root


def _idle(node: WeakTreeNode[T]):
    # Intentionally do nothing.
    pass


def _get_cleanup_method(
    node: WeakTreeNode[T], cleanup_method: WeakTreeNode.CleanupMode
) -> Callable:
    match cleanup_method:
        case WeakTreeNode.PRUNE:
            return _prune
        case WeakTreeNode.REPARENT:
            return _reparent
        case WeakTreeNode.NO_CLEANUP:
            return _idle
        case _:
            root = node.root
            if not root:
                # If we're top level and ask for default, default to pruning.
                return _prune
            # Otherwise, find the root's cleanup method.
            return _get_cleanup_method(root, root._cleanup_mode)


class WeakTreeNode(Generic[T]):

    class CleanupMode(Enum):
        DEFAULT = auto()
        PRUNE = auto()
        REPARENT = auto()
        NO_CLEANUP = auto()

    DEFAULT: ClassVar[CleanupMode] = CleanupMode.DEFAULT
    PRUNE: ClassVar[CleanupMode] = CleanupMode.PRUNE
    REPARENT: ClassVar[CleanupMode] = CleanupMode.REPARENT
    NO_CLEANUP: ClassVar[CleanupMode] = CleanupMode.NO_CLEANUP

    def __init__(
        self,
        data: T,
        root: WeakTreeNode | None = None,
        callback: Callable | None = None,
        cleanup_mode: CleanupMode = DEFAULT,
    ) -> None:
        def _remove(wr: ref, selfref=ref(self)):
            self = selfref()
            if callback:
                callback(wr)
            if self:
                _get_cleanup_method(self, self._cleanup_mode)(self)

        self._data = ref(data, _remove)
        self._root: ref[WeakTreeNode[T]] | None = None
        self.root = root
        self._branches: set[WeakTreeNode[T]] = set()
        self._cleanup_mode: WeakTreeNode.CleanupMode = cleanup_mode

    @property
    def branches(self) -> set[WeakTreeNode[T]]:
        return self._branches

    @property
    def root(self) -> WeakTreeNode[T] | None:
        if self._root:
            return self._root()
        return None

    @root.setter
    def root(self, node: WeakTreeNode | None):
        if self.root:
            self.root._branches.discard(self)
        if node:
            self._root = ref(node)
            node._branches.add(self)
        else:
            self._root = None

    @property
    def data(self) -> T | None:
        # Dereference our data so the real object can be used.
        return self._data()

    def add_branch(
        self,
        data: T,
        callback: Callable | None = None,
        cleanup_mode: CleanupMode = DEFAULT,
    ) -> WeakTreeNode[T]:
        """
        Creates a new node as a child of the current node, with a weak reference to the
        passed value.

        Returns the new isntance, so this can be chained without intermediate variables.

        :param data: The data to be stored by the new WeakTreeNode
        :param callback: An optional additional callback function, called when the
            data reference expires. Defaults to None.
        :param cleanup_mode: An enum indicating how the tree should cleanup after
            itself when the data reference expires, defaults to DEFAULT.
        :return: The newly created node.
        """
        node = WeakTreeNode(data, self, callback, cleanup_mode)
        return node

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

    def to_root(self) -> Iterator[WeakTreeNode[T]]:
        """
        Provides a generator that traces the tree back to the furthest root.

        :yield: The root node of the previous node.
        """

        yield from NodeIterable(self).to_root()

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
        return f"WeakTreeNode({self.data})"


class TreeIterable(ABC, Generic[IterT]):

    def __init__(self, starting_node: WeakTreeNode[T]) -> None:
        self._root_node = starting_node

    @abstractmethod
    def _get_iter_output(self, node: WeakTreeNode) -> IterT:
        pass

    def breadth(self) -> Iterator[IterT]:
        """
        Provides a generator that performs a breadth-first traversal of the tree
        starting at the root node of the iterable.

        Order is not guaranteed.
        """
        queue: deque[WeakTreeNode] = deque([self._root_node])
        while queue:
            node = queue.popleft()
            yield self._get_iter_output(node)

            queue.extend(node.branches)

    def depth(self) -> Iterator[IterT]:
        """
        Provides a generator that performs a depth-first traversal of the tree,
        starting from the root node of the iterable.

        Order is not guaranteed.
        """
        stack: list[WeakTreeNode] = [self._root_node]
        while stack:
            node = stack.pop()
            yield self._get_iter_output(node)

            stack.extend(node.branches)

    def to_root(self) -> Iterator[IterT]:
        """
        Provides a generator that traces the tree back to the furthest root.
        """
        node: WeakTreeNode | None = self._root_node
        while node:
            yield self._get_iter_output(node)

            node = node.root

    def __iter__(self) -> Iterator[IterT]:
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
