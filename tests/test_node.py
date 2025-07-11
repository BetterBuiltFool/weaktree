from __future__ import annotations

from collections import deque
import pathlib
import sys
import unittest

sys.path.append(str(pathlib.Path.cwd()))

from src.weaktree.node import WeakTreeNode  # noqa: E402


class TestObject:

    def __init__(self, data):
        self.data = data

    def __repr__(self) -> str:
        return f"TestObject({str(self.data)})"


class TestNode(unittest.TestCase):

    def setUp(self) -> None:
        test_data: dict[str, TestObject] = {
            "root": TestObject("Root"),
            "1": TestObject("1"),
            "2": TestObject("2"),
            "3": TestObject("3"),
            "4": TestObject("4"),
            "5": TestObject("5"),
            "6": TestObject("6"),
            "7": TestObject("7"),
            "8": TestObject("8"),
            "9": TestObject("9"),
        }
        self.test_data = test_data

        self.root = WeakTreeNode(test_data["root"])

        branch1 = self.root.add_branch(test_data["1"])

        branch4 = branch1.add_branch(test_data["4"])
        branch8 = branch4.add_branch(test_data["8"])
        branch8.add_branch(test_data["9"])

        branch1.add_branch(test_data["5"])

        branch2 = self.root.add_branch(test_data["2"])
        branch2.add_branch(test_data["6"])

        branch3 = self.root.add_branch(test_data["3"])
        branch3.add_branch(test_data["7"])

        # Note: These excess vars all descope after setup, so we don't have to worry
        # about excess references.
        # We could also do this by chaining add_branch, but that actually becomes
        # _less_ readable.

    def test_breadth_iterator(self):

        queue = deque()

        for node in self.root.breadth():
            no_root = node.root is None
            queued_root = node.root in queue

            self.assertTrue(no_root or queued_root)

            if queued_root:
                while queue[0] is not node.root:
                    queue.popleft()

            queue.append(node)

    def test_depth_iterator(self):

        stack = []

        for node in self.root.depth():
            # Determine if our node is top level, or a decendant of one in the stack
            no_root = node.root is None
            stack_root = node.root in stack

            self.assertTrue(no_root or stack_root)

            if stack_root:
                # For a descendant, remove the chain until we get to the node's
                # parent. If we end up out of order, this is what will cause our
                # test to fail
                while stack[-1] is not node.root:
                    stack.pop()

            stack.append(node)


if __name__ == "__main__":
    unittest.main()
