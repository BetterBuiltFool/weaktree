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

    def breadth(self) -> Generator[WeakTreeNode]:
        queue: deque[WeakTreeNode] = deque([self])
        while queue:
            node = queue.popleft()
            print(type(node))
            yield node

            queue.extend(node.branches)

    def depth(self) -> Generator[WeakTreeNode]:
        stack: list[WeakTreeNode] = [self]
        while stack:
            node = stack.pop()
            print(type(node))
            yield node

            stack.extend(node.branches)

    def __iter__(self) -> Generator[WeakTreeNode]:
        yield from self.breadth()
