import tkinter as tk
import pytest


def test_default_overlay_never_opens_or_requests_manual_review(tmp_path):
    from forgely_overlay import FloatingBadge
    from forgely_reading_review import ReviewStore
    try:root=tk.Tk()
    except tk.TclError:pytest.skip('Tk display unavailable')
    root.withdraw();overlay=None
    try:
        overlay=FloatingBadge(root,lambda:None,lambda:None,lambda:None)
        overlay.withdraw()
        overlay.sync_review(99)
        overlay.open_review(ReviewStore(tmp_path/'review.sqlite3'),lambda:None)
        assert overlay.review_count==0
        assert not overlay.review_editing
        assert overlay.review_panel is None
        assert not overlay.review_button.winfo_manager()
        labels=[overlay.menu.entrycget(i,'label') for i in range(overlay.menu.index('end')+1)
                if overlay.menu.type(i)=='command']
        assert 'Lectures à vérifier' not in labels
    finally:
        if overlay is not None:overlay.destroy()
        root.destroy()


def test_overlay_review_is_inline_below_advice_and_disappears(tmp_path):
    from forgely_overlay import FloatingBadge
    from forgely_reading_review import ReviewStore
    try:
        root=tk.Tk()
    except tk.TclError:
        pytest.skip('Tk display unavailable')
    root.withdraw()
    overlay=None
    try:
        store=ReviewStore(tmp_path/'review.sqlite3')
        overlay=FloatingBadge(root,lambda:None,lambda:None,lambda:None,on_reviews=lambda:None)
        overlay.withdraw()
        overlay.sync_review(0)
        assert not overlay.review_button.winfo_manager()
        overlay.sync_review(2)
        root.update_idletasks()
        assert overlay.review_button.winfo_manager()=='place'
        assert int(overlay.review_button.place_info()['y'])>=199
        assert int(overlay.stats_table.place_info()['y'])>int(overlay.review_button.place_info()['y'])+25
        overlay.open_review(store,lambda:None)
        assert overlay.review_panel.winfo_toplevel() is overlay
        overlay.sync_review(0)
        assert not overlay.review_button.winfo_manager()
        assert not overlay.review_panel.winfo_manager()
        overlay.open_review(store,lambda:None)
        overlay.review_panel.show_confirmed.set(True)
        overlay.sync_review(0)
        assert overlay.review_panel.winfo_manager()=='place'
    finally:
        if overlay is not None:overlay.destroy()
        root.destroy()
