import gc
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

from forgely import workshop_change_signature, workshop_significantly_changed
from forgely_atelier import workshop_visual_fallback
from forgely_decision import advise


class ReliabilityFixes(unittest.TestCase):
    def test_small_text_changes_wake_ocr(self):
        for x, y in ((330, 350), (650, 420), (910, 280)):
            with self.subTest(position=(x, y)):
                old = Image.new('RGB', (1648, 928), '#333333')
                new = old.copy()
                ImageDraw.Draw(new).rectangle((x, y, x+7, y+11), fill='white')
                self.assertTrue(workshop_significantly_changed(
                    workshop_change_signature(old), workshop_change_signature(new)))

    def test_single_noise_pixel_does_not_wake_ocr(self):
        old = Image.new('RGB', (1648, 928), '#333333')
        new = old.copy(); new.putpixel((330, 350), (255, 255, 255))
        self.assertFalse(workshop_significantly_changed(
            workshop_change_signature(old), workshop_change_signature(new)))

    def test_rune_colour_change_with_equal_luminance_wakes_ocr(self):
        old = Image.new('RGB', (1648, 928), '#333333')
        new = old.copy()
        ImageDraw.Draw(old).rectangle((900, 280, 920, 300), fill=(255, 0, 0))
        ImageDraw.Draw(new).rectangle((900, 280, 920, 300), fill=(0, 129, 0))
        self.assertTrue(workshop_significantly_changed(
            workshop_change_signature(old), workshop_change_signature(new)))

    def test_uniform_purple_is_not_a_workshop(self):
        self.assertFalse(workshop_visual_fallback(
            Image.new('RGB', (1648, 928), (60, 50, 90))))

    def test_named_item_with_missing_profile_is_blocked(self):
        with patch('forgely_decision.natural_profile', return_value=None):
            p = advise({'PA': 1}, {'PA': 2}, pool=0, item='Unknown item')
        self.assertIsNone(p.rune)
        self.assertIn('profil', p.explanation.lower())

    def test_partial_named_profile_cannot_certify_advice(self):
        with patch('forgely_decision.natural_profile', return_value=None):
            self.assertIsNone(advise({'PA': 0, 'Force': 10}, {'PA': 1},
                natural_max={'Force': 60}, profile_complete=False,
                pool=100, item='Unknown item').rune)

    def test_complete_profile_does_not_certify_incomplete_observed_jet(self):
        with patch('forgely_decision.natural_profile', return_value={'Force': 60, 'Vitalité': 300}):
            proposal = advise({'Force': 10}, {'Force': 20}, pool=10, item='Known item')
        self.assertIsNone(proposal.rune)
        self.assertEqual(proposal.summary, 'Jet incomplet')

    def test_item_queries_close_connections_even_when_references_are_retained(self):
        from forgely_items import item_list
        retained = []
        original = sqlite3.connect

        class TrackedConnection(sqlite3.Connection):
            closed = False
            def close(self):
                self.closed = True
                super().close()

        def tracked(*args, **kwargs):
            connection = original(*args, factory=TrackedConnection, **kwargs)
            retained.append(connection)
            return connection

        with tempfile.TemporaryDirectory() as directory:
            try:
                with patch('forgely_items.sqlite3.connect', side_effect=tracked):
                    item_list(Path(directory) / 'items.sqlite3')
                self.assertTrue(retained)
                self.assertTrue(all(connection.closed for connection in retained))
            finally:
                for connection in retained:
                    connection.close()

    def test_sufficient_context_evidence_changes_rune_ranking(self):
        kwargs = dict(natural_max={'Force': 50}, pool=10)
        baseline = advise({'Force': 0}, {'Force': 10}, **kwargs)
        def measured(rune):
            return {'usable': True, 'n': 200,
                    'counts': {'SC': 0, 'SN': 0 if rune == baseline.rune else 200,
                               'EC': 200 if rune == baseline.rune else 0},
                    'quality': 'exploratoire_ocr_non_verifie'}
        result = advise({'Force': 0}, {'Force': 10},
                        contextual_for=measured, **kwargs)
        self.assertNotEqual(result.rune, baseline.rune)
        self.assertIsNotNone(result.estimates['contextual'])

    def test_insufficient_context_cannot_change_ranking(self):
        kwargs = dict(natural_max={'Force': 50}, pool=10)
        base = advise({'Force': 0}, {'Force': 10}, **kwargs)
        result = advise({'Force': 0}, {'Force': 10}, contextual_for=lambda _: {
            'usable': False, 'n': 1, 'counts': {'EC': 1}}, **kwargs)
        self.assertEqual(result.rune, base.rune)

    def test_learning_never_bypasses_a_line_constraint(self):
        result = advise({'PA': 1}, {'PA': 2}, pool=100,
            natural_max={'PA': 1}, contextual_for=lambda _: {
                'usable': True, 'n': 200, 'counts': {'SC': 200},
                'quality': 'local_verified'})
        self.assertIsNone(result.rune)

    def test_malformed_context_cannot_affect_rank(self):
        from forgely_decision import contextual_measurement
        for record in ({'usable': True, 'n': 200, 'counts': {'SC': 1}},
                       {'usable': True, 'n': True, 'counts': {'SC': 1}},
                       {'usable': True, 'n': 200, 'counts': {'SC': 200}, 'quality': 'simulation'}):
            self.assertIsNone(contextual_measurement(record))

    def test_transaction_commits_rolls_back_and_closes(self):
        from forgely_sqlite import database_connection
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'transaction.sqlite3'
            with database_connection(path) as connection:
                connection.execute('CREATE TABLE test(value)')
                connection.execute('INSERT INTO test VALUES(1)')
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute('SELECT 1')
            with self.assertRaises(ValueError):
                with database_connection(path) as connection:
                    connection.execute('INSERT INTO test VALUES(2)')
                    raise ValueError('rollback')
            with database_connection(path) as connection:
                self.assertEqual(connection.execute('SELECT value FROM test').fetchall(), [(1,)])

    def test_different_pools_never_share_learning(self):
        import json
        from forgely_sqlite import database_connection
        from forgely_labo_live import LiveLaboratory, compute_snapshot
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'learning.sqlite3'
            with database_connection(path) as connection:
                connection.execute('CREATE TABLE fusion_contexts(item,rune,outcome,before_json,source)')
                for pool, outcome in ((1, 'SC'), (9, 'EC')):
                    for _ in range(30):
                        connection.execute('INSERT INTO fusion_contexts VALUES(?,?,?,?,?)',
                            ('Anneau', 'Fo', outcome, json.dumps({'jet': {'Force': 10}, 'pool': pool}), 'local_screen'))
            lab = LiveLaboratory(path)
            lab._snapshot = compute_snapshot(path)
            self.assertEqual(lab.estimate('Anneau', 'Fo', {'Force': 10}, 1)['counts'], {'SC': 30})
            self.assertEqual(lab.estimate('Anneau', 'Fo', {'Force': 10}, 9)['counts'], {'EC': 30})
            self.assertIsNone(lab.estimate('Anneau', 'Fo', {'Force': 10}, 5))


if __name__ == '__main__':
    unittest.main()
