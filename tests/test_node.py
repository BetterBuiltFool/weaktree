from __future__ import annotations
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
        branch2 = self.root.add_branch(test_data["2"])
        branch3 = self.root.add_branch(test_data["3"])

        branch4 = branch1.add_branch(test_data["4"])
        branch1.add_branch(test_data["5"])

        branch2.add_branch(test_data["6"])
        branch3.add_branch(test_data["7"])

        branch8 = branch4.add_branch(test_data["8"])
        branch8.add_branch(test_data["9"])

    def test_breadth_iterator(self):
        test_data = self.test_data
        expected = {
            0: {test_data["root"]},
            # Layer 1: Children of root
            1: {test_data["1"], test_data["2"], test_data["3"]},
            2: {test_data["1"], test_data["2"], test_data["3"]},
            3: {test_data["1"], test_data["2"], test_data["3"]},
            # Layer 2: Grandchildren of root
            4: {test_data["4"], test_data["5"], test_data["6"], test_data["7"]},
            5: {test_data["4"], test_data["5"], test_data["6"], test_data["7"]},
            6: {test_data["4"], test_data["5"], test_data["6"], test_data["7"]},
            7: {test_data["4"], test_data["5"], test_data["6"], test_data["7"]},
            # Layer 3:
            8: {test_data["8"]},
            # Layer 4:
            9: {test_data["9"]},
        }

        for i, node in enumerate(self.root.breadth()):
            with self.subTest(i=i):
                self.assertIn(node.value, expected[i])


if __name__ == "__main__":
    unittest.main()
