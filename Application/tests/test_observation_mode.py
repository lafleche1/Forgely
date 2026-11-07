import tempfile
import unittest
from pathlib import Path
from forgely_observation_mode import load_observation_mode, save_observation_mode

class ObservationModeTests(unittest.TestCase):
    def test_default_is_copilot(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(load_observation_mode(d))
    def test_persist_and_switch(self):
        with tempfile.TemporaryDirectory() as d:
            save_observation_mode(d,True)
            self.assertTrue(load_observation_mode(d))
            save_observation_mode(d,False)
            self.assertFalse(load_observation_mode(d))
    def test_corrupt_file_defaults_safely(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'mode_observation.json').write_text('invalid')
            self.assertFalse(load_observation_mode(d))
