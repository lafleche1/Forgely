from unittest.mock import Mock,patch
from forgely import Forgely
from forgely_simulation_journal import SimulationJournal


def test_statistics_ui_uses_cached_virtual_totals_and_never_waits_on_journal(tmp_path):
    app=Mock()
    app.item.get.return_value='Anneau du Cycloïde'
    app.rune.get.return_value='Fo'
    app.simulator.item_id.return_value=14092
    app.simulation_journal=SimulationJournal(tmp_path/'virtual.db')
    app._virtual_totals={14092:48}
    app.stats_labels={kind:Mock() for kind in ('SC','SN','EC')}
    with patch('forgely.stats',return_value=(10,{'SC':4,'SN':2,'EC':4})), \
         patch.object(app.simulation_journal,'totals',side_effect=RuntimeError('UI must not read SQLite')):
        Forgely.refresh_stats_now(app)
    app.simulation_totals.set.assert_called_once_with('Réelles : 10 · Simulées : 48 · Total : 58')
