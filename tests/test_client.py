import unittest
from gepetto_viewer_rerun import Client


# TODO: add tests for addToGroup, deleteNode
class TestClient(unittest.TestCase):
    """Test cases for client class."""

    def test_create_window(self):
        self.client = Client()
        self.assertEqual(self.client.gui.createWindow("w1"), "w1")

    def test_add_to_group(self):
        self.client = Client()
        self.assertEqual(self.client.gui.addToGroup("test", "s1"), False)
