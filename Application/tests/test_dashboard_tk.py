"""Real Tk smoke checks, opt-in under a display (CI uses Xvfb)."""
import os
import queue
import unittest
from unittest.mock import patch


@unittest.skipUnless(os.environ.get('FORGELY_GUI_TESTS') == '1' and os.environ.get('DISPLAY'),
                     'requires FORGELY_GUI_TESTS=1 and a graphical display')
class DashboardTkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from forgely import Forgely
        with patch('forgely.load_plan', return_value=None), \
             patch('forgely.load_theme', return_value='Atelier émeraude'):
            cls.app = Forgely()
        cls.errors = []
        cls.app.report_callback_exception = lambda *args: cls.errors.append(args)

    @classmethod
    def tearDownClass(cls):
        cls.app.close()

    def setUp(self):
        app = self.app
        app.geometry('1180x780')
        app.plan = None
        app.item.set('')
        app.active_equipment_verified = False
        app.workshop_active = False
        app.live_jet = None
        app.live_pool = None
        app.live_after_fusion = True
        app.workshop_readings.reset()
        app.dashboard.sync()
        app.update()

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def test_initial_table_has_no_fictitious_readings(self):
        self.assertEqual(self.app.dashboard.table.get_children(), ())
        self.assertIn('—', self.app.dashboard.pool_label.cget('text'))

    def test_small_window_keeps_table_pool_and_latest_reading_visible(self):
        app = self.app
        app.geometry('960x660')
        app.update()
        for widget in (app.dashboard.table, app.dashboard.pool_label, app.detect_label, app.total_lbl, app.observe_button):
            self.assertTrue(widget.winfo_ismapped())
            self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(), app.winfo_rooty() + app.winfo_height())
        self.assertGreaterEqual(app.dashboard.table.winfo_height(), 70)

    def test_provisional_table_never_says_target_achieved(self):
        app = self.app
        app.workshop_active = True
        app.workshop_readings.partial_jet = {'Force': 40}
        app.plan = {'item': 'Objet test', 'stats': {'Force': {'target': 40}}}
        app.dashboard.sync()
        row = app.dashboard.table.item(app.dashboard.table.get_children()[0])
        self.assertEqual(tuple(row['values']), ('Force', 40, 40, 'À confirmer'))
        self.assertEqual(row['tags'], ['pending'])

    def test_confirmed_table_and_pool_update_from_current_state(self):
        app = self.app
        app.workshop_active = app.active_equipment_verified = True
        app.live_after_fusion = False
        app.item.set('Objet test')
        app.live_jet, app.live_pool = {'Force': 40}, .5
        app.plan = {'item': 'Objet test', 'stats': {'Force': {'target': 40}}}
        app.dashboard.sync()
        row = app.dashboard.table.item(app.dashboard.table.get_children()[0])
        self.assertEqual(tuple(row['values']), ('Force', 40, 40, 'Atteint'))
        self.assertIn('0,5', app.dashboard.pool_label.cget('text'))

    def test_workshop_loss_clears_confirmed_table_and_pool(self):
        app = self.app
        app.workshop_active = app.active_equipment_verified = True
        app.live_after_fusion = False
        app.live_jet, app.live_pool = {'Force': 40}, .5
        app.dashboard.sync()
        app.messages = queue.Queue()
        app.messages.put(('atelier_waiting', 'Atelier fermé'))
        app.process_messages()
        self.assertEqual(app.dashboard.table.get_children(), ())
        self.assertNotIn('0,5', app.dashboard.pool_label.cget('text'))

    def test_account_switch_clears_confirmed_table_and_pool(self):
        app = self.app
        app.workshop_active = app.active_equipment_verified = True
        app.live_after_fusion = False
        app.live_jet, app.live_pool = {'Force': 40}, .5
        app.dashboard.sync()
        app.messages = queue.Queue()
        app.messages.put(('account_switch', 'Autre compte test'))
        app.process_messages()
        self.assertEqual(app.dashboard.table.get_children(), ())
        self.assertNotIn('0,5', app.dashboard.pool_label.cget('text'))

    def test_all_themes_recolor_table_and_overlay_without_restart(self):
        from forgely_themes import THEMES
        for name, palette in THEMES.items():
            with patch('forgely.save_theme'):
                self.app.apply_theme(name)
            self.app.update()
            self.assertEqual(self.app.dashboard.style.lookup('Forgely.Treeview', 'background'), palette['PANEL'])
            self.assertEqual(self.app.overlay.advice_label.cget('bg'), palette['PANEL'])

    def test_reading_feed_is_bounded_and_keeps_latest_text(self):
        app = self.app
        for number in range(12):
            app.detect_label.configure(text=f'Variation {number} · à vérifier')
        self.assertEqual(len(app.dashboard.activity), 8)
        self.assertEqual(app.dashboard.activity[0], 'Variation 11 · à vérifier')
        self.assertEqual(app.dashboard.activity[1], 'Variation 10 · à vérifier')


if __name__ == '__main__':
    unittest.main()
