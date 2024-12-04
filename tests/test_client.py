import unittest
from gepetto_viewer_rerun import Client


# TODO: add tests for addToGroup, deleteNode
class TestClient(unittest.TestCase):
    """Test cases for client class."""

    def test_create_window(self):
        """Tests for createWindow()"""
        self.client = Client()
        self.assertEqual(self.client.gui.createWindow("w1"), "w1")

    def test_add_to_group(self):
        """Tests for addToGroup()"""
        self.client = Client()
        self.assertFalse(self.client.gui.addToGroup("test", "s1"))

    def test_create_group(self):
        """Tests for createGroup()"""
        self.client = Client()

        res = self.client.gui.createGroup("hello")
        self.assertTrue(res)

        res = self.client.gui.createGroup("world")
        self.assertTrue(res)
        self.assertEqual(self.client.gui.groupList, ["hello", "world"])

    def test_delete_node(self):
        """Tests for deleteNode()"""
        self.client = Client()

        res = self.client.gui.deleteNode("hello", True)
        self.assertFalse(res)

        self.client.gui.createGroup("hello")
        self.assertEqual(self.client.gui.groupList, ["hello"])

        self.client.gui.deleteNode("hello", True)
        self.assertEqual(self.client.gui.groupList, [])

        self.client.gui.addSphere("sphere", 2, (255, 255, 0, 255))
        self.assertFalse(self.client.gui.deleteNode("sphere", True))
