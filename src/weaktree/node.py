from __future__ import annotations

from collections import deque
from collections.abc import Callable, Generator
from typing import ClassVar, Generic, TypeVar
from weakref import ref

T = TypeVar("T")


class WeakTreeNode(Generic[T]):
    PRUNE: ClassVar[int] = 0
    REPARENT: ClassVar[int] = 1
    DEFAULT: ClassVar[int] = 2
    NO_CLEANUP: ClassVar[int] = 3

    def __init__(
        self,
        value: T,
        root: WeakTreeNode | None = None,
        callback=None,
        cleanup_mode: int = DEFAULT,
    ) -> None:
        def _remove(wr: ref, selfref=ref(self)):
            self = selfref()
            if callback:
                callback(wr)
            if self:
                self._cleanup()

        self._value = ref(value, _remove)
        self._root: ref[WeakTreeNode[T]] | None = None
        self.root = root
        self._branches: set[WeakTreeNode] = set()
        self._cleanup_mode = cleanup_mode

    @property
    def branches(self) -> set[WeakTreeNode]:
        return self._branches

    @property
    def root(self) -> WeakTreeNode | None:
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
    def value(self) -> T | None:
        # Dereference our value so the real object can be used.
        return self._value()

    def add_branch(self, value: T) -> WeakTreeNode[T]:
        """
        Creates a new node as a child of the current node, with the value of _value_

        :param value: The value to be stored by the new WeakTreeNode
        :return: The newly created node.
        """
        node = WeakTreeNode(value, self)
        return node

    def breadth(self) -> Generator[WeakTreeNode[T]]:
        """
        Provides a generator that performs a breadth-first traversal of the tree
        starting at the current node.

        :yield: The next node in the tree, breadth-first.
        """
        queue: deque[WeakTreeNode[T]] = deque([self])
        while queue:
            node = queue.popleft()
            yield node

            queue.extend(node.branches)

    def depth(self) -> Generator[WeakTreeNode[T]]:
        """
        Provides a generator that performs a depth-first traversal of the tree
        starting at the current node.

        :yield: The next node in the tree, depth-first.
        """
        stack: list[WeakTreeNode] = [self]
        while stack:
            node = stack.pop()
            yield node

            stack.extend(node.branches)

    def _cleanup(self):
        self._get_cleanup_method(self._cleanup_mode)(self)

    def _get_cleanup_method(self, cleanup_method: int) -> Callable:
        match cleanup_method:
            case self.PRUNE:
                return WeakTreeNode.prune
            case self.REPARENT:
                return WeakTreeNode.reparent
            case self.NO_CLEANUP:
                return WeakTreeNode._idle
            case _:
                if not self.root:
                    # If we're top level and ask for deault, default to pruning.
                    return WeakTreeNode.prune
                # Otherwise, find the root's cleanup method.
                return self.root._get_cleanup_method(self.root._cleanup_mode)

    @staticmethod
    def prune(node: WeakTreeNode):
        """
        Removes a node and all of its descendants.
        """
        if node.root:
            node.root._branches.discard(node)
        # TODO Make ._root a weakref so this will allow it to auto cleanup when its root
        # is gone.
        node._branches.clear()

    @staticmethod
    def reparent(node: WeakTreeNode):
        """
        Shifts a node's branches into the node's root.
        """
        print(f"Reparenting {node}'s branches")
        if node.root:
            node.root._branches.discard(node)
        for subnode in node._branches.copy():
            subnode.root = node.root

    @staticmethod
    def _idle(node: WeakTreeNode):
        # Intentionally do nothing.
        pass

    def __iter__(self) -> Generator[WeakTreeNode[T]]:
        """
        Default iteration method, in this case, breadth-first.

        :yield: The next node in the tree, breadth-first.
        """
        yield from self.breadth()

    def __repr__(self) -> str:
        return f"WeakTreeNode({self.value})"
