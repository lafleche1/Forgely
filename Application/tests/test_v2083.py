import unittest
from forgely_history_identity import latest_visible_history_name
from forgely_history_summary import summarize_history

HISTORY = """
+ ANNEAU DU CYCLOÏDE
© -1 Vitalité
BRAKMARIEN
+ ANNEAU DU PIOU VIOLET
§ -2 Puissance
+ reliquat
hs + À 30 Initiative
§ -2 Puissance
"""

class V2083(unittest.TestCase):
    def test_latest_heading(self):
        self.assertEqual(latest_visible_history_name(HISTORY), 'ANNEAU DU PIOU VIOLET')
    def test_initiative_icon(self):
        changes = summarize_history(HISTORY)['recent_changes']
        self.assertIn(('Initiative', 30), changes)
        self.assertIn(('Puissance', -2), changes)
    def test_no_unsigned_initiative(self):
        self.assertEqual(summarize_history('30 Initiative')['recent_changes'], [])
    def test_no_rune_outcome_inference(self):
        self.assertFalse(summarize_history(HISTORY)['rune_attempt_confirmed'])

if __name__ == '__main__': unittest.main()
