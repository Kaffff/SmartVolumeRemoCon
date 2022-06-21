import unittest
import sys
import os
sys.path.append(os.path.join(os.getcwd(),"src"))
from remocon import Remocon

label = "light_on"
class TestPlay(unittest.TestCase):
    def test_record(self):
        r = Remocon()
        r.play(label)
        

if __name__ == "__main__":
    unittest.main()