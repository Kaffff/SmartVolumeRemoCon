import unittest
import sys
import os
sys.path.append(os.path.join(os.getcwd(),"src"))
from decibel import Decibel

class TestDecibel(unittest.TestCase):
    def test_decibel(self):
        d = Decibel()
        v = d.get_decibel()
        print("Db:{:.3f}".format(v))
        self.assertTrue(0<v and v<300)

if __name__ == "__main__":
    unittest.main()