from __future__ import annotations

from collections import deque
from collections.abc import Generator
from typing import Generic, TypeVar
from weakref import ref


T = TypeVar("T")


class WeakTreeNode(Generic[T]):

    def __init__(self, value: T, root: WeakTreeNode | None = None) -> None:
        self._value = ref(value)
        self._root = root
        self._branches: set[WeakTreeNode] = set()

    @property
    def branches(self) -> set[WeakTreeNode]:
        return self._branches

    @property
    def root(self) -> WeakTreeNode | None:
        return self._root

    @root.setter
    def root(self, node: WeakTreeNode):
        self._root = node

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
        self._branches.add(node)
        return node

    def breadth(self) -> Generator[WeakTreeNode]:
        """
        Provides a generator that performs a breadth-first traversal of the tree
        starting at the current node.

        :yield: The next node in the tree, breadth-first.
        """
        queue: deque[WeakTreeNode] = deque([self])
        while queue:
            node = queue.popleft()
            print(type(node))
            yield node

            queue.extend(node.branches)

    def depth(self) -> Generator[WeakTreeNode]:
        """
        Provides a generator that performs a depth-first traversal of the tree
        starting at the current node.

        :yield: The next node in the tree, depth-first.
        """
        stack: list[WeakTreeNode] = [self]
        while stack:
            node = stack.pop()
            print(type(node))
            yield node

            stack.extend(node.branches)

    def __iter__(self) -> Generator[WeakTreeNode]:
        """
        Default iteration method, in this case, breadth-first.

        :yield: The next node in the tree, breadth-first.
        """
        yield from self.breadth()
