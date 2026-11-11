"""Forgely local beta. No telemetry, cloud, OpenAI, game automation or input.
Optional explicit network action imports public item images; observation remains offline.
"""
from __future__ import annotations
from time import perf_counter_ns as forgely_perf_ns
from forgely_performance import PerformanceTracker
from forgely_runtime_cache import configure_if_changed,capture_wait
from forgely_session_ui import install_recorder,review_tick,review_event,review_transition,close_review,show_review
from forgely_zone_cache import ZoneCache
from forgely_pipeline import FrameMessageSink,AcceptedRuneEvent,AcceptedAttemptGroups,VerifiedItemContext,bind_event_item,history_scope
import io
from pathlib import Path
from datetime import datetime
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from forgely_observation_mode import load_observation_mode, save_observation_mode, enable_copilot_for_goals
from forgely_live_equipment import bind_confirmed_equipment
from forgely_data import connect, insert_observation, insert_unassigned, unassigned_total, stats, stats_by_rune, recent, RUNES, DB_FILE, DATA_DIR
from forgely_attempt_activity import record_activity,activity_total,activity_recent
from runeforge_observer import extract_text
from forgely_detection import HistoryTransitionTracker, read_regions, crop_regions
from forgely_windows import list_dofus_windows, auto_game_window, foreground_handle, is_own_foreground, list_selectable_windows, window_by_handle, physical_pixels, read_window_bounds
from forgely_overlay import FloatingBadge
from forgely_rune_icons import rune_icon_path
from forgely_typographie import families as font_families
from forgely_arrondi import RoundedButton, RoundedCard
from forgely_themes import THEMES, load_theme, save_theme
from forgely_plan import STATS, load_plan, save_plan
from forgely_vision import RuneLibrary, icon_patch
from forgely_catalogue import sync_catalogue, TARGETS
from forgely_items import item_list, register_item, find_item, remember_candidate, pending_items, item_history, register_item_with_icon, IconIdentityConflict, item_icon,key_for
from forgely_item_vision import crop_item_header, identify_known, possible_unknown, recognize_item_header
from forgely_item_icons import crop_item_icon, normalize_icon, ItemVisualTracker, history_icon_for_name, history_icon_by_visual_row
from forgely_history_identity import resolve_history_identity, visible_history_names, latest_visible_history_name
from forgely_atelier import (read_atelier, crop_zone, parse_reliquat, choose_reliquat,
    title_candidates, focus_workshop,workshop_title_signature,workshop_frame_verified,effects_text_occluded)
from forgely_jet import parse_jet
from forgely_item_references import download_references
from forgely_profile_guidance import compare as compare_theoretical_profile
from forgely_workshop_readings import WorkshopReadings
from forgely_equipment_session import ManualEquipmentSession
from forgely_measured_goals import MeasuredGoals,current_snapshot,bound_session,learning_sources,goal_editor_jet,maybe_prompt_goals
from forgely_copilot_continuity import (IconReplacement,advice_key,held_advice,advice_unavailable_reason,numeric_snapshot_covers,
    ConfirmedAtelierRead,read_current_atelier,numeric_frame_signature)
from forgely_continuous_identity import (crop_current_item, current_icon,
    effect_signature, CurrentSlotTracker, match_current_item,
    remember_current_item, remember_provisional)
from forgely_item_icons import icon_distance
from forgely_equipment_identity import slot_equipment_decision, is_catalogue_identity, crop_catalogue_slot
from forgely_ocr_diagnostic import evaluate as evaluate_ocr
from forgely_probabilites import reference as rune_reference, summary as rune_summary
from forgely_decision import advise, Proposal
from forgely_rules import MODES as OBJECTIVE_MODES, objective_mode
from forgely_copilote import MODES, player_signal
from forgely_context import save_transition, context_rates,FusionPairing
from forgely_learning import complete_learning_profile
from forgely_expert import build_dashboard, render_dashboard, audit_transition, rules_text
from forgely_simulation_live import SimulationWorker
from forgely_simulation_journal import SimulationJournal
from forgely_labo_live import LiveLaboratory
from forgely_tools import (read_settings,save_settings,STRATEGIES,
    export_observations_csv,export_item_summary,backup_local,import_bounds_csv,
    natural_bounds,illustrative_scenario,advisory_status,cost_since,observation_cursor,price_reference_label)
from forgely_gallery import verify_goal,save_success,list_successes,export_gallery_json

def clear_fusion_pairing(app):
    pairing=getattr(app,'fusion_pairing',None)
    if isinstance(pairing,FusionPairing):pairing.clear()


BG='#211F1B'; PANEL='#302C26'; PANEL2='#423B30'; ACCENT='#778F35'; GOLD='#E0C28C'
FG='#F4EBDD'; MUTED='#B8AD9C'; GREEN='#A5C95A'; RED='#E48A79'

def set_palette(name):
    global BG,PANEL,PANEL2,ACCENT,GOLD,FG,MUTED,GREEN,RED
    theme=THEMES[name]
    BG,PANEL,PANEL2,ACCENT,GOLD,FG,MUTED,GREEN,RED=(theme[key] for key in ('BG','PANEL','PANEL2','ACCENT','GOLD','FG','MUTED','GREEN','RED'))



def workshop_change_signature(image):
    """Native-resolution semantic regions used only for change detection.

    Keep pixels rather than an exact hash: anti-aliasing, blinking cursors and
    animation make exact checksums unstable even with quantisation.
    """
    from forgely_atelier import ZONES
    w, h = image.size
    # Full semantic coverage: rune-only and upper-effect changes must not wait
    # for the 12-second idle refresh. Tile the tall effects table so a single
    # changed line remains large enough to survive the noise threshold.
    left, top, right, bottom = ZONES['effects']
    step = (bottom-top)/3
    regions = (ZONES['history'], *( (left,top+i*step,right,top+(i+1)*step) for i in range(3)),
               ZONES['runes'], ZONES['reliquat'], (.391,.194,.409,.232), ZONES['title'])
    samples = []
    for x1, y1, x2, y2 in regions:
        patch = image.crop((int(x1*w), int(y1*h), int(x2*w), int(y2*h)))
        # Keep native text pixels: a changed digit must not disappear during
        # reduction of a tall history/effects panel to a 96-pixel thumbnail.
        patch = patch.convert('RGB')
        samples.append(patch.tobytes())
    return tuple(samples)


def workshop_significantly_changed(previous, current):
    """Tolerant image comparison. Never interprets OCR or certifies events."""
    if previous is None or len(previous) != len(current):
        return True
    from PIL import ImageChops
    for old, new in zip(previous, current):
        if len(old) != len(new):
            return True
        # Ignore isolated pixel noise; require a small cluster of changed pixels.
        difference = ImageChops.difference(Image.frombytes('L',(len(old),1),old),
                                          Image.frombytes('L',(len(new),1),new))
        changed = sum(difference.histogram()[36:])
        if changed >= 6:
            return True
    return False


class LatestFrameMailbox:
    """Single-slot latest-image handoff; never queues outdated screenshots."""
    def __init__(self):
        self._condition = threading.Condition()
        self._frame = None
        self._sequence = 0
        self._invalid = None
        self._generation = 0

    def publish(self, image, title, captured_ns, capture_duration_ns):
        with self._condition:
            if self._frame is not None and self._frame[2] != title:
                self._generation += 1
            self._sequence += 1
            self._frame = (self._sequence, image, title, captured_ns, capture_duration_ns)
            self._invalid = None
            self._condition.notify_all()

    def invalidate(self, reason):
        with self._condition:
            if self._frame is None and self._invalid == reason:
                return self._generation
            self._generation += 1
            self._frame = None
            self._invalid = reason
            self._condition.notify_all()
            return self._generation

    def generation(self):
        with self._condition:
            return self._generation

    def snapshot(self):
        with self._condition:
            return self._generation, self._frame

    def deliver_current(self,generation,title,publish):
        """Acceptance and queue insertion are atomic against capture invalidation."""
        with self._condition:
            if self._generation==generation and self._frame is not None and self._frame[2]==title:
                publish()

    def wait_new(self, last_sequence, stop_event):
        with self._condition:
            self._condition.wait_for(lambda: stop_event.is_set() or
                                 (self._frame is not None and self._frame[0] > last_sequence),
                                 timeout=0.25)
            if stop_event.is_set():
                return None
            if self._frame is None or self._frame[0] <= last_sequence:
                return None
            return self._frame

    def wait_snapshot(self, last_sequence, stop_event, generation):
        """Atomically bind a frame to its context, waking on invalidation too."""
        with self._condition:
            self._condition.wait_for(lambda: stop_event.is_set() or generation != self._generation or
                (self._frame is not None and self._frame[0] > last_sequence), timeout=0.25)
            frame=self._frame
            if stop_event.is_set() or frame is None or frame[0] <= last_sequence:
                frame=None
            return self._generation,frame

class GameNotForeground(RuntimeError):
    pass


def foreground_belongs_to_game(active, game_handle):
    """Compare top-level ancestors: Unity can focus a child HWND."""
    if not active or not game_handle:
        return False
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetAncestor.restype = wintypes.HWND
        root = user32.GetAncestor(wintypes.HWND(active), 2) or active
        return int(root) == int(game_handle)
    except (OSError, AttributeError):
        return active == game_handle


def capture_window_native(handle, width, height):
    """Attempt an HWND capture without desktop overlays (may fail for GPU games).

    Returns None when Windows cannot provide an actual image. A black/blank
    PrintWindow surface must never be passed to OCR as a valid game frame.
    """
    import ctypes
    from ctypes import wintypes
    from PIL import ImageStat
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
    hwnd = wintypes.HWND(handle)
    user32.GetWindowDC.argtypes = [wintypes.HWND]
    user32.GetWindowDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.ReleaseDC.restype = ctypes.c_int
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
    user32.PrintWindow.restype = wintypes.BOOL
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [('biSize',wintypes.DWORD),('biWidth',wintypes.LONG),
                    ('biHeight',wintypes.LONG),('biPlanes',wintypes.WORD),
                    ('biBitCount',wintypes.WORD),('biCompression',wintypes.DWORD),
                    ('biSizeImage',wintypes.DWORD),('biXPelsPerMeter',wintypes.LONG),
                    ('biYPelsPerMeter',wintypes.LONG),('biClrUsed',wintypes.DWORD),
                    ('biClrImportant',wintypes.DWORD)]
    class BITMAPINFO(ctypes.Structure):
        _fields_ = [('bmiHeader',BITMAPINFOHEADER),('bmiColors',wintypes.DWORD*3)]
    gdi32.GetDIBits.argtypes = [wintypes.HDC,wintypes.HBITMAP,wintypes.UINT,
                                wintypes.UINT,ctypes.c_void_p,ctypes.POINTER(BITMAPINFO),wintypes.UINT]
    gdi32.GetDIBits.restype = ctypes.c_int
    src = user32.GetWindowDC(hwnd)
    if not src:
        return None
    mem = bmp = old = None
    try:
        mem = gdi32.CreateCompatibleDC(src)
        bmp = gdi32.CreateCompatibleBitmap(src,width,height)
        if not mem or not bmp:
            return None
        old = gdi32.SelectObject(mem,bmp)
        if not user32.PrintWindow(hwnd,mem,2):
            return None
        info=BITMAPINFO()
        info.bmiHeader.biSize=ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth=width
        info.bmiHeader.biHeight=-height
        info.bmiHeader.biPlanes=1
        info.bmiHeader.biBitCount=32
        buf=ctypes.create_string_buffer(width*height*4)
        if gdi32.GetDIBits(mem,bmp,0,height,buf,ctypes.byref(info),0)!=height:
            return None
        img=Image.frombuffer('RGBA',(width,height),buf,'raw','BGRA',0,1).convert('RGB')
        # GPU windows can return entirely black or uniform frames.
        if max(ImageStat.Stat(img.resize((64,36))).stddev)<5:
            return None
        return img
    finally:
        if old and mem: gdi32.SelectObject(mem,old)
        if bmp: gdi32.DeleteObject(bmp)
        if mem: gdi32.DeleteDC(mem)
        user32.ReleaseDC(hwnd,src)


class GameCapture:
    """Identify DOFUS by process or versioned title, capture only its HWND."""
    def __init__(self):
        self.last_handle = None
        self.selected_title = ''
        self.manual_handle = None
        self.debug_stage = 'En attente de capture'
        self.workshop_handle = None
        self.probe_hits = {}
        self.last_probe_ns = 0
        self.capture_failures = 0
        self.last_good_capture_ns = 0
        self._screen=threading.local()
        self._workshop_locators=threading.local()
        self.reacquire_layout=threading.Event()

    def _focus_workshop(self, image, handle):
        from forgely_workshop_layout import WorkshopLocator
        locator = getattr(self._workshop_locators, 'locator', None)
        if locator is None:
            locator = self._workshop_locators.locator = WorkshopLocator()
        if self.reacquire_layout.is_set():
            self.reacquire_layout.clear()
            locator.transform=None
            locator.last_search=-1e10
        normalized = locator.normalize(image, handle)
        return focus_workshop(normalized)

    def _foreground_image(self, window):
        """Reuse MSS only on its creating thread; convert BGRA in native Pillow."""
        import mss
        session=getattr(self._screen,'session',None)
        if session is None:
            session=self._screen.session=mss.mss()
        try:
            shot=session.grab({'left':window.left,'top':window.top,
                               'width':window.width,'height':window.height})
            return Image.frombytes('RGB',shot.size,shot.bgra,'raw','BGRX')
        except Exception:
            self.close()
            raise

    def close(self):
        """Release this thread's capture resources, including after failures."""
        session=getattr(self._screen,'session',None)
        if session is not None:
            del self._screen.session
            session.close()

    def _native_image(self, window):
        """PrintWindow renders the outer HWND; OCR sees only the client area."""
        outer = getattr(window, 'outer_rect', None)
        if outer is None:
            return capture_window_native(window._hWnd, window.width, window.height)
        left, top, right, bottom = outer
        image = capture_window_native(window._hWnd, right-left, bottom-top)
        if image is None or image.size != (right-left, bottom-top):
            return None
        box = (window.left-left, window.top-top,
               window.left-left+window.width, window.top-top+window.height)
        if not (0 <= box[0] < box[2] <= image.width and 0 <= box[1] < box[3] <= image.height):
            return None
        client = image.crop(box)
        # A rendered title bar can mask a black GPU client in the outer-frame
        # check. Validate the exact surface that is about to enter OCR.
        from PIL import ImageStat
        if max(ImageStat.Stat(client.resize((64, 36))).stddev) < 5:
            return None
        return client

    def _check_geometry(self, window):
        """Discard a frame if a mode switch/move happened during acquisition."""
        client = getattr(window, 'client_rect', None)
        if client is not None:
            try:
                current = read_window_bounds(window._hWnd)
            except OSError as exc:
                raise GameNotForeground(str(exc)) from exc
            if current != (window.outer_rect, client):
                raise GameNotForeground('Affichage DOFUS modifié · recadrage automatique en cours')

    @physical_pixels()
    def capture(self):
        active = foreground_handle()
        candidates = list_dofus_windows()
        self.debug_stage = f'Fenêtres DOFUS candidates : {len(candidates)}'
        if self.manual_handle is not None:
            w = window_by_handle(self.manual_handle, candidates)
        elif self.workshop_handle is not None:
            w = window_by_handle(self.workshop_handle, candidates)
        else:
            w = window_by_handle(self.last_handle, candidates)
            if w is None:
                w = auto_game_window(candidates, active, None)
            if w is None and candidates:
                # Initial scan can start on any account; OCR will find the workshop.
                w = candidates[0]
        if w is None:
            raise GameNotForeground(self.debug_stage + ' · compte introuvable, aucune bascule automatique')
        self.last_handle = getattr(w, '_hWnd', None)
        self.selected_title = w.title
        if w.isMinimized or w.width < 300 or w.height < 300:
            raise GameNotForeground('Fenêtre DOFUS réduite ou trop petite pour l’OCR.')
        # Foreground may be a Unity child HWND. Prefer the desktop capture in
        # this case; PrintWindow frequently returns black on GPU games.
        if foreground_belongs_to_game(active,self.last_handle):
            image=self._foreground_image(w)
            if not foreground_belongs_to_game(foreground_handle(),self.last_handle):
                raise GameNotForeground('Focus modifie pendant la capture : image ecartee, attente de DOFUS.')
            self._check_geometry(w)
            self.debug_stage='Capture DOFUS au premier plan · OCR en cours'
            return self._focus_workshop(image, self.last_handle),w.title
        # When the diagnostic / overlay owns focus, do not capture its pixels.
        # PrintWindow can capture independently of the foreground app, if the
        # game's renderer supports it.
        try:
            img=self._native_image(w)
        except (OSError,ValueError):
            img=None
        if img is None:
            self.debug_stage='DOFUS identifié · capture native indisponible (jeu GPU) ; cliquer sur DOFUS pour lire'
            raise GameNotForeground(self.debug_stage)
        self._check_geometry(w)
        self.debug_stage='Capture native DOFUS · OCR en cours'
        focused=self._focus_workshop(img,self.last_handle)
        locator=getattr(self._workshop_locators,'locator',None)
        if locator is not None and not locator.verified:
            self.debug_stage='Capture native non exploitable : atelier non cadre ; remets DOFUS au premier plan.'
            raise GameNotForeground(self.debug_stage)
        return focused,w.title


    @physical_pixels()
    def probe_other_workshops(self, reader):
        """Probe other accounts only after OCR has failed on the current one.

        Never infer a workshop merely from a window title or the presence of
        stats; require two successful independent atelier OCR observations.
        """
        if self.manual_handle is not None:
            return None
        import time
        now=time.monotonic_ns()
        if now-self.last_probe_ns < 4_000_000_000:
            return None
        self.last_probe_ns=now
        candidates=list_dofus_windows()
        for w in candidates:
            handle=getattr(w,'_hWnd',None)
            if handle == self.last_handle or handle is None or w.isMinimized or w.width < 300 or w.height < 300:
                continue
            active=foreground_handle()
            if foreground_belongs_to_game(active,handle):
                try:
                    img=self._foreground_image(w)
                except Exception:
                    continue
            else:
                try:
                    img=self._native_image(w)
                except (OSError,ValueError):
                    img=None
                if img is None:
                    continue
            try:
                self._check_geometry(w)
            except GameNotForeground:
                continue
            if reader(self._focus_workshop(img, handle)):
                self.probe_hits[handle]=self.probe_hits.get(handle,0)+1
                if self.probe_hits[handle]>=2:
                    self.probe_hits.clear()
                    self.workshop_handle=handle
                    self.last_handle=handle
                    self.selected_title=w.title
                    self.debug_stage='Atelier trouvé automatiquement : '+w.title
                    return w.title
            else:
                self.probe_hits.pop(handle,None)
        return None


def ocr_engine_status():
    """Report actual OCR availability instead of mistaking blank text for failure."""
    try:
        import pytesseract
        from PIL import Image as PILImage
        extract_text(PILImage.new('RGB', (100, 40), 'white'))
        return 'OK (' + str(pytesseract.get_tesseract_version()).splitlines()[0] + ')'
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)[:160]


class Forgely(tk.Tk):
    def __init__(self):
        super().__init__()
        self.theme_name=load_theme()
        set_palette(self.theme_name)
        self.title('Forgely · L’atelier - v22.16')
        screen_w=self.winfo_screenwidth()
        screen_h=self.winfo_screenheight()
        self.geometry(f'{min(1220, max(740, screen_w-70))}x{min(790, max(510, screen_h-110))}')
        self.minsize(min(900,screen_w-80),min(570,screen_h-110))
        self.configure(bg=BG)
        self.ui_fonts = font_families(self)
        try: self.iconbitmap('assets/forgely.ico')
        except Exception: pass
        self.window_name=tk.StringVar(value='Détection automatique')
        self.item=tk.StringVar(value='')
        self.manual_equipment=None
        self.equipment_mode=tk.StringVar(value='automatic')
        self.equipment_picker=None
        self.rune=tk.StringVar(value='Vi')
        self.result=tk.StringVar(value='SC')
        self.filter_rune=tk.StringVar(value='Toutes')
        self.mode=tk.StringVar(value='Observateur silencieux')
        self.goal_mode=tk.StringVar(value='')
        self.perfect_goal_checked=tk.BooleanVar(value=False)
        self.observation_only=load_observation_mode(DATA_DIR)
        self._verified_item_context=None
        self.status=tk.StringVar(value='Prêt à observer · Stockage uniquement sur ton PC')
        self.last_detected=tk.StringVar(value='Aucune tentative détectée')
        self.running=False
        # Preference kept across launches; enabled by default.
        self.auto_floating=tk.BooleanVar(value=True)
        try:
            import json
            pref_file=DATA_DIR/'interface_preferences.json'
            if pref_file.exists():
                prefs=json.loads(pref_file.read_text(encoding='utf8'))
                self.auto_floating.set(bool(prefs.get('auto_floating',True)))
        except (OSError,ValueError,TypeError):
            pass
        self.stop_event=threading.Event()
        self.messages=queue.Queue()
        self.simulation_journal=SimulationJournal(DATA_DIR/'simulations.sqlite3')
        self.live_laboratory=LiveLaboratory()
        self.simulator=SimulationWorker(on_ready=self.publish_simulation,
            empirical_for=lambda:self.live_laboratory.empirical_model(),
            real_for=lambda item,rune,jet,pool:self.live_laboratory.estimate(item,rune,jet,pool),
            experience_for=lambda item,rune,jet,pool,targets,bounds:self.live_laboratory.experience(item,rune,jet,pool,targets,bounds))
        self._simulation_key=None
        self.simulation_io_error=None
        self._virtual_totals={}
        self.simulation_totals=tk.StringVar(value='Réelles : 0 · Simulées : 0 · Total : 0')
        threading.Thread(target=self.load_virtual_totals,name='Forgely-Stats-virtuelles',daemon=True).start()
        # UI only consumes recent visual observations; historical events remain queued.
        self.latest_observation_id = 0
        self.last_observation_delay_ms = None
        self.occluded_observations = 0
        self.pending=None
        self.track=HistoryTransitionTracker(RUNES)
        self.vision=RuneLibrary(DATA_DIR / "icones_runes",RUNES)
        from forgely_equipment_identity import prepare_equipment_catalogue
        threading.Thread(target=prepare_equipment_catalogue,
            name='Forgely-Catalogue-visuel',daemon=True).start()
        self.rune_center=None
        self.visual_state="Non configuré"
        # Keep the manually selected window when restarting observation.
        old_manual_handle=None
        self.capture=GameCapture()
        self.capture.manual_handle=None
        self.saved_auto=0
        self._session_observed_groups=0
        self.last_ocr_text=""
        self.last_capture_title=""
        self.skipped_frames=0
        self.error_frames=0
        self.last_debug_error=""
        self.logo_photo=None
        self.main_rune_photo=None
        self.scan_count=0
        self.last_reason="En attente de DOFUS"
        self.capture_debug_requested=threading.Event()
        self.readable_frames=0
        clear_fusion_pairing(self);self.active_equipment_verified=False
        self.last_item_read=''
        self.last_item_ocr_text=''
        self.last_item_candidate=''
        self.item_ocr_last=None
        self.item_ocr_streak=0
        self.item_visual_tracker=ItemVisualTracker()
        self.current_slot_tracker=CurrentSlotTracker()
        self.provisional_slot_id=None
        self.trusted_history_name=None
        self.trusted_history_generation=None
        self.current_slot_status='Emplacement non lu'
        self.item_icon_status="En attente de l’objet actuel"
        self.item_selection_source='none'
        self.missing_item_frames=0
        self.plan=load_plan()
        self.workshop_readings=WorkshopReadings(required_frames=2)
        self.pool_tracking_status={'value':None,'origin':'unknown'}
        self.measured_goals=MeasuredGoals()
        self.workshop_active=False
        self.first_item_name_seen=False
        self.before_identity_reading=None
        self.item_initial_reading=None
        self.live_jet=None
        self.live_pool=None
        self.live_after_fusion=True
        self.pre_fusion_sample=None
        self.pending_transition=None
        self.fusion_pairing=FusionPairing()
        install_recorder(self)
        self.budget_start_cursor=observation_cursor()
        self.last_transition_audit=None
        self.context_saved=0
        self.reading_reviews=None
        self.reading_review_status={}
        self.reading_review_error=''
        try:
            from forgely_reading_review import ReviewStore
            from forgely_review_collection import ReviewCollector
            self.reading_reviews=ReviewCollector(ReviewStore(DATA_DIR/'vision_v1'/'reviews.sqlite3'))
        except (ImportError,OSError) as exc:
            self.reading_review_error=str(exc)
        self.context_rejected=0
        self.learning_summary=tk.StringVar(value='Apprentissage en direct : en attente d’une tentative confirmée')
        self.last_learning=None
        self.current_proposal=None
        self.live_laboratory.start()
        try:
            import json
            calibration=json.loads((DATA_DIR/'calibration_rune.json').read_text(encoding='utf8'))
            self.rune_center=(float(calibration['x']),float(calibration['y']))
        except (OSError,ValueError,KeyError,TypeError):pass
        if self.plan: self.item.set(self.plan.get("item", ""))
        # A saved plan is not proof that the same item is currently in the workshop.
        clear_fusion_pairing(self);self.active_equipment_verified=False
        self._build()
        connect().close()
        self.overlay=FloatingBadge(self,self.restore,self.toggle_observer,self.close,self.open_equipment_quick, self.open_strategy, self.open_workbench,on_goals=self.open_floating_goals,
                                  on_reviews=None,on_perfect=self.toggle_perfect_goal)
        self.refresh_reading_reviews()
        self.overlay.withdraw()
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.after(40,self.process_messages)
        self.after(300,self.refresh_stats)

    def label(self,parent,text,size=11,bold=False,color=FG,**kwargs):
        return tk.Label(parent,text=text,bg=parent.cget('bg'),fg=color,font=(self.ui_fonts['display' if bold else 'body'],size,'bold' if bold else 'normal'),**kwargs)

    def button(self,parent,text,command,primary=False):
        return RoundedButton(parent,text,command,(self.ui_fonts['display'],10,'bold'),primary, palette=THEMES[self.theme_name])

    def card(self,parent,pad=15):
        return RoundedCard(parent,bg=PANEL,radius=12)

    def refresh_reading_reviews(self):
        service=self.reading_reviews
        count=len(service.store.pending()) if service is not None else 0
        self.reading_review_status={**self.reading_review_status,'pending':0,
                                    'automatic_candidates':count}
        if hasattr(self,'review_button'):
            self.review_button.pack_forget()
        if hasattr(self,'overlay'):
            self.overlay.sync_review(0)

    def show_reading_reviews(self):
        # Compatibility with old callbacks: user annotation is no longer part
        # of the product workflow. Archived crops never replace live readings.
        self.overlay.close_review()
        self.status.set('Lecture et calibration automatiques actives.')

    def finish_reading_review(self):
        self.refresh_reading_reviews()
        self.overlay.close_review()
        self.status.set('Réponse enregistrée. Les références candidates attendent des exemples concordants ; le jet actuel n’a pas été modifié.')

    def _build(self):
        from forgely_dashboard import AtelierDashboard
        self.dashboard = AtelierDashboard(self, THEMES[self.theme_name])
        self.render_plan()
        self.refresh_strategy()

    def open_more_menu(self):
        """Accessible options window: theme control visible and long list scrollable."""
        popup=tk.Toplevel(self)
        popup.title('Forgely — Plus d’options')
        popup.configure(bg=BG)
        screen_h=popup.winfo_screenheight()
        popup.geometry(f'440x{min(650,max(390,screen_h-130))}')
        popup.minsize(385,330)
        self.label(popup,'Plus d’options',19,bold=True).pack(anchor='w',padx=22,pady=(16,4))
        self.label(popup,'Personnalisation et outils de forgemagie',10,color=MUTED).pack(anchor='w',padx=22,pady=(0,8))
        # Always visible even on small laptop displays.
        self.button(popup,'Affichage · Obsidienne / Copilote',self.show_appearance).pack(fill='x',padx=22,pady=(0,9))
        area=tk.Frame(popup,bg=BG)
        area.pack(fill='both',expand=True,padx=(12,8),pady=(0,10))
        canvas=tk.Canvas(area,bg=BG,highlightthickness=0,borderwidth=0)
        scrollbar=tk.Scrollbar(area,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y')
        canvas.pack(side='left',fill='both',expand=True)
        contents=tk.Frame(canvas,bg=BG)
        window_id=canvas.create_window((0,0),window=contents,anchor='nw')
        contents.bind('<Configure>',lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e: canvas.itemconfigure(window_id,width=e.width))
        def open_option_and_close_menu(action):
            # Close the options menu before opening another window. Keeping it
            # alive would cover DOFUS when the diagnostic is copied/minimized.
            popup.destroy()
            action()
        for title,fn in [
            ('Statistiques et historique',self.show_history),
            ('Détail de la recommandation',self.open_strategy),
            ('Règles du copilote et poids des runes',self.show_copilot_rules),
            ('Basculer Copilote / Observation',self.toggle_observation_mode),
            ('🌐 Actualiser les jets théoriques DOFUS 3',self.update_public_references),
            ('Réussites et sauvegarde',self.open_workbench),
            ('Terminer et évaluer ma session',lambda:show_review(self)),
            ('Calibrer la reconnaissance des runes',self.learn_icon),
            ('Diagnostic OCR',self.show_ocr_diagnostic),
            ('Exporter les zones de lecture',self.request_debug_capture),
            ('Paramètres',self.show_settings),
        ]:
            self.button(contents,title,lambda action=fn: open_option_and_close_menu(action)).pack(fill='x',padx=8,pady=4)
        self.label(contents,
            f'Runes : {len(self.vision.labels())} types préchargés · reconnaissance automatique',
            9,color=MUTED).pack(anchor='w',padx=12,pady=(8,4))
        def wheel(event):
            if getattr(event,'delta',0):
                canvas.yview_scroll(-int(event.delta/120), 'units')
            elif getattr(event,'num',None)==4:
                canvas.yview_scroll(-1,'units')
            elif getattr(event,'num',None)==5:
                canvas.yview_scroll(1,'units')
        def bind_wheel(event):
            canvas.bind_all('<MouseWheel>',wheel)
            canvas.bind_all('<Button-4>',wheel)
            canvas.bind_all('<Button-5>',wheel)
        def unbind_wheel(event):
            canvas.unbind_all('<MouseWheel>')
            canvas.unbind_all('<Button-4>')
            canvas.unbind_all('<Button-5>')
        popup.bind('<Enter>',bind_wheel)
        popup.bind('<Leave>',unbind_wheel)
        popup.bind('<Destroy>',unbind_wheel)

    def render_plan(self,proposal=None):
        if getattr(self,'_batch_ui_updates',False) is True:
            self._plan_dirty=True
            return
        if getattr(self, 'dashboard', None) is not None:
            self.dashboard.sync()
        if self.observation_only:
            title,detail='Collecte active','Aucun objectif de rune suggéré dans ce mode.'
        else:
            if proposal is None:proposal=self.strategy_current()
            title=proposal.summary
            detail='Référence Dofocus · '+proposal.explanation[:170]+('… Voir le détail.' if len(proposal.explanation)>170 else '')
        if hasattr(self,'plan_item_lbl'):
            manual=getattr(self,'manual_equipment',None)
            from forgely_dashboard import current_card
            card=current_card(self)
            configure_if_changed(self.plan_item_lbl,text=card['title'])
            configure_if_changed(self.plan_action_lbl,text=title)
            configure_if_changed(self.plan_explain_lbl,text=detail)

    def update_mode_button(self):
        if hasattr(self,'mode_button'):
            self.mode_button.configure(text='Mode : Observation' if self.observation_only else 'Mode : Copilote')

    def toggle_observation_mode(self):
        self.observation_only=not self.observation_only
        save_observation_mode(DATA_DIR,self.observation_only)
        self.update_mode_button()
        self.render_plan()
        self.refresh_strategy()

    def strategy_current(self):
        started=forgely_perf_ns()
        try:
            proposal=Forgely._strategy_current(self)
            return proposal
        finally:
            tracker=getattr(self,'advice_performance',None)
            if not isinstance(tracker,PerformanceTracker):tracker=self.advice_performance=PerformanceTracker()
            tracker.record('calcul_conseil',forgely_perf_ns()-started)

    def _strategy_current(self):
        self._simulation_key=None
        if self.observation_only:
            return None
        unavailable=advice_unavailable_reason(self)
        if unavailable:
            if (getattr(self,'running',False) is True
                    and getattr(self,'workshop_active',False) is True
                    and getattr(self,'active_equipment_verified',False) is True):
                return Proposal(None,'calcul','Calcul…',unavailable,'lecture en cours')
            return Proposal(None,'suspendu',unavailable,
                'Aucune rune conseillée avant une nouvelle lecture complète et stable du jet et du puits.', '')
        settings=read_settings()
        price_book=None
        advice_mode=settings.get('strategy','Chances maximales')
        measured=getattr(self,'measured_goals',None)
        if isinstance(measured,MeasuredGoals) and measured.targets:
            goal_mode=getattr(self,'goal_mode',None)
            snapshot=current_snapshot(self)
            if snapshot is None:
                return Proposal(None,'calcul','Calcul…','Actualisation du jet et du reliquat.','lecture en cours')
            selected_item=(self.item.get() if self.active_equipment_verified else
                           measured.equipment.identity_name if measured.equipment is not None else None)
            sources,self._simulation_key=(learning_sources(selected_item,*snapshot,measured.targets,
                getattr(self,'live_laboratory',None),getattr(self,'simulator',None)) if snapshot else ({},None))
            return measured.proposal(snapshot,
                item=selected_item,
                mode=advice_mode,price_book=price_book,
                level=(self.plan or {}).get('level') if (self.plan or {}).get('item')==selected_item else None,
                **sources)
        """Only stable post-fusion OCR, confirmed equipment and saved goal can drive advice."""
        if not self.plan or not self.active_equipment_verified or self.item.get()!=self.plan.get('item'):
            return advise({}, {}, pool=None)
        targets={k:v['target'] for k,v in self.plan.get('stats',{}).items() if v.get('target') is not None}
        jets=self.live_jet or {}
        pool=self.live_pool
        if self.live_after_fusion:
            return Proposal(None,'calcul','Calcul…','Actualisation du jet et du reliquat.','lecture en cours')
        # No claim of EXO without a verified complete natural profile.
        # A partial imported CSV is useful for known overmax lines only.
        bounds=natural_bounds(self.item.get().strip())
        experience_bounds=complete_learning_profile(self.item.get().strip())
        sources,self._simulation_key=learning_sources(self.item.get().strip(),jets,pool,targets,
            self.live_laboratory,getattr(self,'simulator',None))
        from forgely_pricing import active_price_book
        proposal=advise(jets,targets,pool=pool,price_book=price_book,mode=advice_mode,
            predictive_policy=True,
            natural_max=experience_bounds or ({s:v[1] for s,v in bounds.items()} if bounds else None),
            item=self.item.get().strip(),profile_complete=bool(experience_bounds),
            level=self.plan.get('level'),**sources)
        # Contextual measurements are the only measured probabilities that can
        # describe a similar *starting state*. Aggregate rates are not forecasts.
        if proposal.rune and proposal.kind!='bloqué':
            stat=next((s for s,rs in __import__('forgely_decision').RUNE_CHOICES.items() if proposal.rune in rs),None)
            if stat in jets:
                rates=self.live_laboratory.estimate(self.item.get().strip(),proposal.rune,jets,pool)
                if rates is None: rates={'usable':False}

                if rates['usable']:
                    from dataclasses import replace
                    perc=rates['percentages']
                    context_text=(f" Dans {rates['n']} tentatives ayant le même jet observé et le même puits : "
                        f"SC {perc['SC']:.1f} %, SN {perc['SN']:.1f} %, EC {perc['EC']:.1f} % ; "
                        f"IC95 % SC {rates['ci95_sc'][0]:.1f}–{rates['ci95_sc'][1]:.1f} %. "
                        "Échantillon OCR non vérifié : indicatif seulement, pas une probabilité calibrée.")
                    proposal=replace(proposal,explanation=proposal.explanation+context_text,
                        evidence='Dofocus · référence ; observations OCR exploratoires séparées')
        return proposal

    def expert_detail(self,proposal,detail=None):
        """Add an auditable board without replacing the predictive evidence."""
        measured=getattr(self,'measured_goals',None)
        snapshot=current_snapshot(self) if isinstance(measured,MeasuredGoals) and measured.targets else None
        targets=(measured.targets if isinstance(measured,MeasuredGoals) and measured.targets else
            {k:v['target'] for k,v in (self.plan or {}).get('stats',{}).items() if v.get('target') is not None})
        jets=snapshot[0] if snapshot else self.live_jet or {}
        pool=snapshot[1] if snapshot else self.live_pool
        item=self.item.get().strip() if self.active_equipment_verified else None
        complete=complete_learning_profile(item) if item else None
        bounds=natural_bounds(item) if item else {}
        previous=getattr(self,'last_transition_audit',None)
        audit=(previous['audit'] if previous and previous['item']==item
               and previous['after']=={'jet':jets,'pool':pool} else None)
        board=build_dashboard(proposal,jets,targets,pool,
            natural_max=complete or ({s:v[1] for s,v in bounds.items()} if bounds else None),
            profile_complete=bool(complete),item=item,mode=read_settings().get('strategy','Chances maximales'),
            verified=self.active_equipment_verified or snapshot is not None,
            after_fusion=False if snapshot else self.live_after_fusion,last_transition=audit,
            level=(self.plan or {}).get('level') if (self.plan or {}).get('item')==item else None)
        if detail is None:
            from forgely_predictive import report_text
            detail=report_text(proposal,jets,targets,complete or None,pool)
        return render_dashboard(board)+'\n\nDétail du classement :\n'+detail

    def show_copilot_rules(self):
        popup=tk.Toplevel(self)
        popup.title('Forgely — Règles et poids des runes')
        popup.configure(bg=BG);popup.geometry('780x650')
        scroll=ttk.Scrollbar(popup);scroll.pack(side='right',fill='y')
        text=tk.Text(popup,wrap='word',bg=PANEL,fg=FG,font=(self.ui_fonts['body'],10),
                     padx=16,pady=16,yscrollcommand=scroll.set)
        text.pack(fill='both',expand=True);scroll.configure(command=text.yview)
        text.insert('1.0',rules_text(read_settings()));text.configure(state='disabled')
        return popup

    def waiting_for_item_label(self):
        """Small overlay message while the workshop is readable but item is not."""
        if not self.running or not self.workshop_active or self.active_equipment_verified:
            return None
        measured=getattr(self,'measured_goals',None)
        if bound_session(self):
            return None if current_snapshot(self) is not None else 'Actualisation du jet'
        if isinstance(measured,MeasuredGoals) and current_snapshot(self):
            return None if measured.targets else 'Définir le jet souhaité'
        manual=getattr(self,'manual_equipment',None)
        readings=getattr(self,'workshop_readings',None)
        jet_read=bool(getattr(readings,'partial_jet',None))
        if isinstance(manual,ManualEquipmentSession):
            if manual.invalidated:return manual.reason
            return ('Jet lu · association de l’objet' if jet_read
                    else 'Détection de l’objet choisi')
        if jet_read:
            return 'Jet lu · identification de l’objet'
        if self.last_item_candidate:
            return 'Objet à confirmer'
        if self.current_slot_tracker.count < 3:
            return 'Lecture de l’objet'
        if self.provisional_slot_id:
            return 'Objet détecté · identification du nom en cours'
        return 'Identification en cours'

    def sync_workshop_indicator(self):
        from forgely_copilote import workshop_state
        if getattr(self,'overlay',None) is not None:
            self.overlay.state_color(workshop_state(
                getattr(self,'running',False) is True,getattr(self,'workshop_active',False) is True))

    def refresh_strategy(self):
        if getattr(self,'_batch_ui_updates',False) is True:
            # Recording boundaries follow each numeric transition in order;
            # only presentation/calculation is deferred until the batch ends.
            review_tick(self)
            self._strategy_dirty=True
            return
        return Forgely._refresh_strategy_now(self)

    def _refresh_strategy_now(self):
        Forgely.sync_workshop_indicator(self)
        # Keep the actual recommendation/report visible through any overlay.
        # This cache is display-only: current_snapshot() remains strict.
        review_tick(self)
        if getattr(self, 'dashboard', None) is not None:
            self.dashboard.sync()
        if self.observation_only:
            self.current_proposal=None
            if getattr(self,'strategy_headline',None) is not None and self.strategy_headline.winfo_exists():
                configure_if_changed(self.strategy_headline,text='Observation passive : aucun conseil')
            if getattr(self,'strategy_explanation',None) is not None and self.strategy_explanation.winfo_exists():
                configure_if_changed(self.strategy_explanation,text='Les tentatives continuent à être collectées localement.')
            if hasattr(self,'advice_heading'):
                configure_if_changed(self.advice_heading,text='OBSERVATION PASSIVE  /  COLLECTE UNIQUEMENT')
                configure_if_changed(self.home_advice_label,text='Observation sans conseils',fg=GOLD)
                configure_if_changed(self.home_advice_detail,text='Détection des tentatives et statistiques locales actives. Aucune rune recommandée.')
                configure_if_changed(self.player_risk_label,text='Mode collecte : recommandations désactivées')
                self._update_main_rune_icon('')
            if hasattr(self,'overlay'):
                self.overlay.show_advice(self.waiting_for_item_label() or 'Observation', 'collecte')
            return
        if hasattr(self,'advice_heading'):
            configure_if_changed(self.advice_heading,text='PROCHAINE RUNE')
        proposal=self.strategy_current()
        self.current_proposal=proposal
        self._held_advice_key=advice_key(self)
        review_tick(self,proposal)
        if getattr(self,'strategy_headline',None) is not None and self.strategy_headline.winfo_exists():
            configure_if_changed(self.strategy_headline,text=proposal.summary)
        if getattr(self,'strategy_explanation',None) is not None and self.strategy_explanation.winfo_exists():
            configure_if_changed(self.strategy_explanation,text=proposal.explanation)
        targets={k:v['target'] for k,v in (self.plan or {}).get('stats',{}).items() if v.get('target') is not None}
        measured=getattr(self,'measured_goals',None)
        snapshot=current_snapshot(self) if isinstance(measured,MeasuredGoals) and measured.targets else None
        if isinstance(measured,MeasuredGoals) and measured.targets:targets=measured.targets
        signal=player_signal(proposal,snapshot[0] if snapshot else self.live_jet,targets,
            snapshot[1] if snapshot else self.live_pool,
            self.active_equipment_verified or snapshot is not None,
            False if snapshot else self.live_after_fusion,self.goal_mode.get())
        from forgely_predictive import report_text,report_measurements
        from forgely_vision_guidance import reference_for
        report_jet=snapshot[0] if snapshot else self.live_jet or {}
        report_pool=snapshot[1] if snapshot else self.live_pool
        report_jet,report_pool,measurement_origin=report_measurements(proposal,report_jet,report_pool,
            readings=getattr(self,'workshop_readings',None),
            active=bool(getattr(self,'running',False) and getattr(self,'workshop_active',False)))
        report_bounds=reference_for(self.item.get()) if self.active_equipment_verified else {}
        report_max={k:max(v) for k,v in report_bounds.items()} or None
        tracking=getattr(self,'pool_tracking_status',None)
        pool_origin=('calculé' if isinstance(tracking,dict) and tracking.get('origin')=='calculated' else 'lu')
        if measurement_origin!='lu':pool_origin=measurement_origin
        self.predictive_report=report_text(proposal,report_jet,targets,report_max,report_pool,pool_origin=pool_origin)
        if proposal.kind!='calcul':
            self.predictive_report=self.expert_detail(proposal,self.predictive_report)
        compact_report=report_text(proposal,report_jet,targets,report_max,report_pool,pool_origin=pool_origin,compact=True)
        if getattr(self,'strategy_explanation',None) is not None and self.strategy_explanation.winfo_exists():
            configure_if_changed(self.strategy_explanation,text=self.predictive_report)
        if hasattr(self,'overlay'):self.overlay.show_prediction(compact_report)
        if hasattr(self,'player_risk_label'):
            classification = ''
            if self.active_equipment_verified and self.live_jet:
                from forgely_fm_model import classify_item
                bounds = natural_bounds(self.item.get())
                if bounds:
                    states = classify_item(self.live_jet, {k:v[1] for k,v in bounds.items()}, complete_profile=False)
                    counts = {}
                    for state in states:
                        counts[state.kind] = counts.get(state.kind, 0) + 1
                    classification = ' · Jet : ' + ', '.join(f'{k} {v}' for k,v in counts.items())
                else:
                    classification = ' · Naturel/exo : fiche non vérifiée'
            configure_if_changed(self.player_risk_label,text=f'Risque indicatif : {signal.risk} · {self.goal_mode.get()}{classification}')
        if hasattr(self,'home_advice_label'):
            configure_if_changed(self.home_advice_label,text=signal.title,fg=GOLD if signal.stop else GREEN if proposal.rune else GOLD)

            sequence=(proposal.estimates or {}).get('objective',{}).get('sequence')
            if sequence:
                detail=signal.detail+' Anticipation : jusqu’à '+str(sequence['horizon'])+' poses pour atteindre tout le jet.'
            else:
                detail=signal.detail+'  '+proposal.explanation
            configure_if_changed(self.home_advice_detail,text=compact_report)
            self._update_main_rune_icon(proposal.rune if not signal.stop else '')
        if hasattr(self,'overlay'):
            self.overlay.show_advice((signal.title if proposal.kind=='calcul' else self.waiting_for_item_label()) or
                (signal.title if proposal.kind=='suspendu' else 'STOP' if signal.stop else signal.title), signal.risk)
        if getattr(self, 'dashboard', None) is not None:
            self.dashboard.fit_advice()

    def _update_main_rune_icon(self, rune: str):
        """Display only a uniquely matched local rune icon; no invented substitutes."""
        if not hasattr(self, 'main_rune_icon'):
            return
        path = rune_icon_path(rune or '')
        from forgely_runtime_cache import file_revision
        key=(id(self.main_rune_icon),rune,file_revision(path) if path is not None else None)
        if getattr(self,'_last_main_rune_icon_key',None)==key:return
        if path is not None:
            try:
                with Image.open(path) as source:
                    picture = source.convert('RGBA')
                    picture.thumbnail((58, 58), Image.Resampling.LANCZOS)
                    self.main_rune_photo = ImageTk.PhotoImage(picture)
                self.main_rune_icon.configure(image=self.main_rune_photo, text='', width=64, height=64)
                self._last_main_rune_icon_key=key
                return
            except (OSError, ValueError, tk.TclError):
                pass
        self.main_rune_photo = None
        self.main_rune_icon.configure(image='', text='FM', width=5, height=3)
        self._last_main_rune_icon_key=key
    def open_budget(self):
        """Manual cost planner; never pretends OCR knows the market price."""
        popup=tk.Toplevel(self);popup.title('Forgely — Budget de runes')
        popup.configure(bg=BG);popup.geometry('580x540')
        cfg=read_settings()
        budget_value=tk.StringVar(value=str(cfg['budget_kamas']))
        stop_at_budget=tk.BooleanVar(value=cfg.get('stop_at_budget',False))
        self.label(popup,'Budget des runes',18,bold=True,color=GOLD).pack(anchor='w',padx=20,pady=14)
        self.label(popup,price_reference_label(cfg),9,color=MUTED,wraplength=530,justify='left').pack(anchor='w',padx=20)
        self.label(popup,'Budget depuis le lancement (kamas, 0 = sans limite)',10).pack(anchor='w',padx=20,pady=(12,0))
        tk.Entry(popup,textvariable=budget_value).pack(fill='x',padx=20)
        tk.Checkbutton(popup,text='Suspendre les conseils quand le budget est épuisé',variable=stop_at_budget,bg=BG,fg=FG,selectcolor=PANEL).pack(anchor='w',padx=20,pady=8)
        rune=tk.StringVar(value=self.rune.get() or 'Vi')
        price=tk.StringVar(value=str(cfg['prices'].get(rune.get(),'')))
        self.label(popup,'Rune',10).pack(anchor='w',padx=20,pady=(12,0))
        rune_selector=ttk.Combobox(popup,textvariable=rune,values=sorted(RUNES),state='readonly')
        rune_selector.pack(fill='x',padx=20)
        rune_selector.bind('<<ComboboxSelected>>',lambda _e:price.set(str(read_settings()['prices'].get(rune.get(),''))))
        self.label(popup,'Prix unitaire (kamas)',10).pack(anchor='w',padx=20,pady=(12,0))
        tk.Entry(popup,textvariable=price).pack(fill='x',padx=20)
        result=self.label(popup,'',10,color=GOLD,wraplength=425,justify='left');result.pack(anchor='w',padx=20,pady=12)
        def compute():
            try:
                fresh=read_settings()
                if price.get().strip(): fresh['prices'][rune.get().strip()]=int(price.get())
                fresh['budget_kamas']=int(budget_value.get() or 0)
                fresh['stop_at_budget']=bool(stop_at_budget.get())
                save_settings(fresh)
                self.rune_prices=dict(fresh['prices'])
                cost=cost_since(self.budget_start_cursor,fresh['prices'])
                remaining=max(0,fresh['budget_kamas']-cost['known_cost']) if fresh['budget_kamas'] else None
                result.configure(text=f'Dépense enregistrée : {cost["known_cost"]:g} K. '
                    f'Tentatives sans prix : {cost["unpriced_attempts"]}. '
                    f'Restant : {remaining if cost["complete"] and remaining is not None else "inconnu ou sans limite"}. '
                    'Estimation aux prix saisis, tous objets depuis le lancement ; les tentatives non détectées ne sont pas comptées.')
                self.refresh_strategy()
            except ValueError: messagebox.showerror('Valeur incorrecte','Saisis des nombres positifs.',parent=popup)
        self.button(popup,'Enregistrer les prix',compute,primary=True).pack(anchor='w',padx=20)


    def open_strategy(self):
        if self.observation_only:
            messagebox.showinfo('Mode Observation', 'Les recommandations sont désactivées. Passe en mode Copilote pour les consulter.')
            return
        """Live recommendation viewer. Does not perform game actions."""
        popup=tk.Toplevel(self);popup.title('Forgely — Conseil de forgemagie')
        popup.configure(bg=BG)
        from forgely_dashboard import advice_window_size
        width,height=advice_window_size(self.winfo_screenwidth(),self.winfo_screenheight())
        popup.geometry(f'{width}x{height}')
        canvas=tk.Canvas(popup,bg=BG,highlightthickness=0)
        scroll=ttk.Scrollbar(popup,orient='vertical',command=canvas.yview)
        scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        canvas.configure(yscrollcommand=scroll.set)
        contents=tk.Frame(canvas,bg=BG)
        window=canvas.create_window((0,0),window=contents,anchor='nw')
        contents.bind('<Configure>',lambda event:canvas.configure(scrollregion=canvas.bbox('all')))
        def resize_contents(event):
            canvas.itemconfigure(window,width=event.width)
            for widget in contents.winfo_children():
                if isinstance(widget,tk.Label):widget.configure(wraplength=max(120,event.width-44))
        canvas.bind('<Configure>',resize_contents)
        popup.attributes('-topmost',True)
        self.label(contents,'PROCHAINE RUNE',12,color=GOLD,bold=True).pack(anchor='w',padx=22,pady=(20,5))
        self.label(contents,'Objectif : atteindre le jet souhaité',10,color=MUTED).pack(anchor='w',padx=22,pady=(4,12))
        proposal=self.strategy_current()
        self.strategy_headline=self.label(contents,proposal.summary,20,bold=True,color=GREEN,wraplength=620,justify='left')
        self.strategy_headline.pack(anchor='w',padx=22,pady=(0,12))
        self.strategy_explanation=self.label(contents,self.expert_detail(proposal),10,color=FG,wraplength=620,justify='left')
        self.strategy_explanation.pack(anchor='w',padx=22,pady=(0,14))
        self.label(contents,'Les fréquences constatées ne prouvent pas le taux du prochain essai. Aucun clic dans DOFUS.',9,color=MUTED,wraplength=620,justify='left').pack(anchor='w',padx=22,pady=(0,12))
        self.button(contents,'Actualiser le conseil',self.refresh_strategy,primary=True).pack(anchor='w',padx=22)
        def close_popup():
            self.strategy_headline=None
            self.strategy_explanation=None
            popup.destroy()
        popup.protocol('WM_DELETE_WINDOW',close_popup)
        return popup

    def open_plan_editor(self):
        self.open_equipment_picker(goals_only=True)

    def open_floating_goals(self):
        self.open_equipment_picker(goals_only=True,floating=True)

    def make_combo(self,parent,var,values):
        combo=ttk.Combobox(parent,textvariable=var,values=list(values),state='readonly',font=(self.ui_fonts['body'],10))
        return combo

    def update_public_references(self):
        """Visible entry point for the optional DOFUS 3 theoretical reference update."""
        if not messagebox.askyesno('Référentiel DOFUS 3',
            'Télécharger les jets théoriques publics depuis Dofusdude ?\n'
            'Connexion Internet requise. Les jets réels ne seront jamais remplacés.',parent=self):
            return
        self.status.set('Téléchargement du référentiel DOFUS 3 en cours…')
        def job():
            try:
                result = download_references()
            except Exception as exc:
                def show_error(msg=str(exc)):
                    self.status.set('Échec de la mise à jour des jets théoriques')
                    messagebox.showerror('Référentiel DOFUS 3', 'Import impossible : '+msg,parent=self)
                self.after(0,show_error)
            else:
                def show_success():
                    self.status.set(f'Référentiel actualisé : {result[0]} équipements')
                    messagebox.showinfo('Référentiel DOFUS 3',
                        f'{result[0]} équipements et {result[1]} caractéristiques théoriques importés.',parent=self)
                self.after(0,show_success)
        threading.Thread(target=job,daemon=True).start()

    def open_workbench(self):
        """Local workbench, optional tools kept outside of uncluttered dashboard."""
        win=tk.Toplevel(self);win.title('Forgely — Stratégies, données & réussites')
        win.geometry('795x670');win.minsize(690,530);win.configure(bg=BG)
        book=ttk.Notebook(win);book.pack(fill='both',expand=True,padx=13,pady=13)
        strategy=tk.Frame(book,bg=PANEL);gallery=tk.Frame(book,bg=PANEL);data=tk.Frame(book,bg=PANEL)
        book.add(strategy,text='Simulation');book.add(gallery,text='Galerie des réussites');book.add(data,text='Données et sauvegarde')
        def add(parent,text,color=FG,size=10):
            w=self.label(parent,text,size,color=color,wraplength=710,justify='left');w.pack(anchor='w',padx=17,pady=(8,3));return w
        def entry(parent,var,width=20):
            e=tk.Entry(parent,textvariable=var,width=width,font=(self.ui_fonts['body'],11),bg=PANEL2,fg=FG,insertbackground=FG,relief='flat',bd=7)
            e.pack(anchor='w',padx=17,pady=4);return e
        add(strategy,'SIMULATEUR — hypothèses, pas statistiques du jeu',GOLD)
        add(strategy,'Les fréquences saisies sont uniquement des scénarios hypothétiques. Aucune simulation ne rejoint les observations.',MUTED)
        prune=tk.StringVar(value=self.rune.get() or 'Vi')
        add(strategy,'Rune à simuler')
        ttk.Combobox(strategy,values=sorted(RUNES),textvariable=prune,state='readonly',width=25).pack(anchor='w',padx=17,pady=7)
        prob=tk.StringVar(value='0.20');count=tk.StringVar(value='1000')
        line=tk.Frame(strategy,bg=PANEL);line.pack(fill='x',padx=17)
        for lab,var in [('SC supposé (0 à 1)',prob),('Nombre d’essais',count)]:
            self.label(line,lab,10,color=MUTED).pack(side='left',padx=(0,7))
            tk.Entry(line,textvariable=var,width=8,bg=PANEL2,fg=FG,insertbackground=FG).pack(side='left',padx=(0,14))
        def simulate():
            try:
                p=float(prob.get());n=int(count.get());
                if not 0<=p<=1:raise ValueError('SC doit être entre 0 et 1')
                result=illustrative_scenario(prune.get(),n,0,p,0,1-p)
                messagebox.showinfo('Simulation illustrative',f'{n} essais hypothétiques\nSC {result["counts"]["SC"]}\n'
                    f'EC {result["counts"]["EC"]}\n'
                    'Aucun résultat ajouté aux statistiques réelles.',parent=win)
            except (ValueError,TypeError) as exc:messagebox.showerror('Simulation',str(exc),parent=win)
        self.button(strategy,'Simuler ces hypothèses',simulate).pack(anchor='w',padx=17,pady=10)
        from forgely_simulation_ui import mount_simulator
        mount_simulator(self,strategy,win)
        add(gallery,'GALERIE DES JETS RÉUSSIS',GOLD,13)
        add(gallery,'Une fiche peut être préparée seulement si toutes les caractéristiques cibles sont atteintes et le jet stable vérifié. Aucune publication Internet.',MUTED)
        state_label=add(gallery,'Vérification du jet...',GOLD)
        table=ttk.Treeview(gallery,columns=('date','item','stats'),show='headings',height=10)
        for col,label,w in [('date','Date (UTC)',175),('item','Équipement',200),('stats','Objectifs atteints',330)]:
            table.heading(col,text=label);table.column(col,width=w)
        table.pack(fill='both',expand=True,padx=17,pady=12)
        def reload_gallery():
            for child in table.get_children():table.delete(child)
            for record in list_successes():
                summary=', '.join(f'{k}: {v:g}' for k,v in record['actual'].items())
                table.insert('', 'end',values=(record['date'][:19],record['item'],summary))
            ok,why=verify_goal(self.plan,self.item.get(),self.live_jet,self.live_pool,
                self.active_equipment_verified,not self.live_after_fusion)
            state_label.configure(text=('✓ Prêt à créer une carte locale' if ok else 'Pas encore éligible : '+why),fg=GREEN if ok else GOLD)
            return ok
        def publish_local():
            if not reload_gallery():return
            try:
                save_success(self.plan,self.item.get(),self.live_jet,self.live_pool,
                             self.active_equipment_verified,not self.live_after_fusion)
                reload_gallery()
                messagebox.showinfo('Réussite enregistrée','Carte ajoutée à la galerie locale. Aucune donnée envoyée.',parent=win)
            except ValueError as exc:messagebox.showerror('Validation',str(exc),parent=win)
        bar=tk.Frame(gallery,bg=PANEL);bar.pack(fill='x',padx=17,pady=8)
        self.button(bar,'✓ Ajouter ma réussite',publish_local,True).pack(side='left',padx=(0,8))
        self.button(bar,'Actualiser',reload_gallery).pack(side='left')
        def export_cards():
            file=filedialog.asksaveasfilename(parent=win,title='Exporter les cartes locales',defaultextension='.json',filetypes=[('JSON','*.json')])
            if file:
                n=export_gallery_json(file)
                messagebox.showinfo('Export',f'{n} carte(s) exportée(s). Aucune donnée publiée.',parent=win)
        self.button(gallery,'Exporter les cartes JSON (partage manuel)',export_cards).pack(anchor='w',padx=17,pady=(0,12))
        reload_gallery()
        add(data,'EXPORT ET SAUVEGARDE',GOLD,13)
        add(data,'Tous les fichiers restent sur cet ordinateur. Les captures et les noms de personnage ne sont pas inclus dans les exports.',MUTED)
        def ask_file(title,ext):return filedialog.asksaveasfilename(parent=win,title=title,defaultextension=ext,filetypes=[(ext.upper(),'*'+ext)])
        def dump_obs():
            path=ask_file('Exporter les tentatives réelles','.csv')
            if path:messagebox.showinfo('Export',f'{export_observations_csv(path)} ligne(s) exportée(s)',parent=win)
        def dump_summary():
            path=ask_file('Exporter les tableaux par équipement','.csv')
            if path:messagebox.showinfo('Export',f'{export_item_summary(path)} ligne(s) exportée(s)',parent=win)
        def backup():
            path=ask_file('Sauvegarder Forgely','.zip')
            if path:
                try:backup_local(path);messagebox.showinfo('Sauvegarde','Archive créée localement.',parent=win)
                except Exception as exc:messagebox.showerror('Erreur',str(exc),parent=win)
        def bounds():
            path=filedialog.askopenfilename(parent=win,title='Importer jets naturels vérifiés',filetypes=[('CSV','*.csv')])
            if not path:return
            try:
                n=import_bounds_csv(path)
                messagebox.showinfo('Jets naturels',f'{n} caractéristiques importées.\nVérifie les sources avant de les utiliser.',parent=win)
            except Exception as exc:messagebox.showerror('CSV non valide',str(exc),parent=win)
        self.button(data,'Exporter toutes les tentatives (CSV)',dump_obs).pack(anchor='w',padx=17,pady=8)
        self.button(data,'Exporter un tableau par item (CSV)',dump_summary).pack(anchor='w',padx=17,pady=8)
        self.button(data,'Sauvegarder données + préférences (ZIP)',backup,True).pack(anchor='w',padx=17,pady=8)
        self.button(data,'Importer des jets naturels vérifiés (CSV)',bounds).pack(anchor='w',padx=17,pady=8)
        def update_public_refs():
            if not messagebox.askyesno('Référentiel DOFUS 3',
                'Télécharger les jets théoriques publics depuis Dofusdude ?\n'
                'Connexion Internet requise. Les jets réels ne seront jamais remplacés.',parent=win):return
            def job():
                try: result=download_references()
                except Exception as exc:
                    self.after(0,lambda msg=str(exc):messagebox.showerror('Référentiel DOFUS 3',
                        'Import impossible : '+msg,parent=win))
                else:
                    self.after(0,lambda:messagebox.showinfo('Référentiel DOFUS 3',
                        f'{result[0]} équipements et {result[1]} caractéristiques théoriques importés.',parent=win))
            threading.Thread(target=job,daemon=True).start()
        self.button(data,'Actualiser les jets théoriques DOFUS 3 (Internet)',update_public_refs).pack(anchor='w',padx=17,pady=8)
        add(data,'Format CSV des jets naturels : equipement,statistique,min,max. Ne pas importer une liste supposée exhaustive.',MUTED)
        add(data,'Statistiques communautaires : futur serveur opt-in et contrôle anti-doublon. Rien n’est envoyé dans cette version.',GOLD)

    def show_dashboard(self): pass

    def open_equipment_quick(self):
        popup=tk.Toplevel(self)
        popup.title('Forgely - Identification de l’objet')
        popup.configure(bg=BG)
        popup.geometry('510x300')
        self.label(popup,'Comment identifier ton objet ?',18,bold=True).pack(anchor='w',padx=20,pady=18)
        self.label(popup,'Automatique : Forgely lit le nom et le logo dans DOFUS.\n'
            'Manuelle : choisis ton objet dans le catalogue, puis ton jet cible.',
            11,color=MUTED,wraplength=460,justify='left').pack(anchor='w',padx=20,pady=(0,15))
        def choose(mode):
            self.set_equipment_mode(mode)
            popup.destroy()
            if mode=='manual':self.open_equipment_picker()
        self.button(popup,'Détection automatique',lambda:choose('automatic')).pack(fill='x',padx=20,pady=5)
        self.button(popup,'Sélection manuelle de l’objet',lambda:choose('manual'),primary=True).pack(fill='x',padx=20,pady=5)

    def set_equipment_mode(self,mode):
        """Changing identity source starts a fresh, unverified workshop context."""
        if mode not in ('manual','automatic'):
            raise ValueError('Mode d’identification inconnu')
        if self.running:self.toggle_observer()
        picker=getattr(self,'equipment_picker',None)
        if picker is not None and picker.winfo_exists():picker.close()
        self.equipment_picker=None
        self.equipment_mode.set(mode)
        self.manual_equipment=None
        self.measured_goals=MeasuredGoals()
        self.perfect_goal_checked.set(False)
        self.goal_mode.set('')
        self.current_slot_tracker=CurrentSlotTracker()
        self.item_visual_tracker.reset()
        self.workshop_readings.reset();clear_fusion_pairing(self)
        clear_fusion_pairing(self);self.active_equipment_verified=False
        self._verified_item_context=None
        self.item_selection_source='none'
        self.item.set('')
        self.last_item_candidate=''
        self.live_jet=None;self.live_pool=None;self.live_after_fusion=True
        self.pending_transition=None;self.pre_fusion_sample=None
        self.before_identity_reading=None;self.item_initial_reading=None
        self.provisional_slot_id=None
        self.trusted_history_name=None;self.trusted_history_generation=None
        self.item_icon_status=('Détection automatique : démarre l’observation.' if mode=='automatic'
                               else 'Sélection manuelle : choisis ton objet et ton jet cible.')
        self.status.set(self.item_icon_status)
        self.render_plan();self.refresh_strategy()

    def open_equipment_picker(self,goals_only=False,floating=False):
        if goals_only and goal_editor_jet(self) is not None:
            self.prompt_measured_goals()
            return
        from forgely_equipment_picker import EquipmentPicker
        from forgely_equipment_catalog import EquipmentCatalog
        picker=getattr(self,'equipment_picker',None)
        if (picker is not None and picker.winfo_exists() and goals_only and
            self.equipment_mode.get()=='automatic' and
            (not self.active_equipment_verified or
             key_for(getattr(getattr(picker,'selected',None),'identity_name',''))!=key_for(self.item.get()))):
            picker.close();self.equipment_picker=None;picker=None
        if picker is not None and picker.winfo_exists():
            if floating:
                picker.transient(self.overlay)
                picker.attributes('-topmost',True)
            picker.deiconify();picker.lift();return
        session=getattr(self,'manual_equipment',None)
        selected_id=session.equipment.item_id if isinstance(session,ManualEquipmentSession) else None
        if goals_only and self.equipment_mode.get()=='automatic':
            if not self.active_equipment_verified:
                messagebox.showinfo('Jet cible','Attends que Forgely confirme l’objet dans DOFUS, puis ouvre Jet cible.',parent=self.overlay if floating else self)
                return
            matches=[item for item in EquipmentCatalog().items
                     if key_for(item.identity_name)==key_for(self.item.get())]
            if len(matches)!=1:
                messagebox.showinfo('Jet cible','L’objet détecté ne correspond pas à une fiche unique du catalogue. '
                    'Attends une identification complète ou utilise la sélection manuelle.',parent=self.overlay if floating else self)
                return
            detected_name=self.item.get()
            def save_detected_goals(equipment,values,start=False):
                self.commit_automatic_goals(equipment,values,start,detected_name=detected_name)
            self.equipment_picker=EquipmentPicker(self,THEMES[self.theme_name],
                save_detected_goals,selected_id=matches[0].item_id,
                goals_only=True,lock_equipment=True,floating=floating)
            return
        self.equipment_picker=EquipmentPicker(self,THEMES[self.theme_name],
            self.commit_equipment_selection,selected_id,goals_only,floating=floating)

    def commit_automatic_goals(self,equipment,values,start=False,*,detected_name=None):
        """Save targets for the independently detected item without rebinding it."""
        from forgely_equipment_catalog import EquipmentCatalog
        # Opening a Forgely window takes focus from DOFUS and temporarily
        # invalidates live readings. Targets can still be saved for the item
        # confirmed when the editor opened; this never revalidates its jet.
        if (self.equipment_mode.get()!='automatic'
                or (not self.active_equipment_verified and detected_name is None)
                or (detected_name is not None and key_for(detected_name)!=key_for(equipment.identity_name))
                or key_for(self.item.get())!=key_for(equipment.identity_name)
                or EquipmentCatalog().get(equipment.item_id)!=equipment):
            raise ValueError('L’objet ou le mode a changé. Rouvre Jet cible pour l’objet actuellement détecté.')
        self.plan=save_plan(self.item.get(),values,item_id=equipment.item_id,level=equipment.level)
        measured=getattr(self,'measured_goals',None)
        if isinstance(measured,MeasuredGoals) and measured.targets:
            measured.targets={k:v['target'] for k,v in self.plan['stats'].items()}
        enable_copilot_for_goals(self)
        self.perfect_goal_checked.set(False)
        self.goal_mode.set('')
        self.status.set('Jet cible enregistré pour '+equipment.name+' · Détection automatique conservée')
        self.render_plan();self.refresh_strategy()
        if start and not self.running:self.after(0,self.toggle_observer)

    def commit_measured_goals(self,targets,jet,revision,*,allowed=()):
        """Keep the slot-bound target and the named equipment plan identical."""
        session=self.measured_goals
        previous=session.targets
        session.save(targets,jet,revision,allowed=allowed)
        equipment=session.equipment
        name=(self.item.get() if self.active_equipment_verified else
              equipment.identity_name if equipment is not None else None)
        if name:
            try:
                values={k:(jet.get(k),v) for k,v in session.targets.items()}
                metadata=({'item_id':equipment.item_id,'level':equipment.level}
                          if equipment is not None else
                          {k:v for k,v in (self.plan or {}).items()
                           if k in ('item_id','level') and key_for((self.plan or {}).get('item',''))==key_for(name)})
                self.plan=save_plan(name,values,**metadata)
            except (ValueError,OSError):
                session.targets=previous
                raise

    def prompt_measured_goals(self):
        jet=goal_editor_jet(self)
        if jet is None:return
        session=self.measured_goals
        if self.overlay.goal_editing:return
        session.prompted=True
        revision=session.revision
        jet=dict(jet)
        from forgely_perfect_goal import perfect_goal,resolve_goal_equipment
        resolve_goal_equipment(self)
        try:allowed=perfect_goal(self)[2]
        except ValueError:allowed={}
        def save(targets):
            Forgely.commit_measured_goals(self,targets,jet,revision,allowed=allowed)
            enable_copilot_for_goals(self)
            perfect=bool(self.perfect_goal_checked.get() and targets==allowed)
            self.goal_mode.set('Jet parfait' if perfect else '')
            self.perfect_goal_checked.set(perfect)
            self.overlay.close_targets()
            self.status.set('Jet souhaité enregistré · conseils automatiques actifs')
            self.render_plan();self.refresh_strategy()
            self.after(100,self.resume_game_after_targets)
        self.overlay.deiconify()
        if session.equipment is not None:
            self.overlay.item_label.configure(text=session.equipment.name)
        existing=(self.plan or {}).get('stats',{}) if self.active_equipment_verified and (self.plan or {}).get('item')==self.item.get() else {}
        defaults=session.targets or {k:v['target'] for k,v in existing.items() if v.get('target') is not None}
        def fill_perfect():
            if not self.perfect_goal_checked.get():return
            try:
                values=perfect_goal(self)[2]
                allowed.update(values)
                self.overlay.goal_panel.fill_targets(values)
            except ValueError as exc:
                self.perfect_goal_checked.set(False)
                self.overlay.goal_panel.error.configure(text=str(exc))
        self.overlay.open_targets(jet,defaults,save,on_perfect=fill_perfect)

    def toggle_perfect_goal(self):
        if self.perfect_goal_checked.get():
            self.apply_perfect_goal()
        else:
            self.goal_mode.set('')
            self.refresh_strategy()

    def resume_game_after_targets(self):
        from forgely_windows import activate_game_window
        handle=getattr(self.capture,'last_handle',None)
        if isinstance(handle,int):activate_game_window(handle)

    def apply_perfect_goal(self):
        from forgely_perfect_goal import perfect_goal
        try:
            name,ident,targets=perfect_goal(self)
            observed=self.live_jet or self.workshop_readings.partial_jet or {}
            values={k:(observed.get(k),v) for k,v in targets.items()}
            plan=save_plan(name,values,item_id=ident)
        except (ValueError,OSError) as exc:
            self.status.set(str(exc))
            self.overlay.show_advice(str(exc),'unknown')
            self.goal_mode.set('')
            self.perfect_goal_checked.set(False)
            return
        self.plan=plan
        measured=getattr(self,'measured_goals',None)
        if isinstance(measured,MeasuredGoals):
            if (measured.icon is not None and self.active_equipment_verified
                    and key_for(self.item.get())==key_for(name)) or (
                    measured.icon is not None and measured.equipment is not None
                    and key_for(measured.equipment.identity_name)==key_for(name)):
                measured.save(targets,observed,measured.revision,allowed=targets)
            else:
                measured.targets={}
        enable_copilot_for_goals(self)
        self.goal_mode.set('Jet parfait')
        self.perfect_goal_checked.set(True)
        self.overlay.close_targets()
        self.status.set('Jet parfait enregistré pour '+name+' · toutes les caractéristiques au maximum théorique')
        self.render_plan();self.refresh_strategy()
        self.after(100,self.resume_game_after_targets)

    def commit_equipment_selection(self,equipment,values,start=False):
        from forgely_equipment_catalog import EquipmentCatalog
        official=EquipmentCatalog().get(equipment.item_id)
        if official!=equipment:raise ValueError('Équipement absent du catalogue.')
        plan=save_plan(equipment.identity_name,values,item_id=equipment.item_id,level=equipment.level)
        enable_copilot_for_goals(self)
        resume_observation=bool(self.running or start)
        if self.running:self.toggle_observer()
        register_item(equipment.identity_name)
        self.plan=plan
        self.equipment_mode.set('manual')
        self.measured_goals=MeasuredGoals()
        self.perfect_goal_checked.set(False)
        self.goal_mode.set('')
        self.manual_equipment=ManualEquipmentSession(equipment)
        self.current_slot_tracker=self.manual_equipment.tracker
        self.item.set(equipment.identity_name)
        self.item_selection_source='manual'
        clear_fusion_pairing(self);self.active_equipment_verified=False
        self._verified_item_context=None
        self.live_jet=None;self.live_pool=None;self.live_after_fusion=True
        self.pending_transition=None;self.pre_fusion_sample=None
        self.workshop_readings.reset();clear_fusion_pairing(self);self.item_visual_tracker.reset()
        self.current_slot_status=self.manual_equipment.reason
        self.item_icon_status='Objet choisi : '+equipment.name
        self.last_item_candidate=''
        self.last_item_ocr_text=''
        self._item_header_cache=None
        self.status.set('Objet et jet souhaité enregistrés. Place le même objet dans DOFUS, puis démarre la session.')
        self.render_plan();self.refresh_stats_now();self.refresh_strategy()
        if resume_observation:self.after(0,self.toggle_observer)

    def process_manual_equipment(self,slot_icon,signature,source_context,frame_id):
        session=self.manual_equipment
        from forgely_continuous_identity import prime_slot_tracker
        prime_slot_tracker(session.tracker,getattr(self,'fast_slot_evidence',None),
                           slot_icon,source_context,forgely_perf_ns())
        ready=session.observe(slot_icon,signature)
        self.current_slot_status=session.reason
        self.item_icon_status=session.reason
        self.active_equipment_verified=ready
        self.item_selection_source='manual'
        if not ready:
            if slot_icon is None:
                self.workshop_readings.reset();clear_fusion_pairing(self)
            self._verified_item_context=None
            self.live_jet=None;self.live_pool=None;self.live_after_fusion=True
            if session.invalidated:
                self.pending_transition=None
                self.workshop_readings.reset();clear_fusion_pairing(self)
                self.status.set(session.reason)
            elif slot_icon is not None:
                getattr(self,'confirmation_requested',threading.Event()).set()
        else:
            bind_confirmed_equipment(self,session.equipment.identity_name,
                                     slot_icon,signature,source_context,frame_id)
        self.render_plan();self.refresh_strategy()

    def show_item_table(self, name):
        if not name or not find_item(name):
            messagebox.showinfo('Fiche équipement','Équipement non encore reconnu automatiquement.');return
        popup=tk.Toplevel(self);popup.title('Forgely — Tableau de '+name)
        popup.configure(bg=BG);popup.geometry('715x480')
        self.label(popup,name,19,bold=True).pack(anchor='w',padx=20,pady=(17,8))
        n,counts=stats(item=name)
        self.label(popup,f'{n} tentatives · SC {counts["SC"]} · SN {counts["SN"]} · EC {counts["EC"]}',
                   11,color=GOLD).pack(anchor='w',padx=20,pady=(0,10))
        columns=('Date','Rune','Résultat','Source')
        table=ttk.Treeview(popup,columns=columns,show='headings',height=14)
        for c in columns: table.heading(c,text=c)
        table.column('Date',width=170);table.column('Rune',width=160)
        table.column('Résultat',width=95);table.column('Source',width=150)
        table.pack(fill='both',expand=True,padx=20,pady=(0,18))
        for stamp,rune,outcome,source in item_history(name):
            table.insert('', 'end', values=(stamp[:19].replace('T',' '),rune,outcome,source))

    def show_history(self):
        popup=tk.Toplevel(self);popup.title('Forgely — Mes tentatives locales');popup.configure(bg=BG);popup.geometry('760x430')
        self.label(popup,'Historique local des tentatives classées ou observées',17,bold=True).pack(anchor='w',padx=20,pady=16)
        box=tk.Text(popup,bg=PANEL,fg=FG,insertbackground=FG,font=('Consolas',11),relief='flat',padx=15,pady=12)
        box.pack(fill='both',expand=True,padx=20,pady=(0,20))
        rows=recent(100)
        rows += [(date,item or 'Objet non attribué','—','À déterminer','icône · résultat non classé')
                 for date,item in activity_recent(100)]
        rows=sorted(rows,key=lambda row:row[0],reverse=True)[:100]
        if not rows: box.insert('end','Aucune tentative enregistrée pour le moment.')
        for date,item,rune,outcome,source in rows:
            box.insert('end',f'{date[:16].replace("T","  ")}  |  {rune:<9}  |  {outcome}  |  {item[:26]:<26}  |  {source}\n')
        box.configure(state='disabled')

    def show_appearance(self):
        """One visual identity, two workspace sizes."""
        popup=tk.Toplevel(self)
        popup.title('Forgely · Affichage')
        popup.configure(bg=BG)
        popup.geometry('440x290')
        self.label(popup,'Obsidienne',20,bold=True).pack(anchor='w',padx=22,pady=(22,8))
        self.label(popup,'Une interface sombre, deux façons de travailler.',10,color=MUTED).pack(anchor='w',padx=22,pady=(0,18))
        self.button(popup,'Atelier complet',lambda: (popup.destroy(),self.restore()),primary=True).pack(fill='x',padx=22,pady=6)
        self.button(popup,'Copilote compact',lambda: (popup.destroy(),self.minimize_to_badge())).pack(fill='x',padx=22,pady=6)

    def apply_theme(self,name,appearance_popup=None):
        if name not in THEMES:
            return
        old={key:globals()[key] for key in ('BG','PANEL','PANEL2','ACCENT','GOLD','FG','MUTED','GREEN','RED')}
        self.theme_name=name
        set_palette(name)
        save_theme(name)
        translation={old[key]:globals()[key] for key in old}
        def recolor(widget):
            if isinstance(widget,RoundedButton):
                widget.set_palette(THEMES[name])
            elif isinstance(widget,RoundedCard):
                widget._card_color=PANEL
                widget._outer_color=translation.get(widget._outer_color,widget._outer_color)
            try:
                config=widget.configure()
                updates={}
                for prop in ('bg','background','fg','foreground','insertbackground','activebackground','activeforeground','highlightbackground'):
                    if prop in config:
                        value=str(widget.cget(prop))
                        if value in translation and translation[value]!=value:
                            updates[prop]=translation[value]
                if updates: widget.configure(**updates)
            except (tk.TclError,ValueError):
                pass
            if isinstance(widget,RoundedCard):
                widget._redraw_corners()
            for child in widget.winfo_children():
                recolor(child)
        recolor(self)
        if getattr(self, 'dashboard', None) is not None:
            self.dashboard.apply_palette(THEMES[name])
        if appearance_popup and appearance_popup.winfo_exists():
            appearance_popup.destroy()
        # Overlay is recreated only when hidden, to avoid disrupting the current view.
        if hasattr(self,'overlay') and self.overlay.winfo_exists():
            self.overlay.set_theme(THEMES[name])

    def show_window_picker(self):
        popup=tk.Toplevel(self)
        popup.title('Forgely — Choisir la fenêtre du jeu')
        popup.configure(bg=BG)
        popup.geometry('650x380')
        self.label(popup,'Choisir la fenêtre DOFUS',17,bold=True).pack(anchor='w',padx=18,pady=(14,6))
        self.label(popup,'Sélectionne la fenêtre du jeu, même si son titre ne contient pas DOFUS.',
                   10,color=MUTED,wraplength=600).pack(anchor='w',padx=18)
        entries=[]
        selection=tk.StringVar()
        picker=ttk.Combobox(popup,textvariable=selection,state='readonly',width=75)
        picker.pack(fill='x',padx=18,pady=14)
        status=self.label(popup,'',10,color=MUTED,wraplength=590)
        status.pack(anchor='w',padx=18)
        def refresh():
            nonlocal entries
            try:
                entries=list_selectable_windows()
                names=[f'{w.title[:72]}  [{w.width}×{w.height}]  (ID {w._hWnd})' for w in entries]
                picker.configure(values=names)
                if names:
                    picker.current(next((i for i,w in enumerate(entries)
                        if getattr(w,'_hWnd',None)==self.capture.manual_handle),0))
                    status.configure(text=f'{len(entries)} fenêtre(s) disponible(s).')
                else:
                    selection.set('');status.configure(text='Aucune fenêtre disponible : ouvre DOFUS puis actualise.')
            except Exception as exc:
                status.configure(text='Impossible de lister les fenêtres : '+str(exc))
        def apply():
            idx=picker.current()
            if idx < 0 or idx >= len(entries):
                messagebox.showwarning('Forgely','Choisis une fenêtre dans la liste.',parent=popup)
                return
            w=entries[idx]
            self.capture.manual_handle=w._hWnd
            self.capture.last_handle=w._hWnd
            self.window_name.set(w.title)
            self.capture.workshop_handle=w._hWnd
            self.status.set('Fenêtre verrouillée : '+w.title+' · surveillance automatique')
            popup.destroy()
        actions=tk.Frame(popup,bg=BG)
        actions.pack(fill='x',padx=18,pady=10)
        self.button(actions,'Actualiser',refresh).pack(side='left',padx=(0,8))
        self.button(actions,'Utiliser cette fenêtre',apply,primary=True).pack(side='left')
        def automatic():
            self.capture.manual_handle=None
            self.capture.last_handle=None
            self.capture.workshop_handle=None
            self.window_name.set('Détection automatique')
            self.status.set('Détection automatique réactivée')
            popup.destroy()
        self.button(popup,'Revenir à la détection automatique',automatic).pack(anchor='w',padx=18,pady=8)
        self.label(popup,'Mode automatique : Forgely recherche le compte avec un atelier visible ou capturable. Une fenêtre masquée peut ne pas être lisible.',
                   9,color=MUTED,wraplength=600).pack(anchor='w',padx=18)
        refresh()

    def show_settings(self):
        popup=tk.Toplevel(self);popup.title('Forgely — Paramètres locaux');popup.configure(bg=BG);popup.geometry('520x470')
        from forgely_tools import read_settings, save_settings, price_reference_label
        from forgely_rules import MODES
        settings=read_settings()
        self.label(popup,'Conseils vers le jet souhaite',17,bold=True).pack(anchor='w',padx=20,pady=(17,8))
        economic_mode=tk.StringVar(value=settings['strategy'])
        choice=ttk.Combobox(popup,textvariable=economic_mode,values=MODES,state='readonly')
        choice.pack(fill='x',padx=20)
        choice.bind('<<ComboboxSelected>>',lambda event: save_settings({'strategy':economic_mode.get()}))
        self.label(popup,'Objectif : atteindre toutes les cibles. Les prix sont exclus du conseil.',10,color=MUTED,wraplength=470).pack(anchor='w',padx=20)
        self.label(popup,'Paramètres de capture',17,bold=True).pack(anchor='w',padx=20,pady=(17,12))
        self.label(popup,'Fenêtre actuelle : '+self.window_name.get(),10,color=MUTED,wraplength=470).pack(anchor='w',padx=20)
        self.button(popup,'Choisir la fenêtre DOFUS',lambda: open_option_and_close_menu(self.show_window_picker),primary=True).pack(fill='x',padx=20,pady=10)
        self.label(popup,'OCR : Tesseract avec le français et l’anglais.',10,color=MUTED).pack(anchor='w',padx=20)
        self.label(popup,'Capture locale uniquement, sans envoi réseau.',10,color=GREEN).pack(anchor='w',padx=20,pady=8)
        self.label(popup,'Base : '+str(DB_FILE),9,color=MUTED,wraplength=470).pack(anchor='w',padx=20)

    def show_ocr_diagnostic(self):
        popup=tk.Toplevel(self)
        popup.title('Forgely — Diagnostic OCR en direct')
        popup.configure(bg=BG)
        popup.geometry('850x680')
        self.label(popup,'Diagnostic de lecture',18,bold=True).pack(anchor='w',padx=20,pady=(16,5))
        self.label(popup,'État explicable, sans pourcentage de fiabilité inventé. Aucune image sauvegardée automatiquement.',
                   10,color=MUTED,wraplength=800).pack(anchor='w',padx=20,pady=(0,10))
        health=tk.Label(popup,bg=PANEL,fg=GOLD,font=(self.ui_fonts['display'],12,'bold'),anchor='w',padx=12,pady=8)
        health.pack(fill='x',padx=20)
        box=tk.Text(popup,bg=PANEL,fg=FG,font=('Consolas',10),wrap='word',padx=14,pady=12)
        box.pack(fill='both',expand=True,padx=20,pady=10)
        footer=tk.Frame(popup,bg=BG)
        footer.pack(fill='x',padx=20,pady=(0,16))
        def content():
            raw_effects=self.last_ocr_text.partition('\nEFFETS\n')[2].partition('\nRUNES (Pa / Ra)\n')[0]
            raw_jet=parse_jet(raw_effects)
            profile=compare_theoretical_profile(self.item.get() if self.active_equipment_verified or isinstance(getattr(self,'manual_equipment',None),ManualEquipmentSession) else '',raw_jet)
            report=evaluate_ocr(self.last_ocr_text,running=self.running,
                item_verified=self.active_equipment_verified,
                jet_verified=self.live_jet is not None and self.live_pool is not None,
                observation_delay_ms=self.last_observation_delay_ms,
                rune_zone_read=False)
            proposal=getattr(self,'current_proposal',None)
            lines=['ÉTAT : '+report.level,
                   'CONSEIL : '+(getattr(proposal,'summary','') or 'Non calculé'),
                   'MOTIF CONSEIL : '+(getattr(proposal,'explanation','') or 'Aucun résultat du moteur disponible'),
                   'FENÊTRE : '+(self.last_capture_title or 'Non détectée'),
                   'CAPTURE : '+self.capture.debug_stage,
                   'TESSERACT : '+ocr_engine_status(),
                   'PIPELINE NUMÉRIQUE : '+('indépendant v1' if getattr(self,'_numeric_worker_enabled',False) is True else 'observateur commun'),
                   'PERFORMANCES NUMÉRIQUES INDÉPENDANTES (ms) : '+repr(
                       getattr(self,'numeric_performance_tracker',None).snapshot()
                       if isinstance(getattr(self,'numeric_performance_tracker',None),PerformanceTracker) else {}),
                   'MOTIF OBSERVATEUR : '+self.last_reason,
                   'LECTURE RAPIDE (PROVISOIRE) : '+getattr(self, 'fast_preview_reason', 'Non démarrée'),
                   'DÉTAILS LECTURE RAPIDE : '+repr(getattr(self, 'fast_preview_details', {})),
                   'PERFORMANCES LECTURE RAPIDE (ms) : '+repr(self.fast_preview_performance.snapshot() if hasattr(self, 'fast_preview_performance') else {}),
                   'LECTURES : '+str(self.scan_count),
                   'RETARD DERNIÈRE OBSERVATION : '+(f'{self.last_observation_delay_ms:.0f} ms' if self.last_observation_delay_ms is not None else 'Non mesuré'),
                   'RETARD DERNIÈRE LECTURE NUMÉRIQUE : '+(f'{self.last_numeric_delay_ms:.0f} ms' if getattr(self,'last_numeric_delay_ms',None) is not None else 'Non mesuré'),
                   'LECTURE ZONE RUNES : Non demandée par le lecteur principal ; suivi séparé dans l’historique',
                   'CAPTURES AVEC INFOBULLE SUSPECTÉE : '+str(self.occluded_observations),
                   'CAPTURES INCHANGÉES SANS OCR : '+str(getattr(self,'_unchanged_frames_skipped',0)),
                   'CHANGEMENTS VISUELS OBSERVÉS : '+str(getattr(self,'_visual_changes_seen',0)),
                   'FILTRE RAPIDE : comparaison tolérante dans le thread de capture (120 ms)',
                   'CAPTURES MASQUÉES ÉCARTÉES : '+str(getattr(self,'_occluded_frames_rejected',0)),
                   'OCR CADENCE SÉCURITÉ : 12 s sans changement visuel',
                   'OCR SUR IMAGE ANCIENNE (> 1 s) : '+str(getattr(self,'_ocr_stale_frames',0)),
                   'ÂGE DERNIÈRE IMAGE APRÈS OCR : '+str(getattr(self,'_last_ocr_frame_age_ms',None))+' ms',
                   'LECTURES NUMÉRIQUES REJETÉES (SOURCE MODIFIÉE) : '+str(getattr(self,'_numeric_reads_rejected',0)),
                   'MOTIFS REJETS NUMÉRIQUES : '+repr(getattr(self,'_numeric_rejection_reasons',{})),
                   'CONFIRMATIONS JET / PUITS : '+repr((self.workshop_readings.jet_streak,self.workshop_readings.pool_streak)),
                   'ATTENTE NUMÉRIQUE : '+str(self.workshop_readings.waiting_reason or 'Lecture stabilisée'),
                   'PERFORMANCES p50/p95 (ms) : '+repr({k:(round(v['p50'],1),round(v['p95'],1)) for k,v in getattr(self,'performance_tracker',PerformanceTracker()).snapshot().items()}),
                   'ÉQUIPEMENT : '+(self.item.get() if self.active_equipment_verified else 'Non confirmé'),
                   'OBJET CHOISI DANS FORGELY : '+(self.item.get() or 'aucun'),
                   'MODE IDENTIFICATION : '+self.equipment_mode.get(),
                   'JET OCR INSTANTANÉ (NON STABILISÉ) : '+repr(raw_jet),
                   'LIGNE ENCADRÉE (OCR) : '+repr(__import__('forgely_jet').LAST_HIGHLIGHT_DIAGNOSTIC),
                   'JET PROVISOIRE : '+(repr(self.workshop_readings.jet) if self.workshop_readings.jet is not None else 'En cours de stabilisation'),
                   'JET PARTIEL STABILISÉ (DIAGNOSTIC UNIQUEMENT) : '+(repr(self.workshop_readings.partial_jet) if self.workshop_readings.partial_jet is not None else 'En cours de stabilisation'),
                   'PUITS PROVISOIRE : '+(str(self.workshop_readings.pool) if self.workshop_readings.pool is not None else 'En cours de stabilisation'),
                   'PUITS PARTIEL STABILISÉ (DIAGNOSTIC UNIQUEMENT) : '+(str(self.workshop_readings.partial_pool) if self.workshop_readings.partial_pool is not None else 'Non confirmé'),
                   'PUITS OCR EFFETS / DÉDIÉ : '+repr((parse_reliquat(raw_effects), parse_reliquat(self.last_ocr_text.partition('\nRELIQUAT\n')[2].partition('\nVISION\n')[0]))),
                   'LECTURE AVANT IDENTIFICATION : '+(repr(self.item_initial_reading) if self.item_initial_reading else 'Non associée'),
                   'PHASE : '+('Atelier absent' if not self.workshop_active else 'Équipement confirmé' if self.active_equipment_verified else self.waiting_for_item_label() or 'Identification en cours'),
                   'CONFIRMATIONS NOM/LOGO : '+str(self.item_visual_tracker.count),
                   'LECTURES OCR MANQUANTES (identification logo) : '+str(self.item_visual_tracker.missed),
                   'RÉFÉRENTIEL THÉORIQUE : '+(str(len(profile['expected']))+' caractéristiques attendues (jamais utilisées comme valeurs observées)' if profile['available'] else 'Aucune fiche locale pour cet objet'),
                   'CARACTÉRISTIQUES NON LUES : '+(', '.join(profile['missing']) or 'Aucune manquante dans le profil théorique' if profile['available'] else 'Non évaluables sans profil de référence'),
                   'CARACTÉRISTIQUES HORS JET NATUREL (à vérifier) : '+(', '.join(f'{n}={v} (naturel {lo}–{hi})' for n,v,lo,hi in profile['outside']) or 'Aucune' if profile['available'] else 'Profil indisponible'),
                   'CARACTÉRISTIQUES SUPPLÉMENTAIRES (exo possible, non confirmé) : '+(', '.join(profile['extra']) or 'Aucune' if profile['available'] else 'Profil indisponible'),
                   'ÉQUIPEMENT OCR (ligne de l’objet) : '+repr(self.last_item_ocr_text[:180]),
                   'CANDIDAT OBJET : '+(self.last_item_candidate or 'aucun'),
                   'HISTORIQUE OBJET : '+self.last_history_identity,
                   'DERNIER NOM HISTORIQUE (CANDIDAT NON CONFIRMÉ) : '+str(getattr(self, 'last_history_candidate', None) or 'aucun'),
                   'VARIATIONS HISTORIQUE VISIBLES (NON CERTIFIÉES) : '+repr(__import__('forgely_history_summary').summarize_history(self.last_ocr_text.partition('HISTORIQUE\n')[2].partition('\nEFFETS\n')[0])['recent_changes']),
                   'HISTORIQUE DIFFÉRENTIEL (NON CERTIFIÉ) : '+repr(getattr(self, 'history_delta_diagnostic', {'status': 'en_attente'})),
                   'LOGO OBJET : '+self.item_icon_status,
                   'EMPLACEMENT ACTUEL : '+self.current_slot_status,
                   'FICHE PROVISOIRE : '+str(self.provisional_slot_id or 'aucune'),
                   'V1 / VÉRIFICATIONS MANUELLES (DIAGNOSTIC UNIQUEMENT) : '+repr(getattr(self,'reading_review_status',{})),
                   '', 'POINTS À CONTRÔLER :']
            lines += ['• '+r for r in report.reasons] or ['• Aucune anomalie détectée par les contrôles de présence.']
            lines += ['', 'ZONES OCR (texte brut, non corrigé) :']
            for name,value in report.sections.items():
                lines += ['', name, value or '[aucun texte]']
            return report,'\n'.join(lines)
        def update():
            if not popup.winfo_exists(): return
            report,body=content()
            health.configure(text=report.level,fg=GREEN if not report.reasons else GOLD)
            if not getattr(popup,'_editing',False):
                box.configure(state='normal')
                box.delete('1.0','end');box.insert('1.0',body)
                box.configure(state='disabled')
            popup.after(1500,update)
        def copy_report_and_hide():
            # The timer starts only after Forgely windows have been hidden.
            # A completed workshop observation, not merely an OCR invocation,
            # is required to claim that the post-hide game state was sampled.
            from time import monotonic as _monotonic
            start_scan_count = self.scan_count
            initial_frame_id = self.latest_observation_id
            start_ocr_attempts = getattr(self, 'completed_ocr_attempts', 0)
            popup.destroy()
            for child in list(self.winfo_children()):
                if isinstance(child, tk.Toplevel):
                    try:
                        if child.winfo_exists(): child.withdraw()
                    except tk.TclError:
                        pass
            self.iconify()
            hide_started = _monotonic()
            # Reject frames captured before the windows disappeared.
            initial_frame_id = max(initial_frame_id, getattr(self.frame_mailbox, '_sequence', 0))
            min_wait = 3.0
            max_wait = 12.0
            self.status.set('Diagnostic : fenêtres masquées · attente de lecture DOFUS…')

            def check_and_copy():
                if not self.winfo_exists(): return
                elapsed = _monotonic() - hide_started
                scans = max(0, self.scan_count - start_scan_count)
                # The scan is committed by the worker after its messages are
                # queued; process them before building the final report.
                fresh = scans > 0 and self.latest_observation_id > initial_frame_id
                if elapsed < min_wait or (not fresh and elapsed < max_wait and self.running):
                    self.after(200, check_and_copy)
                    return
                try:
                    # Apply any queued observations on Tk's main thread first.
                    self.process_messages()
                    report_text = content()[1]
                    report_text += ('\n\nDIAGNOSTIC DIFFÉRÉ : %.2f s après masquage' % elapsed)
                    report_text += ('\nOBSERVATIONS TERMINÉES PENDANT ATTENTE : %d' % scans)
                    report_text += ('\nDERNIÈRE IMAGE TRAITÉE : %s' % self.latest_observation_id)
                    report_text += ('\nLECTURES OCR TERMINÉES PENDANT ATTENTE : %d' % max(0, getattr(self,'completed_ocr_attempts',0)-start_ocr_attempts))
                    report_text += ('\nDERNIER RÉSULTAT OCR : %s' % getattr(self,'last_ocr_attempt_reason','Inconnu'))
                    if fresh:
                        report_text += '\nVALIDATION DIAGNOSTIC : observation DOFUS post-masquage terminée'
                    else:
                        report_text += ('\nVALIDATION DIAGNOSTIC : ÉCHEC — aucune observation d’atelier '
                                        'terminée après masquage (délai maximal de 12 s).')
                    self.clipboard_clear()
                    self.clipboard_append(report_text)
                    self.update_idletasks()
                    self.status.set('Diagnostic copié · '+('lecture récente obtenue' if fresh else 'lecture indisponible (voir rapport)')+' · Ctrl+V')
                except tk.TclError:
                    pass

            self.after(200, check_and_copy)
        tk.Button(footer,text='Masquer puis copier après lecture (3–12 s)',command=copy_report_and_hide,
                  bg=ACCENT,fg=FG,relief='flat',padx=12,pady=7).pack(side='left')
        tk.Button(footer,text='Copier seulement',command=lambda: (self.clipboard_clear(),
                  self.clipboard_append(content()[1]),self.update_idletasks()),
                  bg=PANEL2,fg=FG,relief='flat',padx=12,pady=7).pack(side='left',padx=8)
        tk.Button(footer,text='Exporter images OCR (même si atelier NON)',command=self.request_debug_capture,
                  bg=PANEL2,fg=FG,relief='flat',padx=12,pady=7).pack(side='left',padx=10)
        tk.Button(footer,text='Fermer',command=popup.destroy,bg=PANEL2,fg=FG,
                  relief='flat',padx=12,pady=7).pack(side='right')
        update()

    def request_debug_capture(self):
        if not self.running:
            messagebox.showinfo('Diagnostic', 'Démarre l’observateur puis repasse sur DOFUS. Reviens ici pour demander un export.')
            return
        self.capture_debug_requested.set()
        directory = DATA_DIR / 'diagnostics'
        self.status.set('Export en attente : retourne sur DOFUS pour autoriser la capture.')
        messagebox.showinfo('Export OCR demandé',
            'La demande est enregistrée.\n\nClique sur DOFUS et laisse son atelier visible quelques secondes.\n\n'
            'Les images seront enregistrées dans :\n' + str(directory) + '\n\n'
            'Une confirmation apparaîtra lorsque les fichiers seront prêts.')

    def import_catalogue(self):
        """Explicit user action, network only during requested catalogue import."""
        if not messagebox.askyesno('Forgely — Catalogue DOFUS 3',
            'Importer un petit catalogue depuis l’API communautaire DofusDude ?\n\n'
            'Cette opération contacte un service tiers uniquement pour récupérer des icônes. '
            'Aucune capture DOFUS ni donnée personnelle ne sera envoyée.\n\n'
            'Les images appartiennent à leurs ayants droit et la reconnaissance restera expérimentale.'):
            return
        self.status.set('Catalogue : recherche d’icônes sur demande…')
        def worker():
            try:
                result=sync_catalogue(DATA_DIR/'catalogue_dofus3')
                self.messages.put(('catalogue',result))
            except Exception as exc:
                self.messages.put(('catalogue_error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def learn_icon(self):
        """One-time local training from a player-provided screenshot, no network."""
        filename=filedialog.askopenfilename(title='Capture DOFUS montrant la rune sélectionnée',
                    filetypes=[('Captures PNG/JPEG','*.png *.jpg *.jpeg')])
        if not filename:return
        try:
            src=Image.open(filename).convert('RGB')
        except Exception as exc:
            messagebox.showerror('Image',str(exc));return
        popup=tk.Toplevel(self)
        popup.title('Apprentissage local — clique au centre de l’icône de rune')
        popup.configure(bg=BG)
        factor=min(1.0,900/src.width,540/src.height)
        small=src.resize((max(1,int(src.width*factor)),max(1,int(src.height*factor))))
        photo=ImageTk.PhotoImage(small)
        popup._photo=photo
        self.label(popup,'Capture de la fenêtre DOFUS entière : clique sur la rune sélectionnée, puis choisis son nom.',12,bold=True,wraplength=850).pack(pady=8)
        canvas=tk.Canvas(popup,width=small.width,height=small.height,highlightthickness=0)
        canvas.pack(padx=12,pady=8)
        canvas.create_image(0,0,image=photo,anchor='nw')
        row=tk.Frame(popup,bg=BG);row.pack(pady=8)
        rune=tk.StringVar(value='Vi')
        self.make_combo(row,rune,RUNES).pack(side='left',padx=8)
        state={'xy':None}
        feedback=self.label(popup,'Choisis le centre de la petite icône, pas son texte.',10,color=MUTED)
        feedback.pack(pady=6)
        def click(evt):
            x=round(evt.x/factor);y=round(evt.y/factor)
            state['xy']=(x,y)
            canvas.delete('marker')
            canvas.create_oval(evt.x-6,evt.y-6,evt.x+6,evt.y+6,outline='#66DBA8',width=2,tags='marker')
            feedback.configure(text=f'Position : {x}, {y} · Rune : {rune.get()}')
        canvas.bind('<Button-1>',click)
        def save():
            if state['xy'] is None:
                messagebox.showwarning('Position','Clique sur le centre de l’icône.');return
            try:
                patch=icon_patch(src,*state['xy'])
                self.vision.add(rune.get(),patch)
                self.rune_center=(state['xy'][0]/src.width,state['xy'][1]/src.height)
                (DATA_DIR/'calibration_rune.json').write_text(__import__('json').dumps({
                    'x':self.rune_center[0],'y':self.rune_center[1]}),encoding='utf8')
                self.visual_label.configure(text=f'Vision : {len(self.vision.references)} référence(s), '+
                    f'{len(self.vision.labels())} rune(s) distincte(s) · {rune.get()} ajoutée')
                popup.destroy()
            except Exception as exc:messagebox.showerror('Apprentissage',str(exc))
        self.button(row,'Mémoriser cette rune',save,primary=True).pack(side='left',padx=8)

    def save_floating_preference(self):
        try:
            import json
            DATA_DIR.mkdir(parents=True,exist_ok=True)
            (DATA_DIR/'interface_preferences.json').write_text(
                json.dumps({'auto_floating':bool(self.auto_floating.get())}),encoding='utf8')
        except OSError:
            pass  # The session can still run if preferences cannot be persisted.

    def toggle_observer(self):
        self._copilot_masked=False
        self._icon_replacement=IconReplacement()
        self._confirmed_atelier_read=None
        if self.running:
            self.stop_event.set();self.running=False
            self.frame_mailbox.invalidate('Observation arrêtée')
            self.clear_fast_preview()
            self.observe_button.configure(text='Démarrer l’observation')
            self.overlay.state_color('paused')
            self.status.set('Observation arrêtée · Toutes les données restent locales')
            self.game_state_label.configure(text='● Observateur arrêté',fg=MUTED)
            self.workshop_readings.invalidate()
            self.live_after_fusion=True
            self._verified_item_context=None
            self.refresh_strategy()
            return
        session=getattr(self,'manual_equipment',None)
        automatic=self.equipment_mode.get()=='automatic'
        if not automatic and (not isinstance(session,ManualEquipmentSession) or session.invalidated
                or not self.plan or self.plan.get('item')!=session.equipment.identity_name
                or not self.plan.get('stats')):
            self.open_equipment_quick()
            return
        # A fresh observation session never inherits a previously bound slot.
        if automatic:
            self.manual_equipment=None
            self.current_slot_tracker=CurrentSlotTracker()
        else:
            session.bound=False;session.tracker.reset()
        self.running=True;self.stop_event=threading.Event();self.track=HistoryTransitionTracker(RUNES)
        from forgely_history_delta import HistoryDeltaMonitor
        self.history_delta_monitor=HistoryDeltaMonitor()
        self.history_delta_diagnostic=self.history_delta_monitor.last
        self.workshop_readings.reset();clear_fusion_pairing(self);self.workshop_active=False
        self.first_item_name_seen=False;self.before_identity_reading=None;self.item_initial_reading=None
        self.history_has_attempts=False
        self.live_jet=None;self.live_pool=None;self.live_after_fusion=True;self.pre_fusion_sample=None
        self.last_transition_audit=None
        # Never carry a previous session's verified item into a new capture.
        clear_fusion_pairing(self);self.active_equipment_verified=False
        self.item_selection_source='none' if automatic else 'manual'
        self.item_ocr_last=None;self.item_ocr_streak=0;self.missing_item_frames=0
        self.item_visual_tracker.reset()
        self.current_slot_tracker.reset()
        self.provisional_slot_id=None
        self.trusted_history_name=None
        self.trusted_history_generation=None
        self.current_slot_status='Emplacement non lu'
        self.item_icon_status='En attente de l’objet actuel'
        self.last_item_ocr_text='';self.last_item_candidate=''
        self.last_history_identity='Historique non analysé'
        self.pending_transition=None
        old_capture=self.capture
        self._verified_item_context=None
        self.capture=GameCapture()
        self.capture.manual_handle=old_capture.manual_handle
        self.capture.last_handle=old_capture.last_handle
        self.capture.workshop_handle=old_capture.workshop_handle
        # One-slot mailbox: the producer overwrites obsolete frames instead of
        # allowing a multi-second OCR backlog to accumulate.
        self.frame_mailbox = LatestFrameMailbox()
        self.confirmation_requested = threading.Event()
        self.pool_refresh_requested = threading.Event()
        self.fast_preview_performance = PerformanceTracker()
        self.fast_preview_reason = 'En attente du premier historique stable'
        self.fast_preview_details = {}
        self.last_full_event_frame_id = 0
        self._stable_numeric_frame = None
        self.last_displayed_result_frame_id = 0
        self.fast_preview_visible = False
        # Cache the expensive two-pass item-header OCR while the exact header
        # pixels remain unchanged. Invalidate on every visual change.
        self._item_header_cache = None
        self._item_header_cache_hits = 0
        self._item_header_cache_misses = 0
        self._capture_interval = 0.12
        self._capture_gate_reference = None
        self._capture_gate_last_sent_ns = 0
        self._capture_gate_force_ns = 12_000_000_000
        self._capture_gate_changes = 0
        self._unchanged_frames_skipped = 0
        self._visual_changes_seen = 0
        self._visual_change_to_ocr_ms = None
        self._visual_refresh_interval_ns = 12_000_000_000
        self._occluded_frames_rejected = 0
        self._ocr_stale_frames = 0
        self._numeric_reads_rejected = 0
        self._numeric_rejection_reasons = {}
        self.last_numeric_delay_ms = None
        self._last_ocr_frame_age_ms = None
        self.saved_auto=0
        self.scan_count=0
        self.completed_ocr_attempts=0
        self.last_ocr_attempt_reason='Aucune lecture OCR terminée'
        self.skipped_frames=0
        self.error_frames=0
        self.readable_frames=0
        self.observe_button.configure(text='■  Arrêter')
        self.overlay.state_color('unknown')
        self.status.set('Analyse locale en cours · En attente de l’atelier de FM')
        self._numeric_worker_enabled=True
        threading.Thread(target=self.capture_worker,daemon=True).start()
        threading.Thread(target=self.item_identity_worker,daemon=True).start()
        threading.Thread(target=self.fast_preview_worker,daemon=True).start()
        threading.Thread(target=self.numeric_worker,daemon=True).start()
        threading.Thread(target=self.observer_worker,daemon=True).start()
        if self.auto_floating.get():
            # Defer the transition until the start button callback is finished.
            self.after(150,self.minimize_to_badge)
            self.after(250,self.resume_game_after_targets)

    def capture_worker(self):
        from forgely_runtime_cache import capture_wait
        """Capture independently of slow OCR; keep only the newest frame."""
        stop_event = self.stop_event
        mailbox = self.frame_mailbox
        capture = self.capture
        last_invalid_generation = None
        from forgely_continuous_identity import RapidSlotTracker
        from forgely_atelier import workshop_visual_fallback
        rapid_slot=RapidSlotTracker()
        self.fast_slot_evidence=None
        while not stop_event.is_set():
            try:
                started = forgely_perf_ns()
                im, title = capture.capture()
                if stop_event.is_set():
                    break
                elapsed = forgely_perf_ns() - started
                # This independent fast path runs during slow OCR. Publish only
                # meaningful changes; never accumulate a backlog of screenshots.
                signature = workshop_change_signature(im)
                changed = workshop_significantly_changed(self._capture_gate_reference, signature)
                identity=(title,getattr(capture,'last_handle',None),getattr(im,'size',None))
                context_changed=(getattr(self,'_capture_gate_identity',None) != identity)
                confirmed=getattr(self,'_confirmed_atelier_read',None)
                confirmed_context=(mailbox,title,getattr(capture,'last_handle',None),getattr(im,'size',None))
                has_confirmed=(isinstance(confirmed,ConfirmedAtelierRead)
                               and confirmed.matches(confirmed_context,signature))
                refresh = (not has_confirmed and
                           started - self._capture_gate_last_sent_ns >= self._capture_gate_force_ns)
                confirmation = self.confirmation_requested.is_set()
                if changed or refresh or confirmation or context_changed:
                    if context_changed and getattr(self,'_capture_gate_identity',None) is not None:
                        generation=mailbox.invalidate('Compte, fenêtre ou dimensions DOFUS modifiés')
                        self.messages.put(('capture_invalidated',(mailbox,generation,'Compte, fenêtre ou dimensions DOFUS modifiés')))
                    self._capture_gate_identity=identity
                    self.confirmation_requested.clear()
                    self._capture_gate_reference = signature
                    self._capture_gate_last_sent_ns = started
                    mailbox.publish(im, title, started, elapsed)
                    if changed:
                        self._visual_changes_seen += 1
                        self._capture_gate_changes += 1
                else:
                    self._unchanged_frames_skipped += 1
                try:
                    verified_workshop=workshop_frame_verified(im,
                        (mailbox,mailbox.generation(),title),getattr(self,'_workshop_title_signature',None))
                    notice=(mailbox,mailbox.generation(),title)
                    if verified_workshop and notice!=getattr(self,'_fast_workshop_notice',None):
                        self._fast_workshop_notice=notice
                        self.messages.put(('workshop_detected',notice))
                    self.fast_slot_evidence=rapid_slot.observe(
                        current_icon(im) if verified_workshop else None,
                        (mailbox,mailbox.generation(),title),forgely_perf_ns())
                except Exception:
                    # Optional acceleration must never invalidate a valid OCR
                    # frame. Fall back to normal multi-analysis association.
                    self.fast_slot_evidence=None
                    rapid_slot=RapidSlotTracker()
            except (GameNotForeground, RuntimeError) as exc:
                self.fast_slot_evidence=None
                self._capture_gate_reference = None
                generation=mailbox.invalidate(str(exc))
                if generation != last_invalid_generation:
                    self.messages.put(('capture_invalidated',(mailbox,generation,str(exc))))
                    last_invalid_generation=generation
            except Exception as exc:
                self.fast_slot_evidence=None
                self._capture_gate_reference = None
                reason=type(exc).__name__ + ': ' + str(exc)
                generation=mailbox.invalidate(reason)
                if generation != last_invalid_generation:
                    self.messages.put(('capture_invalidated',(mailbox,generation,reason)))
                    last_invalid_generation=generation
            # The latest-frame mailbox prevents backlog. Faster lightweight
            # capture reduces the age of the frame available after OCR ends.
            elapsed=max(0.,(forgely_perf_ns()-started)/1_000_000_000)
            stop_event.wait(capture_wait(self._capture_interval,elapsed))
        capture.close()

    def item_identity_worker(self):
        """Identify the current item without waiting for complete atelier OCR."""
        from forgely_item_identity import ItemIdentityReader
        reader=ItemIdentityReader(artwork_only=True)
        mailbox=self.frame_mailbox
        stop_event=self.stop_event
        generation=mailbox.generation()
        last_frame_id=0
        retry_at=None
        last_artwork_key=None
        while not stop_event.is_set() and mailbox is self.frame_mailbox:
            if retry_at is not None and forgely_perf_ns()>=retry_at:
                request=getattr(self,'confirmation_requested',None)
                if request is not None:request.set()
                retry_at=forgely_perf_ns()+1_000_000_000
            current_generation,frame=mailbox.wait_snapshot(last_frame_id,stop_event,generation)
            if current_generation!=generation:
                reader.reset();generation=current_generation;retry_at=None;last_artwork_key=None
            if frame is None:continue
            frame_id,image,title,captured_ns,_=frame
            last_frame_id=frame_id
            try:
                started=forgely_perf_ns()
                confirmed=getattr(self,'_confirmed_atelier_read',None)
                tracker=getattr(self,'current_slot_tracker',None)
                complete_slot=crop_catalogue_slot(image)
                effects_patch=crop_zone(image,'effects')
                bounds_patch=effects_patch.crop((0,0,round(effects_patch.width*.32),effects_patch.height))
                artwork_key=(generation,title,complete_slot.size,complete_slot.tobytes(),
                             bounds_patch.size,bounds_patch.tobytes())
                same_artwork=artwork_key==last_artwork_key
                verified=getattr(self,'_verified_item_context',None)
                if (getattr(self,'active_equipment_verified',False) is True
                        and isinstance(tracker,CurrentSlotTracker) and tracker.icon is not None
                        and isinstance(verified,VerifiedItemContext)
                        and verified.mailbox is mailbox and verified.generation==generation
                        and verified.title==title):
                    visible_icon=current_icon(image)
                    if stop_event.is_set():break
                    if visible_icon is not None and icon_distance(tracker.icon,visible_icon)<=17:
                        # A changed rune selection is not a request to identify
                        # this same object or OCR its characteristics again.
                        retry_at=None
                        continue
                context=(mailbox,title,getattr(getattr(self,'capture',None),'last_handle',None),getattr(image,'size',None))
                if (same_artwork and isinstance(confirmed,ConfirmedAtelierRead)
                        and confirmed.matches(context,workshop_change_signature(image))):
                    retry_at=None
                    continue
                reading=reader.read(image,extract_text,item_list)
                self.fast_preview_performance.record('identification_objet',forgely_perf_ns()-started)
                if reading is None:
                    retry_at=None
                    continue
                self._workshop_title_signature=workshop_title_signature(image,(mailbox,generation,title))
                if reading.catalogue_verified:
                    last_artwork_key=artwork_key
                # Recheck context before publishing; previous-account work is discarded.
                if stop_event.is_set() or generation!=mailbox.generation():continue
                # An unresolved fast name must not consume newer identity frames
                # and starve a successful (slower) full-heading reading.
                if (reading.icon is not None and not reading.known and not reading.candidate
                        and match_current_item(reading.icon,reading.signature) is None):
                    retry_at=forgely_perf_ns()+1_000_000_000
                    continue
                retry_at=None
                if reading.icon is None:
                    tracker=getattr(self,'current_slot_tracker',None)
                    request=getattr(self,'confirmation_requested',None)
                    if tracker is not None and not tracker.absence_confirmed and request is not None:
                        request.set()
                verified=getattr(self,'_verified_item_context',None)
                if bind_event_item(verified,mailbox,generation,title,frame_id,reading.icon,
                                   reading.signature,name_hint=reading.known or reading.candidate):
                    continue
                sink=FrameMessageSink(self.messages,mailbox,generation,title,stop_event)
                sink.put(('identity_observation',(frame_id,captured_ns,'item_visual',
                    (reading.known,reading.candidate,reading.raw,reading.icon,None,None,
                     reading.signature,(),None,None,reading.catalogue_verified))))
            except (OSError,ValueError,RuntimeError,__import__('sqlite3').Error):
                # The complete observer remains a fallback; never reuse failed evidence.
                reader.reset()


    def fast_preview_worker(self):
        """Display provisional results independently of slow effect recovery."""
        from forgely_fast_preview import FastRunePreview
        reader = FastRunePreview(RUNES)
        last_frame_id = 0
        mailbox = self.frame_mailbox
        stop_event = self.stop_event
        generation = mailbox.generation()
        while not stop_event.is_set():
            frame = mailbox.wait_new(last_frame_id, stop_event)
            current_generation = mailbox.generation()
            if generation != current_generation:
                reader.reset()
                generation = current_generation
                self.messages.put(('fast_preview_clear', (last_frame_id, mailbox)))
                continue
            if frame is None:
                continue
            frame_id, image, title, captured_ns, _ = frame
            last_frame_id = frame_id
            try:
                started = forgely_perf_ns()
                confirmed=getattr(self,'_confirmed_atelier_read',None)
                context=(mailbox,title,getattr(getattr(self,'capture',None),'last_handle',None),getattr(image,'size',None))
                exact=(isinstance(confirmed,ConfirmedAtelierRead)
                       and confirmed.matches(context,workshop_change_signature(image)))
                def preview_ocr(patch):
                    zone=patch.info.get('forgely_preview_zone')
                    if exact and zone in ('history','runes'):return getattr(confirmed.atelier,zone)
                    return extract_text(patch)
                result = reader.read(image, title, preview_ocr)
                if generation != mailbox.generation() or stop_event.is_set():
                    reader.reset()
                    continue
                self.fast_preview_performance.record('historique_et_rune', forgely_perf_ns() - started)
                self.fast_preview_reason = reader.reason
                self.fast_preview_details = reader.diagnostic
                if result.context_reset:
                    self.messages.put(('fast_preview_clear', (frame_id, mailbox)))
                if result.needs_confirmation:
                    getattr(self,'confirmation_requested',threading.Event()).set()
                if result.event:
                    self.messages.put(('fast_preview', (frame_id, captured_ns, result.event,
                                                        generation, title, reader.icon, mailbox)))
                elif result.changes:
                    self.messages.put(('fast_changes', (frame_id, captured_ns,
                        (result.changes, result.changes_stable), generation, title, reader.icon, mailbox)))
            except Exception as exc:
                # Failure of an optional preview must not stop the complete
                # observer or reuse a stale reference after OCR failure.
                reader.reset()
                self.messages.put(('fast_preview_clear', (frame_id, mailbox)))
                self.fast_preview_reason = 'Lecture rapide indisponible : ' + str(exc)[:160]

    def numeric_worker(self):
        """Latest-frame numeric lane, independent of history and artwork OCR.

        Exactly the existing source-bound delivery enters the UI guards. The
        OCR backend shares identical in-flight reads with the full observer.
        """
        mailbox=self.frame_mailbox
        stop=self.stop_event
        generation=mailbox.generation()
        last_frame=0
        cache=ZoneCache(refresh_seconds=12.0)
        titles={}
        perf=PerformanceTracker()
        self.numeric_performance_tracker=perf
        while not stop.is_set():
            current_generation,frame=mailbox.wait_snapshot(last_frame,stop,generation)
            if stop.is_set() or mailbox is not self.frame_mailbox:break
            if current_generation!=generation:
                generation=current_generation;cache.clear();titles.clear()
            if frame is None:continue
            frame_id,image,title,started,capture_ns=frame
            last_frame=frame_id
            fresh=False
            numeric_delivered=False
            try:
                identity=getattr(self,'_verified_item_context',None)
                icon=current_icon(image)
                bound=(bind_event_item(identity,mailbox,generation,title,frame_id,
                    icon,identity.signature,self.item.get())
                    if isinstance(identity,VerifiedItemContext) and self.active_equipment_verified else None)
                if not bound:continue
                request=getattr(self,'pool_refresh_requested',None)
                fresh=isinstance(request,threading.Event) and request.is_set()
                if fresh:request.clear();cache.discard('reliquat')
                readings=getattr(self,'workshop_readings',None)
                if isinstance(readings,WorkshopReadings) and readings.expected:
                    from forgely_dofocus import normalise_jet
                    cached=cache.get('current_jet')
                    if cached is not None and not readings.expected.issubset(normalise_jet(parse_jet(cached)) or {}):
                        cache.retry_unresolved('current_jet')
                result=read_atelier(image,extract_text,cache,titles,numeric_only=True,
                    pool_ocr_token=(id(mailbox),generation,frame_id) if fresh else None)
                if stop.is_set() or mailbox is not self.frame_mailbox or generation!=mailbox.generation():continue
                if not result.active or effects_text_occluded(result.effects):
                    cache.clear()
                    continue
                jet=parse_jet(result.effects)
                pool=choose_reliquat(result.effects,result.reliquat)
                if not jet or pool is None:
                    cache.retry_unresolved('current_jet' if not jet else 'reliquat')
                    if fresh:request.set()
                    self.confirmation_requested.set()
                    continue
                # Identity can change while subprocess OCR is running.
                now=getattr(self,'_verified_item_context',None)
                if not isinstance(now,VerifiedItemContext) or bind_event_item(now,mailbox,generation,title,
                        frame_id,icon,now.signature,self.item.get())!=bound:continue
                context=(mailbox,title,getattr(self.capture,'last_handle',None),image.size)
                delivery=ConfirmedAtelierRead(context,workshop_change_signature(image),result,
                    (dict(jet),pool),tuple((z,cache.entries[z]) for z in ('current_jet','reliquat') if z in cache.entries),
                    numeric_signature=numeric_frame_signature(image),complete=False)
                FrameMessageSink(self.messages,mailbox,generation,title,stop).put(
                    ('observation',(frame_id,started,'atelier_read',(jet,pool,delivery))))
                numeric_delivered=True
                perf.record('capture_vers_publication_numerique',forgely_perf_ns()-started)
                for phase,duration in result.timings.items():perf.record(phase,duration)
            except Exception as exc:
                self.numeric_worker_error=str(exc)
                cache.clear()
                self.confirmation_requested.set()
            finally:
                # A masked panel or failed OCR has not satisfied the rune's
                # request. Retry with a fresh backend token on the next frame,
                # without carrying the request into another capture session.
                if (fresh and not numeric_delivered and not stop.is_set()
                        and mailbox is self.frame_mailbox and generation==mailbox.generation()):
                    request.set()

    def observer_worker(self):
        from forgely_attempt_groups import AttemptGroupTracker
        from forgely_history_reader import HistoryReader,VisualHistoryTracker
        visual_history=VisualHistoryTracker(HistoryReader(ocr=extract_text))
        from uuid import uuid4
        attempt_groups=AttemptGroupTracker()
        attempt_session=uuid4().hex
        from forgely_learning import FusionContextTracker
        from forgely_dofocus import natural_profile
        fusion_contexts = FusionContextTracker()
        from forgely_pool_observer import PoolObserver
        pool_observer=PoolObserver()
        pool_cycle=0
        pool_ocr_override=None
        stop_event = self.stop_event
        mailbox = self.frame_mailbox
        capture = self.capture
        missed_workshop = 0
        zone_cache = ZoneCache(refresh_seconds=12.0)
        title_cache = {}
        perf = PerformanceTracker()
        self.performance_tracker = perf
        last_frame_id = 0
        previous_processed_id = 0
        generation = mailbox.generation()
        messages = self.messages
        while not stop_event.is_set():
            try:
                current_generation,frame = mailbox.wait_snapshot(last_frame_id,stop_event,generation)
                if stop_event.is_set() or mailbox is not self.frame_mailbox:
                    break
                if current_generation != generation:
                    generation=current_generation
                    zone_cache.clear();title_cache.clear()
                    self._item_header_cache=None
                    self.track=HistoryTransitionTracker(RUNES)
                    self.history_delta_monitor.reset()
                    missed_workshop=0
                    fusion_contexts.reset()
                    pool_observer.reset()
                    pool_ocr_override=None
                if frame is None:
                    continue
                frame_id, im, title, frame_started_ns, capture_ns = frame
                last_frame_id = frame_id
                messages=FrameMessageSink(self.messages,mailbox,generation,title,stop_event)
                perf.record("capture", capture_ns)
                perf.record("capture_vers_ocr", forgely_perf_ns() - frame_started_ns)
                self.last_capture_title = title
                # The capture worker already filtered noise at 120 ms cadence.
                # Never perform a second exact-hash gate here: it would discard
                # meaningful frames while the OCR worker is occupied.
                # Capture only visible, foreground DOFUS. OCR only cropped areas
                # of the forgemagie workshop (based on supplied DOFUS screenshot).
                t_ocr = forgely_perf_ns()
                visual_context=(mailbox,title,getattr(capture,'last_handle',None),getattr(im,'size',None))
                visual_signature=workshop_change_signature(im)
                confirmed=getattr(self,'_confirmed_atelier_read',None)
                pool_patch=crop_zone(im,'reliquat') if pool_ocr_override is not None else None
                pool_pixels=((pool_patch.size,pool_patch.mode,pool_patch.tobytes())
                             if pool_patch is not None else None)
                if (pool_ocr_override is not None and pool_ocr_override[:2]==(visual_context,pool_pixels)
                        and isinstance(confirmed,ConfirmedAtelierRead)
                        and confirmed.numeric[1]!=pool_ocr_override[2]):
                    # A delayed UI confirmation must not restore the pool
                    # reading that a more recent explicit OCR just corrected.
                    confirmed=None
                    zone_cache.confirm_numeric(())
                if isinstance(confirmed,ConfirmedAtelierRead) and confirmed.context==visual_context:
                    zone_cache.confirm_numeric(confirmed.zones)
                pool_request=getattr(self,'pool_refresh_requested',None)
                fresh_pool=(getattr(self,'_numeric_worker_enabled',False) is not True
                    and isinstance(pool_request,threading.Event) and pool_request.is_set())
                if fresh_pool:
                    pool_request.clear()
                    zone_cache.discard('reliquat')
                # A first OCR pass can omit text during a fusion animation.
                # Retry only an actually missing numeric zone, at most once
                # per second, rather than retaining that omission for 12 s.
                readings=getattr(self,'workshop_readings',None)
                if isinstance(readings,WorkshopReadings) and readings.expected:
                    from forgely_dofocus import normalise_jet
                    cached=zone_cache.get('current_jet')
                    if cached is not None and not readings.expected.issubset(normalise_jet(parse_jet(cached)) or {}):
                        zone_cache.retry_unresolved('current_jet')
                    cached_pool=zone_cache.get('reliquat')
                    if cached_pool is not None and parse_reliquat(cached_pool) is None:
                        zone_cache.retry_unresolved('reliquat')
                numeric_published=False
                def publish_numeric(reading,numeric=None,*,complete=False,zones=None):
                    nonlocal numeric_published
                    if getattr(self,'_numeric_worker_enabled',False) is True:return
                    if (numeric_published or stop_event.is_set() or mailbox is not self.frame_mailbox
                            or generation!=mailbox.generation() or not reading.active
                            or effects_text_occluded(reading.effects)):
                        return
                    numeric=numeric if numeric is not None else (
                        parse_jet(reading.effects),choose_reliquat(reading.effects,reading.reliquat))
                    identity=getattr(self,'_verified_item_context',None)
                    icon=current_icon(im)
                    bound=(bind_event_item(identity,mailbox,generation,title,frame_id,
                        icon,identity.signature,self.item.get())
                        if isinstance(identity,VerifiedItemContext) and self.active_equipment_verified else None)
                    if not bound or not numeric[0] or numeric[1] is None:
                        return
                    if zones is None:
                        zones=tuple((zone,zone_cache.entries[zone]) for zone in ('effects','current_jet','reliquat')
                            if zone in zone_cache.entries and (
                                numeric[1]==choose_reliquat(reading.effects,reading.reliquat) if zone=='reliquat'
                                else numeric[0]==parse_jet(reading.effects)))
                    delivery=ConfirmedAtelierRead(visual_context,visual_signature,reading,
                        (dict(numeric[0]),numeric[1]),zones,
                        numeric_signature=numeric_frame_signature(im),complete=complete)
                    messages.put(('observation',(frame_id,frame_started_ns,'atelier_read',
                        (numeric[0],numeric[1],delivery))))
                    perf.record('capture_vers_publication_numerique',forgely_perf_ns()-frame_started_ns)
                    numeric_published=True
                atelier,reused_reading=read_current_atelier(None if fresh_pool else confirmed,visual_context,visual_signature,
                    lambda:read_atelier(im,extract_text,zone_cache,title_cache,
                        history_ocr=visual_history.reader.latest_text,five_zones=True,
                        pool_ocr_token=(id(mailbox),generation,frame_id) if fresh_pool else None,
                        on_numeric=publish_numeric))
                if stop_event.is_set():
                    break
                if mailbox is not self.frame_mailbox or generation != mailbox.generation():
                    continue
                perf.record("atelier_et_ocr", forgely_perf_ns() - t_ocr)
                for phase,duration in ({} if reused_reading else getattr(atelier,'timings',{})).items():
                    perf.record('atelier_'+phase,duration)
                if getattr(atelier,'recovery_pending',False):
                    getattr(self,'confirmation_requested',threading.Event()).set()
                # This is diagnostic only: never claim a late OCR reading is
                # an instant rune result. A newer frame is already in the mailbox.
                self._last_ocr_frame_age_ms = round((forgely_perf_ns() - frame_started_ns) / 1_000_000, 1)
                if self._last_ocr_frame_age_ms > 1000:
                    self._ocr_stale_frames += 1
                # Count completed OCR passes, including unsuccessful workshop detection.
                # This counter is independent of the Tk message queue and of scans.
                self.completed_ocr_attempts = getattr(self, 'completed_ocr_attempts', 0) + 1
                self.last_ocr_attempt_reason = ('Atelier reconnu' if atelier.active
                                                else 'Lecture du jeu indisponible : ' + atelier.reason)
                self.capture.debug_stage = ('Atelier reconnu · OCR en cours' if atelier.active
                                            else 'Capture OK · titre atelier OCR : '+repr(atelier.title[:70]))
                if self.capture_debug_requested.is_set():
                    self.capture_debug_requested.clear()
                    directory = DATA_DIR / 'diagnostics'
                    directory.mkdir(parents=True, exist_ok=True)
                    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    # Explicit user request only. Save workshop regions, never full screen.
                    for index, candidate in enumerate(title_candidates(im), 1):
                        candidate.save(directory / f'titre_{stamp}_{index}.png')
                    for zone in ('history', 'effects', 'runes', 'reliquat'):
                        crop_zone(im, zone).save(directory / f'{zone}_{stamp}.png')
                    crop_item_header(im).save(directory / f'item_{stamp}.png')
                    (history_icon_for_name(im, self.last_item_candidate) or crop_zone(im, 'history')).save(directory / f'item_logo_historique_{stamp}.png')
                    crop_current_item(im).save(directory / f'item_logo_actuel_{stamp}.png')
                    (directory / f'ocr_{stamp}.txt').write_text(
                        'FENETRE: '+title+'\nCAPTURE: '+self.capture.debug_stage+
                        '\nTITRE OCR: '+repr(atelier.title)+'\nATELIER: '+str(atelier.active)+
                        '\nTESSERACT: '+ocr_engine_status()+
                        '\nEQUIPEMENT OCR: '+repr(self.last_item_ocr_text)+
                        '\nCANDIDAT: '+repr(self.last_item_candidate)+
                        '\nHISTORIQUE OBJET: '+self.last_history_identity+
                        '\nLOGO: '+self.item_icon_status+
                        '\nEMPLACEMENT: '+self.current_slot_status+
                        '\nCONFIRMATIONS: '+str(self.item_visual_tracker.count)+'\n', encoding='utf-8')
                    messages.put(('exported', str(directory)))
                numeric_reading=(confirmed.numeric if reused_reading else
                    (parse_jet(atelier.effects),choose_reliquat(atelier.effects,atelier.reliquat)))
                if fresh_pool:
                    perf.record('relecture_reliquat',getattr(atelier,'timings',{}).get('reliquat',0))
                    pool_patch=crop_zone(im,'reliquat')
                    pool_ocr_override=(visual_context,
                        (pool_patch.size,pool_patch.mode,pool_patch.tobytes()),numeric_reading[1])
                    if getattr(self,'_confirmed_atelier_read',None) is confirmed:
                        self._confirmed_atelier_read=None
                    if numeric_reading[1] is None:
                        pool_request.set()
                        getattr(self,'confirmation_requested',threading.Event()).set()
                # One authoritative numeric reader. Experimental review tools
                # remain available separately and cannot overwrite/block live
                # measurements or delay every frame with a second full reader.
                if not atelier.active or (getattr(atelier,'readable',True) is False and not numeric_reading[0]):
                    visual_history.reset()
                    pool_observer.reset()
                    if atelier.active:
                        capture.reacquire_layout.set()
                        getattr(self,'confirmation_requested',threading.Event()).set()
                        self.last_ocr_attempt_reason=atelier.reason
                        self.last_ocr_text=('HISTORIQUE\n'+atelier.history+'\nEFFETS\n'+atelier.effects+'\nRUNES (Pa / Ra)\n'+atelier.runes+'\nRELIQUAT\n'+atelier.reliquat+'\nVISION\nLecture non exploitable')
                        messages.put(('atelier_masked',atelier.reason))
                    fusion_contexts.reset()
                    zone_cache.clear()
                    missed_workshop += 1
                    if missed_workshop >= 3:
                        # A foreground overlay is not permission to switch to
                        # another account's workshop and discard this item.
                        session=getattr(self,'measured_goals',None)
                        if atelier.active or self.active_equipment_verified or isinstance(session,MeasuredGoals) and session.targets:
                            messages.put(('atelier_masked' if atelier.active else 'atelier_waiting',atelier.reason))
                            continue
                        # Keep the last confirmed account while probing; do not
                        # oscillate between clients on transient OCR failures.
                        # Search other DOFUS accounts only when this workshop is
                        # absent. Avoid mixing their item, rune and pool states.
                        found=self.capture.probe_other_workshops(
                            lambda candidate: read_atelier(candidate,extract_text,
                                ZoneCache(refresh_seconds=12.0),{}).active)
                        if found:
                            title_cache.clear()
                            self._item_header_cache = None
                            self.track=HistoryTransitionTracker(RUNES)
                            self.workshop_readings.reset();clear_fusion_pairing(self)
                            self.pending=None
                            messages.put(('account_switch',found))
                            missed_workshop=0
                            zone_cache.clear()
                            continue
                        self.track=HistoryTransitionTracker(RUNES)
                        self.history_delta_monitor.reset()
                        self.history_delta_diagnostic=self.history_delta_monitor.last
                        messages.put(('atelier_waiting',atelier.reason))
                    continue
                missed_workshop = 0
                if self.capture.manual_handle is None:
                    self.capture.workshop_handle=self.capture.last_handle
                history_text, rune_text = atelier.history, atelier.runes
                # Rune tooltips may overlap the effects table. Never certify
                # a contaminated image as the equipped item's current jet.
                occluded = effects_text_occluded(atelier.effects)
                if occluded:
                    self.occluded_observations += 1
                    self._occluded_frames_rejected += 1
                    # Do not keep a tooltip-contaminated OCR result in cache.
                    zone_cache.discard('effects')
                    zone_cache.discard('current_jet')
                    pool_observer.reset()
                    fusion_contexts.reset()
                    visual_history.reset()
                    self._confirmed_atelier_read=None
                    self.last_ocr_attempt_reason='Lecture masquée : infobulle sur les caractéristiques'
                    self.last_ocr_text=('HISTORIQUE\n'+atelier.history+'\nEFFETS\n'+atelier.effects+
                        '\nMODIFICATIONS\n'+getattr(atelier,'modifications','')+
                        '\nRUNES (Pa / Ra)\n'+atelier.runes+'\nRELIQUAT\n'+atelier.reliquat+
                        '\nVISION\nInfobulle détectée : chiffres non utilisables')
                    messages.put(('atelier_masked','Infobulle sur les caractéristiques · éloigne le pointeur pour relire'))
                    getattr(self,'confirmation_requested',threading.Event()).set()
                    continue
                # Publish the measured jet/pool before artwork matching and
                # history analysis. Those secondary tasks must not hold the
                # numbers back for several seconds on a slower machine.
                t_icon = forgely_perf_ns()
                slot_icon = current_icon(im)
                identity=getattr(self,'_verified_item_context',None)
                early_identity=(bind_event_item(identity,mailbox,generation,title,frame_id,
                    slot_icon,identity.signature,self.item.get())
                    if isinstance(identity,VerifiedItemContext) and self.active_equipment_verified else None)
                publish_numeric(atelier,numeric_reading,complete=True,
                    zones=confirmed.zones if reused_reading else None)
                # Automatic identity comes exclusively from labelled artwork
                # and natural bounds. Never OCR the name/history to guess it.
                signature = ()  # current-slot artwork, never a historical name
                verified_identity=getattr(self,'_verified_item_context',None)
                if (isinstance(verified_identity,VerifiedItemContext)
                        and verified_identity.mailbox is mailbox and verified_identity.generation==generation
                        and verified_identity.title==title and verified_identity.frame_id<=frame_id
                        and slot_icon is not None and icon_distance(verified_identity.icon,slot_icon)<=17):
                    # Reuse only previously verified natural Min/Max evidence.
                    # Mutable current values never contribute to identity.
                    signature=verified_identity.signature
                manual_session=getattr(self,'manual_equipment',None)
                manual_selected=isinstance(manual_session,ManualEquipmentSession)
                visual_name = (early_identity or slot_equipment_decision(im, signature).name
                               if not manual_selected and slot_icon is not None and not occluded else None)
                perf.record("extraction_icone", forgely_perf_ns() - t_icon)
                if manual_selected:
                    found,new_name,item_ocr=None,None,'Nom choisi dans le catalogue Forgely'
                elif visual_name:
                    found,new_name,item_ocr=visual_name,None,'Nom associé au logo dans le catalogue local'
                else:
                    found,new_name,item_ocr=None,None,'Logo inconnu ou ambigu · aucun OCR du nom'
                if stop_event.is_set() or mailbox is not self.frame_mailbox or generation != mailbox.generation():
                    continue
                history_identity = None
                # Read the ACTUAL equipment slot even if the FM history is empty
                # or contains an old item's heading. No game interaction.
                historical_names = []
                latest_history_candidate = None
                # Historical icons are not a source of current-item identity.
                # Their former OCR geometry/visual-row search was discarded by
                # the UI, yet launched expensive subprocesses every cycle.
                # Explicit diagnostic exports can still locate a history icon.
                history_icon = None
                corroborated_history_name = None
                if stop_event.is_set():
                    break
                # The event is detected below after rune OCR. Associate its
                # evidence with this exact frame via a separate message.
                messages.put(('observation', (frame_id, frame_started_ns, 'item_visual', (found, new_name, item_ocr,
                    slot_icon, history_identity, history_icon, signature, historical_names, corroborated_history_name, latest_history_candidate,bool(visual_name)))))
                visual_match=None
                if self.rune_center and self.vision.references:
                    cx,cy=self.rune_center
                    try:
                        visual_match=self.vision.predict(icon_patch(im,cx*im.width,cy*im.height))
                    except ValueError:pass
                # Prefer explicit OCR when it agrees; incompatible OCR/vision -> unknown.
                from runeforge_observer import find_rune
                ocr_rune=find_rune(rune_text,RUNES)
                vision_rune=visual_match.rune if visual_match else None
                if ocr_rune and vision_rune and ocr_rune != vision_rune:
                    selected_rune=''
                    self.track.invalidate_rune()
                    vision_note='CONFLIT OCR / icône : vérification nécessaire'
                else:
                    selected_rune='Rune '+(ocr_rune or vision_rune) if (ocr_rune or vision_rune) else ''
                    if visual_match and not visual_match.rune and not ocr_rune:
                        self.track.invalidate_rune()
                    vision_note=('Icône : '+visual_match.reason if visual_match else 'Vision non calibrée')
                from forgely_history_summary import summarize_history
                history_summary = summarize_history(history_text)
                delta_diagnostic = self.history_delta_monitor.observe(history_text)
                self.history_delta_diagnostic = delta_diagnostic
                raw = ('ANALYSE HISTORIQUE (indicative) : '
                       + str(history_summary['visible_stat_changes'])
                       + ' variations de caractéristiques visibles ; tentative non certifiée\n'
                       + 'HISTORIQUE\n'+history_text+'\nEFFETS\n'+atelier.effects+
                       '\nMODIFICATIONS\n'+getattr(atelier,'modifications','')+
                       '\nRUNES (Pa / Ra)\n'+rune_text+'\nRELIQUAT\n'+atelier.reliquat+'\nVISION\n'+vision_note)
                event = self.track.observe(history_text,selected_rune)
                context_item = bind_event_item(getattr(self,'_verified_item_context',None),
                    mailbox,generation,title,frame_id,slot_icon,signature,found or new_name)
                if not history_summary['has_explicit_outcome'] and slot_icon is not None:
                    visual_started=forgely_perf_ns()
                    visual_result=visual_history.observe(crop_zone(im,'history'),
                        history_scope(mailbox,generation,title,context_item,slot_icon),
                        frame_id,ocr_rune or vision_rune)
                    perf.record('historique_visuel',forgely_perf_ns()-visual_started)
                    if visual_result.history:
                        # Same semantic history feeds the existing frozen
                        # before/after pairing, not just the result counter.
                        history_text=visual_result.history
                        event=visual_result.event
                    if visual_result.needs_confirmation:
                        getattr(self,'confirmation_requested',threading.Event()).set()
                else:
                    visual_history.reset()
                if not history_summary['has_explicit_outcome'] and event is None and slot_icon is not None:
                    grouped=attempt_groups.observe(crop_zone(im,'history'),
                        history_scope(mailbox,generation,title,context_item,slot_icon),frame_id)
                    messages.put(('attempt_group_status',dict(status=grouped['status'],
                        visible=len(grouped['visible_groups']),observed=grouped['observed_attempts'])))
                    if grouped['pending']:
                        zone_cache.entries.pop('history',None)
                        getattr(self,'confirmation_requested',threading.Event()).set()
                    if grouped['newly_confirmed_groups']:
                        groups=tuple((g.signature,g.root_signature) for g in grouped['newly_confirmed_groups'])
                        messages.put(('accepted_attempt_groups',AcceptedAttemptGroups(frame_id,
                            attempt_session+':'+str(generation),groups,context_item,mailbox,generation,title)))
                else:
                    attempt_groups.reset()
                context_jet = parse_jet(atelier.effects)
                pool_cycle+=1
                pool_name=context_item or (manual_session.equipment.identity_name if manual_selected
                    and not manual_session.invalidated else None)
                pool_profile=complete_learning_profile(pool_name) if pool_name else None
                numeric_jet,numeric_pool=numeric_reading
                confirmed_zones=(confirmed.zones if reused_reading else tuple(
                    (zone,entry) for zone,entry in zone_cache.entries.items()
                    if (zone in ('effects','current_jet') and numeric_jet==parse_jet(atelier.effects)) or
                       (zone=='reliquat' and numeric_pool==choose_reliquat(atelier.effects,atelier.reliquat))))
                visual_reading=ConfirmedAtelierRead(visual_context,visual_signature,atelier,
                    (dict(numeric_jet),numeric_pool),confirmed_zones,
                    numeric_signature=numeric_frame_signature(im))
                pool_complete=bool(pool_profile and set(pool_profile)<=numeric_jet.keys()
                                   and slot_icon is not None and not occluded)
                pool_context=(id(mailbox),generation,title,pool_name,
                              slot_icon.tobytes() if slot_icon is not None else None)
                tracking=pool_observer.observe(pool_context,history_text,numeric_jet,numeric_pool,event,
                                               pool_complete,pool_cycle)
                if tracking['pending']:getattr(self,'confirmation_requested',threading.Event()).set()
                if numeric_pool is None and tracking['origin']=='calculated' and tracking['value'] is not None:
                    numeric_pool=float(tracking['value'])
                messages.put(('observation',(frame_id,frame_started_ns,'pool_tracking',tracking)))
                if not occluded and not numeric_published and getattr(self,'_numeric_worker_enabled',False) is not True:
                    messages.put(('observation',(frame_id,frame_started_ns,'atelier_read',(numeric_jet,numeric_pool,visual_reading))))
                elif not occluded and getattr(self,'_numeric_worker_enabled',False) is not True:
                    messages.put(('observation',(frame_id,frame_started_ns,'atelier_read_complete',visual_reading)))
                profile=complete_learning_profile(context_item) if context_item else None
                from forgely_dofocus import normalise_jet
                complete=profile is not None and set(profile).issubset(normalise_jet(context_jet) or {}) and not occluded
                transition = fusion_contexts.observe(context_item if complete else None,
                    history_text, context_jet, choose_reliquat(atelier.effects, atelier.reliquat), event,
                    event_frame_id=frame_id if event is not None else None)
                if transition is not None and event is None:
                    messages.put(('learning_transition', (context_item, transition)))
                if fusion_contexts.pending_event is not None:
                    getattr(self,'confirmation_requested',threading.Event()).set()
                if (self.track.pending_count or
                    (self.track.baseline is None and self.track._init_count == 1) or
                    self.history_delta_monitor.pending is not None):
                    # Request independent OCR on a fresh capture, without
                    # waiting for the twelve-second idle refresh.
                    zone_cache.entries.pop('history', None)
                    getattr(self,'confirmation_requested',threading.Event()).set()
                self.scan_count += 1
                if raw.strip(): self.readable_frames += 1
                messages.put(('observation', (frame_id, frame_started_ns, 'scan', (title,raw,self.scan_count,
                                             self.track.quarantined,self.skipped_frames,self.track.reason,vision_note))))
                # Publish only after all observations for this frame are queued.
                self.latest_observation_id = frame_id
                perf.record('cycle_complet', forgely_perf_ns() - frame_started_ns)
                self.images_remplacees = max(0, frame_id - previous_processed_id - 1)
                previous_processed_id = frame_id
                if event:
                    messages.put(('history_event_identity', (
                        (found or new_name) if history_identity and history_identity.outcome else None,
                        slot_icon)))
                    bound_item=bind_event_item(getattr(self,'_verified_item_context',None),
                        mailbox,generation,title,frame_id,slot_icon,signature,found or new_name)
                    messages.put(('accepted_event',AcceptedRuneEvent(frame_id,event,bound_item,
                        mailbox,generation,title,transition)))
            except GameNotForeground as e:
                pool_observer.reset()
                self.skipped_frames += 1
                if self.skipped_frames % 4 == 1:
                    messages.put(('waiting_window',str(e)))
            except RuntimeError as e:
                pool_observer.reset()
                self.skipped_frames += 1
                if self.skipped_frames % 4 == 1:
                    messages.put(('waiting_window',str(e)))
            except Exception as e:
                pool_observer.reset()
                self.error_frames += 1
                messages.put(('fatal',type(e).__name__+': '+str(e)))
                break
        capture.close()

    def load_virtual_totals(self):
        try:
            totals=self.simulation_journal.totals_by_item()
            self.messages.put(('simulation_totals_ready',totals))
        except (OSError,__import__('sqlite3').Error) as exc:
            self.simulation_io_error=str(exc)

    def publish_simulation(self,key):
        """Worker callback: persist virtual batches without touching Tk."""
        # Refinement is available immediately, even if the journal is locked.
        self.messages.put(('simulator_ready',key))
        try:
            results=self.simulator.results_for(key)
            if results:self.simulation_journal.record(key,results)
            count=self.simulation_journal.totals(key[1])['virtual']
            self.messages.put(('simulation_totals_ready',{key[1]:count}))
            self.simulation_io_error=None
        except (OSError,ValueError,__import__('sqlite3').Error) as exc:
            self.simulation_io_error=str(exc)

    def record_learning(self,item,rune,outcome,before,after,observation_id=None):
        """Persist once, publish new experience, then refresh visible advice."""
        from forgely_online_experience import OnlineExperience
        from forgely_dofocus import normalise_jet
        profile=complete_learning_profile(item)
        if not profile or any(not set(profile).issubset(normalise_jet(state['jet']) or {}) for state in (before,after)):
            raise ValueError('Profil complet et toutes ses lignes lus avant/après requis pour apprendre')
        audit=audit_transition(rune,outcome,before,after,complete=True)
        if not OnlineExperience(max_samples=1).observe(1,item,rune,outcome,before,after) and audit['status']!='cohérent':
            raise ValueError('Transition contradictoire ou incomplète : exclue de l’apprentissage')
        started=forgely_perf_ns()
        delta=save_transition(item,rune,outcome,before,after,event_confirmed=True,natural_max=profile,complete=True)
        review_transition(self,observation_id,before,after,audit['status']=='cohérent')
        from copy import deepcopy
        self.last_transition_audit={'item':item,'after':deepcopy(after),
            'audit':audit_transition(rune,outcome,before,after,complete=True)}
        self.context_saved+=1
        try:
            self.live_laboratory.refresh()
            memory_ready=True
        except (OSError,__import__('sqlite3').Error):
            self.live_laboratory.notify_observation()
            memory_ready=False
        effects=', '.join(f'{stat} {amount:+g}' for stat,amount in delta['changes'].items()) or 'jet inchangé'
        summary=(f'Mémoire +1 · {item} · {rune} / {outcome} · {effects} · '
                 f'puits {delta["pool_delta"]:+g}')
        if not memory_ready:summary+=' · actualisation en attente'
        self.last_learning={'item':item,'rune':rune,'outcome':outcome,
            'changes':delta['changes'],'pool_delta':delta['pool_delta'],'summary':summary,
            'update_ms':round((forgely_perf_ns()-started)/1_000_000,2)}
        learning_summary=getattr(self,'learning_summary',None)
        if learning_summary is not None:learning_summary.set(summary)
        if hasattr(self,'overlay'):
            self.overlay.show_learning(f'Mémoire +{self.context_saved} · {rune} / {outcome}')
        self.refresh_strategy()
        return delta

    def preview_is_current(self, generation, title, icon, mailbox=None):
        if not self.running or self.stop_event.is_set() or mailbox is not self.frame_mailbox:
            return False
        current_generation, frame = self.frame_mailbox.snapshot()
        if current_generation != generation or frame is None or frame[2] != title:
            return False
        from forgely_atelier import workshop_visual_fallback
        if not workshop_visual_fallback(frame[1]):
            return False
        latest_icon = current_icon(frame[1])
        return latest_icon is not None and icon is not None and icon_distance(latest_icon, icon) <= 17

    def clear_fast_preview(self):
        if getattr(self, 'fast_preview_visible', False):
            self.fast_preview_visible = False
            self.detect_label.configure(text='Lecture en attente')
            self.detect_help.configure(text='Nouvelle lecture de l’atelier nécessaire')

    def retain_masked_copilot(self,reason):
        """Retain display identity/advice; discard before/after learning evidence."""
        measured=getattr(self,'measured_goals',None)
        tracker=getattr(self,'current_slot_tracker',None)
        icon=getattr(tracker,'icon',None)
        if icon is None and isinstance(measured,MeasuredGoals):icon=measured.icon
        if icon is None or not (self.active_equipment_verified or
                isinstance(measured,MeasuredGoals) and measured.targets):return False
        self._copilot_masked=True
        self._verified_item_context=None
        self.workshop_readings.invalidate()
        clear_fusion_pairing(self)
        self.pending_transition=None
        self.pre_fusion_sample=None
        self.before_identity_reading=None
        self.status.set(reason+' · objet conservé · conseil suspendu')
        self.refresh_strategy()
        return True

    def process_messages(self):
        pump_started=forgely_perf_ns()
        self._batch_ui_updates=True
        self._strategy_dirty=self._plan_dirty=False
        had_messages=False
        try:
            for index in range(64):
                if index and forgely_perf_ns()-pump_started >= 8_000_000:
                    break
                kind,data=self.messages.get_nowait()
                had_messages=True
                source_context=None
                hard_capture_invalidation=False
                frame_id=event_frame_id=None
                event_observation_id=None
                event_already_recorded=False
                learning_receipt=False
                if kind=='simulator_ready':
                    if data==getattr(self,'_simulation_key',None):self.refresh_strategy()
                    self.refresh_stats_now()
                    continue
                if kind=='simulation_totals_ready':
                    for ident,count in data.items():
                        self._virtual_totals[ident]=max(self._virtual_totals.get(ident,0),count)
                    self.refresh_stats_now()
                    continue
                if kind=='worker_message':
                    mailbox,generation,title,kind,data=data
                    source_context=(mailbox,generation,title)
                    if mailbox is not self.frame_mailbox:
                        continue
                    current_generation,frame=mailbox.snapshot()
                    if generation!=current_generation or frame is None or frame[2]!=title:
                        continue
                if kind=='workshop_detected':
                    notice_mailbox,notice_generation,notice_title=data
                    generation,frame=self.frame_mailbox.snapshot()
                    if (notice_mailbox is self.frame_mailbox and notice_generation==generation
                            and frame is not None and frame[2]==notice_title):
                        self.workshop_active=True
                        self.detect_label.configure(text='Atelier repéré · lecture du jet en cours')
                        self.detect_help.configure(text='Structure reconnue ; objet, valeurs et reliquat restent à confirmer.')
                        getattr(self,'confirmation_requested',threading.Event()).set()
                        self.refresh_strategy()
                    continue
                if kind=='attempt_group_status':
                    visible=data['visible']
                    if data['status']=='initial_reference' and visible:
                        self.detect_label.configure(text=f'Historique : {visible} groupes de tentative visibles')
                        self.detect_help.configure(text='Référence initiale : seules les nouvelles tentatives sont comptées.')
                    elif data['status'] in ('clipped_window','scrollbar_visible','ambiguous_reference'):
                        self.detect_label.configure(text='Historique partiel · comptage à vérifier')
                        self.detect_help.configure(text='Défilement ou lecture ambiguë : aucune tentative ajoutée.')
                    elif data['status']=='confirmation_pending':
                        self.detect_help.configure(text='Historique modifié · confirmation sur une nouvelle capture.')
                    elif data['status']=='anchors_unavailable':
                        self.detect_help.configure(text='Lecture de l’historique : aucune nouvelle tentative suffisamment identifiable.')
                    continue
                if kind=='accepted_attempt_groups':
                    receipt=data
                    inserted=0
                    try:
                        for index,(signature,root) in enumerate(receipt.groups):
                            key=f'{receipt.session_key}:{receipt.frame_id}:{index}:{signature}'
                            inserted+=bool(record_activity(key,receipt.item or '',
                                f'Groupe ancré par une icône de rune ; résultat non déterminé ; root={root}'))
                    except (OSError,ValueError,__import__('sqlite3').Error) as exc:
                        self.status.set('Enregistrement de tentative impossible : '+str(exc))
                        continue
                    if not inserted:continue
                    self.refresh_stats_now()
                    generation,frame=self.frame_mailbox.snapshot()
                    if (receipt.mailbox is not self.frame_mailbox or receipt.generation!=generation
                            or frame is None or frame[2]!=receipt.title):continue
                    summary=f'{inserted} tentative'+('s' if inserted>1 else '')+' observée'+('s' if inserted>1 else '')+' · résultat non déterminé'
                    getattr(self,'pool_refresh_requested',threading.Event()).set()
                    getattr(self,'confirmation_requested',threading.Event()).set()
                    self.last_detected.set(summary)
                    self.detect_label.configure(text=summary)
                    self.detect_help.configure(text='Enregistrée(s) à part · exclue(s) des taux SC/SN/EC et de l’apprentissage.')
                    continue
                if kind=='capture_invalidated':
                    mailbox,generation,reason=data
                    if mailbox is not self.frame_mailbox or generation!=mailbox.generation():
                        continue
                    hard_capture_invalidation=reason=='Compte, fenêtre ou dimensions DOFUS modifiés'
                    if hard_capture_invalidation:self._copilot_masked=False
                    kind,data='atelier_waiting',reason
                if kind=='accepted_event':
                    receipt=data
                    event=receipt.event
                    learning_receipt=True
                    try:
                        if receipt.item and event.rune:
                            event_observation_id=insert_observation(receipt.item,event.rune,event.outcome,'ocr_auto',event.evidence)
                            review_event(self,event_observation_id,receipt.item,event.rune,event.outcome,receipt.frame_id,
                                str(id(receipt.mailbox))+':'+str(receipt.generation))
                            self.saved_auto+=1
                            if receipt.transition is None:
                                links=getattr(self,'_learning_observation_ids',None)
                                if not isinstance(links,dict):links=self._learning_observation_ids={}
                                key=(id(receipt.mailbox),receipt.generation,receipt.title,receipt.frame_id,
                                     receipt.item,event.rune,event.outcome)
                                links[key]=(receipt.mailbox,event_observation_id)
                                while len(links)>256:links.pop(next(iter(links)))
                            if receipt.transition is not None:
                                try:
                                    self.record_learning(receipt.item,event.rune,event.outcome,
                                        receipt.transition['before'],receipt.transition['after'],observation_id=event_observation_id)
                                except Exception as exc:
                                    self.context_rejected += 1
                                    self.status.set('Contexte non enregistré : '+str(exc))
                        else:
                            insert_unassigned(event.outcome,'Rune '+str(event.rune or '?')+
                                ' · identité non confirmée au moment de la lecture · '+event.evidence)
                    except Exception as exc:
                        self.status.set('Enregistrement impossible : '+str(exc))
                        continue
                    # Persistence uses the immutable original identity. Current
                    # display/state may have moved on while this receipt waited.
                    current_generation,frame=self.frame_mailbox.snapshot()
                    current=(receipt.mailbox is self.frame_mailbox and receipt.generation==current_generation
                        and frame is not None and frame[2]==receipt.title and receipt.item is not None
                        and self.active_equipment_verified and self.item.get()==receipt.item)
                    if not current:
                        self.refresh_stats_now()
                        continue
                    event_already_recorded=True
                    source_context=(receipt.mailbox,receipt.generation,receipt.title)
                    kind,data='auto_event_frame',(receipt.frame_id,event)
                if kind=='learning_transition':
                    context_item, transition = data
                    observation_id=None
                    if source_context is not None and transition.get('event_frame_id') is not None:
                        mailbox,generation,title=source_context
                        key=(id(mailbox),generation,title,transition['event_frame_id'],
                             context_item,transition['rune'],transition['outcome'])
                        links=getattr(self,'_learning_observation_ids',{})
                        link=links.pop(key,None) if isinstance(links,dict) else None
                        if link is None or link[0] is not mailbox:
                            self.context_rejected+=1
                            continue
                        observation_id=link[1]
                    try:
                        self.record_learning(context_item,transition['rune'],transition['outcome'],
                            transition['before'],transition['after'],observation_id=observation_id)
                    except Exception as exc:
                        self.context_rejected += 1
                        self.status.set('Contexte non enregistré : '+str(exc))
                    continue
                show_event_result = True
                if kind == 'auto_event_frame':
                    event_frame_id, data = data
                    self.last_full_event_frame_id = max(self.last_full_event_frame_id, event_frame_id)
                    show_event_result = event_frame_id >= self.last_displayed_result_frame_id
                    if show_event_result:
                        self.last_displayed_result_frame_id = event_frame_id
                        self.fast_preview_visible = False
                    kind = 'auto_event'
                identity_only=kind=='identity_observation'
                if identity_only:kind='observation'
                identity_frame_key=None
                if kind == 'observation':
                    frame_id, frame_started_ns, kind, data = data
                    # Keep the two most recent samples for stability checks,
                    # but discard stale UI work. Do not discard rune events.
                    if frame_id < self.latest_observation_id - 1:
                        continue
                    if source_context is not None and kind=='item_visual':
                        from forgely_item_identity import IdentityFrameGate
                        gate=getattr(self,'_identity_frame_gate',None)
                        if gate is None:gate=self._identity_frame_gate=IdentityFrameGate()
                        if not gate.accept(*source_context,frame_id):continue
                        identity_frame_key=(*source_context,frame_id)
                    if identity_only:self.last_identity_delay_ms=(forgely_perf_ns()-frame_started_ns)/1_000_000
                    self.last_observation_delay_ms = (
                        forgely_perf_ns() - frame_started_ns) / 1_000_000
                if kind=='item_visual':
                    frame_kwargs={'frame_key':identity_frame_key} if identity_frame_key is not None else {}
                    known, new_name, raw, slot_icon, history_identity, history_icon, signature, historical_names, corroborated_history_name, latest_history_candidate = data[:10]
                    catalogue_proof=len(data)>10 and data[10] is True
                    reference=getattr(self.current_slot_tracker,'icon',None)
                    measured=getattr(self,'measured_goals',None)
                    if reference is None and isinstance(measured,MeasuredGoals):reference=measured.icon
                    retained_identity=(self.active_equipment_verified or
                        isinstance(measured,MeasuredGoals) and bool(measured.targets))
                    replacing_named=bool(retained_identity and catalogue_proof and known and self.item.get() and
                                         key_for(known)!=key_for(self.item.get()))
                    if reference is not None and retained_identity and not replacing_named:
                        replacement=getattr(self,'_icon_replacement',None)
                        if not isinstance(replacement,IconReplacement):
                            replacement=self._icon_replacement=IconReplacement()
                        state=replacement.observe(reference,slot_icon,identity_frame_key)
                        if state in ('hidden','pending'):
                            # Delayed identity OCR cannot suspend numbers that
                            # were independently confirmed at or after its frame.
                            if numeric_snapshot_covers(self,source_context,frame_id):
                                continue
                            self.retain_masked_copilot('Icône temporairement masquée' if state=='hidden'
                                else 'Vérification du changement d’icône')
                            getattr(self,'confirmation_requested',threading.Event()).set()
                            continue
                        if state=='same':
                            # OCR text, including tooltip min/max, cannot rename
                            # an item whose independently identified icon matches.
                            self.current_slot_tracker.observe(slot_icon,self.current_slot_tracker.signature,**frame_kwargs)
                            if isinstance(measured,MeasuredGoals) and source_context is not None:
                                measured.observe_slot(slot_icon,measured.signature,(source_context[0],source_context[2]))
                            if self.active_equipment_verified and source_context is not None:
                                self._verified_item_context=VerifiedItemContext(*source_context,frame_id,
                                    self.item.get(),slot_icon.copy(),tuple(signature))
                            continue
                        self._copilot_masked=False
                        self._icon_replacement=IconReplacement()
                    measured=getattr(self,'measured_goals',None)
                    if isinstance(measured,MeasuredGoals) and source_context is not None:
                        before=measured.revision
                        measured.observe_slot(slot_icon,signature,(source_context[0],source_context[2]))
                        if measured.revision!=before:
                            self.perfect_goal_checked.set(False)
                            self.goal_mode.set('')
                        if measured.revision!=before and self.overlay.goal_editing:
                            self.overlay.close_targets()
                    if isinstance(getattr(self,'manual_equipment',None),ManualEquipmentSession):
                        self.process_manual_equipment(slot_icon,signature,source_context,
                            frame_id if source_context is not None else 0)
                        continue
                    self.last_history_candidate = latest_history_candidate
                    self.last_history_identity=(
                        (history_identity.name or 'aucun')+' · '+history_identity.source
                        if history_identity else 'Historique non lu')
                    if historical_names:
                        self.last_history_identity += ' · noms visibles (non confirmés) : ' + ', '.join(historical_names[:3])
                    self.last_item_ocr_text=raw
                    from forgely_continuous_identity import prime_slot_tracker
                    fast_slot=prime_slot_tracker(self.current_slot_tracker,
                        getattr(self,'fast_slot_evidence',None),slot_icon,source_context,forgely_perf_ns())
                    stable, changed=self.current_slot_tracker.observe(slot_icon, signature,**frame_kwargs)
                    if changed or replacing_named:
                        self.clear_fast_preview()
                        # A different icon in the actual workshop means a new
                        # item, even if the history still shows the OLD name.
                        clear_fusion_pairing(self);self.active_equipment_verified=False
                        self.item_selection_source='none'
                        self.last_item_candidate=''
                        self.item_icon_status='Changement d’objet détecté · nouvelle identification requise'
                        self.item_visual_tracker.reset()
                        self.history_delta_monitor.reset()
                        self.history_delta_diagnostic=self.history_delta_monitor.last
                        self.trusted_history_name=None
                        self.trusted_history_generation=None
                        self.provisional_slot_id=None
                        self.live_jet=None;self.live_pool=None
                        self.live_after_fusion=True;self.pending_transition=None
                        self.workshop_readings.reset();clear_fusion_pairing(self)
                        self.before_identity_reading=None
                        self._verified_item_context=None
                        self._confirmed_atelier_read=None
                        if isinstance(measured,MeasuredGoals):
                            measured.reset()
                            self.perfect_goal_checked.set(False)
                            self.goal_mode.set('')
                        self.refresh_strategy()
                    if slot_icon is None:
                        self.workshop_readings.reset();clear_fusion_pairing(self)
                        self.live_jet=None;self.live_pool=None;self.live_after_fusion=True
                        self.clear_fast_preview()
                        self.current_slot_status='Icône absente ou illisible'
                        self.last_item_candidate=''
                        self.item_icon_status='Emplacement actuel non lisible'
                        if self.current_slot_tracker.misses>=3:
                            self.workshop_readings.reset();clear_fusion_pairing(self)
                            clear_fusion_pairing(self);self.active_equipment_verified=False
                            self.item_selection_source='none'
                            self.provisional_slot_id=None
                            self.trusted_history_name=None
                            self.live_jet=None;self.live_pool=None
                            self.live_after_fusion=True
                        self.refresh_strategy()
                        continue
                    self.current_slot_status=f'Icône actuelle · {min(self.current_slot_tracker.count,3)}/3 lectures'
                    # Confirm the name and slot concurrently on independent
                    # captured frames; preserve the existing three-frame rule.
                    candidate_streak = self.item_visual_tracker.observe(
                        known or new_name, slot_icon)
                    if not stable:
                        if getattr(self, 'confirmation_requested', None) is not None:
                            getattr(self,'confirmation_requested',threading.Event()).set()
                        self.item_icon_status='Stabilisation de l’icône actuelle'
                        self.refresh_strategy()
                        continue
                    # Strict icon-first identification. Never derive an item's
                    # name from rune history, even when a historical row matches.
                    # A named reference must already exist in the icon catalogue.
                    catalogued_known=bool(known and is_catalogue_identity(known))
                    automatic=getattr(getattr(self,'equipment_mode',None),'get',lambda:None)()=='automatic'
                    matched=(known if catalogued_known else None if automatic else
                             match_current_item(slot_icon, self.current_slot_tracker.signature))
                    # The old reference is not allowed to survive a strong
                    # change of natural effect ranges. Never recycle its pool.
                    if matched and not catalogued_known:
                        bounds = natural_bounds(matched)
                        from forgely_jet import norm
                        expected = {norm(k):tuple(v) for k,v in bounds.items()}
                        current_sig = self.current_slot_tracker.signature
                        disagreements = sum(1 for k,lo,hi in current_sig
                                            if k in expected and expected[k] != (lo,hi))
                        unexpected = sum(1 for k,lo,hi in current_sig if k not in expected)
                        if len(current_sig) >= 3 and (disagreements >= 2 or unexpected >= 3):
                            matched=None
                            known=None
                            self.item_icon_status='Profil incompatible avec l’ancien objet · identification suspendue'

                    # A confirmed OCR reading of the fixed ACTIVE heading is
                    # independent name evidence. Unlike a past history block,
                    # this line always belongs to the current workshop item.
                    # The visual tracker below still requires 3 stable frames.
                    # The active heading can identify an official object even
                    # when its workshop icon has no previous local reference.
                    # The stable current-slot icon is still required below.
                    name=matched or known or new_name
                    # OCR of the ACTIVE heading may be missing, but a distinct
                    # history name is not by itself proof of current identity.
                    # Keep the item unknown rather than reuse the old name.
                    if name and self.item.get() == name and not self.active_equipment_verified:
                        self.live_jet=None
                        self.live_pool=None
                    if matched and known and key_for(matched) != key_for(known):
                        name=None
                        self.item_icon_status='Conflit entre icône et nom actuel : vérification nécessaire'
                    self.last_item_candidate=name or ''
                    if not name:
                        if self.active_equipment_verified:
                            clear_fusion_pairing(self);self.active_equipment_verified=False
                            self.item_selection_source='none'
                            self.live_jet=None; self.live_pool=None
                            self.live_after_fusion=True; self.pending_transition=None
                        if automatic and self.workshop_readings.context is not None:
                            self.workshop_readings.reset()
                            self._verified_item_context=None
                            self._confirmed_atelier_read=None
                        if self.provisional_slot_id is None:
                            try:
                                self.provisional_slot_id=remember_provisional(slot_icon, self.current_slot_tracker.signature)
                            except (OSError, ValueError, __import__('sqlite3').Error) as exc:
                                self.item_icon_status='Sauvegarde provisoire impossible : '+str(exc)
                                self.refresh_strategy()
                                continue
                        self.item_icon_status=(
                            'Icône de l’atelier inconnue du catalogue · '
                            f'fiche provisoire {self.provisional_slot_id} · ' +
                            (f'candidat historique : {latest_history_candidate} (non confirmé)'
                             if latest_history_candidate else 'aucun candidat historique'))
                        self.refresh_strategy()
                        continue
                    streak=(candidate_streak if name == (known or new_name)
                            else self.item_visual_tracker.observe(name,slot_icon,**frame_kwargs))
                    threshold=1 if fast_slot and matched else 3
                    self.item_icon_status=f'Objet actuel et nom cohérents · {min(streak,threshold)}/{threshold}'
                    if streak<threshold:
                        if getattr(self, 'confirmation_requested', None) is not None:
                            getattr(self,'confirmation_requested',threading.Event()).set()
                        self.refresh_strategy()
                        continue
                    try:
                        # Never register a name from stale history. The current
                        # slot icon and a confirmed source are mandatory.
                        registered=register_item(name)
                        name=registered[1]
                        # Official mappings permit shared artwork, resolved by
                        # bounds/category above. Do not force them into the old
                        # local one-icon/one-name enrollment constraint.
                        if not is_catalogue_identity(name):
                            remember_current_item(name,slot_icon,self.current_slot_tracker.signature)
                            if item_icon(name) is None:
                                register_item_with_icon(name,slot_icon)
                    except (ValueError,OSError,__import__('sqlite3').Error) as exc:
                        self.item_icon_status='Conflit ou erreur : '+str(exc)
                        clear_fusion_pairing(self);self.active_equipment_verified=False
                        self.refresh_strategy()
                        continue
                    self.provisional_slot_id=None
                    self.item_icon_status='Icône de l’atelier reconnue : '+name
                    identity_changed=self.item.get()!=name or not self.active_equipment_verified
                    bind_confirmed_equipment(self,name,slot_icon,
                        self.current_slot_tracker.signature,source_context,frame_id)
                    if identity_changed:
                        self.item_selection_source='catalogue' if is_catalogue_identity(name) else 'visual_reference'
                        self.status.set('Objet présent dans l’atelier identifié : '+name)
                        self.render_plan();self.refresh_stats_now();self.refresh_strategy()
                elif kind=='history_event_identity':
                    event_name, event_slot_icon = data
                    if (event_name and event_slot_icon is not None and
                        self.current_slot_tracker.icon is not None and
                        icon_distance(event_slot_icon,self.current_slot_tracker.icon)<=17):
                        self.trusted_history_name=event_name
                        self.trusted_history_generation=self.current_slot_tracker.generation
                elif kind=='scan':
                    title,raw,count,uncertain,skipped,reason,vision_note=data
                    self.window_name.set(title)
                    self.last_capture_title=title
                    self.last_ocr_text=raw
                    # The workshop can contain attempts already made before
                    # this observer session. Do not call it 'waiting for first
                    # rune' if OCR sees historical outcomes; this flag does
                    # NOT count or persist any of those older attempts.
                    history_part=raw.partition('\nEFFETS\n')[0]
                    from forgely_detection import norm
                    history_normalized=norm(history_part)
                    if ('echec' in history_normalized or
                            'succes' in history_normalized or
                            'reussite' in history_normalized):
                        self.history_has_attempts=True
                    self.last_reason=reason
                    self.reason_label.configure(text=reason)
                    if self.rune_center: self.visual_label.configure(text=vision_note)
                    self.game_state_label.configure(text='● Analyse active',fg=GREEN)
                    self.game_title_label.configure(text=title)
                    self.scan_label.configure(text=f'{count} scans de l’historique')
                    self.ignored_label.configure(text=f'{uncertain} action(s) sans rune')
                    self.status.set(f'Capture DOFUS active · {count} scans · {self.saved_auto} tentative(s) complètes')
                elif kind=='atelier_read_complete':
                    # Enrich only the already confirmed numeric source. This
                    # completion is not a second independent confirmation.
                    previous=getattr(self,'_confirmed_atelier_read',None)
                    if (isinstance(previous,ConfirmedAtelierRead) and isinstance(data,ConfirmedAtelierRead)
                            and previous.context==data.context and previous.numeric_signature==data.numeric_signature
                            and self.workshop_readings.snapshot()==data.numeric):
                        self._confirmed_atelier_read=data
                elif kind=='atelier_read':
                    jet,puits=data[:2]
                    visual_reading=data[2] if len(data)>2 else None
                    if isinstance(visual_reading,ConfirmedAtelierRead):
                        mailbox=getattr(self,'frame_mailbox',None)
                        _,latest=mailbox.snapshot() if mailbox is not None else (None,None)
                        context=((mailbox,latest[2],getattr(getattr(self,'capture',None),'last_handle',None),latest[1].size)
                                 if latest is not None else None)
                        rejection=('capture_absente' if latest is None else visual_reading.numeric_mismatch_reason(context,latest[1]))
                        if rejection:
                            # The last completed OCR may predate another fusion.
                            # Retain display values but revoke actionable evidence.
                            self.workshop_readings.invalidate()
                            self.live_jet=self.live_pool=None
                            self.live_after_fusion=True
                            self._confirmed_atelier_read=None
                            self._numeric_reads_rejected=getattr(self,'_numeric_reads_rejected',0)+1
                            counts=getattr(self,'_numeric_rejection_reasons',None)
                            if not isinstance(counts,dict):counts=self._numeric_rejection_reasons={}
                            counts[rejection]=counts.get(rejection,0)+1
                            getattr(self,'confirmation_requested',threading.Event()).set()
                            self.refresh_strategy()
                            continue
                    if frame_id is not None and source_context is not None:
                        delay_ns=forgely_perf_ns()-frame_started_ns
                        self.last_numeric_delay_ms=delay_ns/1_000_000
                        tracker=getattr(self,'performance_tracker',None)
                        if isinstance(tracker,PerformanceTracker):
                            tracker.record('capture_vers_affichage_numerique',delay_ns)
                    if (not jet or puits is None) and self.retain_masked_copilot('Lecture temporairement masquée'):
                        getattr(self,'confirmation_requested',threading.Event()).set()
                        continue
                    self.workshop_active=True
                    manual=getattr(self,'manual_equipment',None)
                    selected=(manual.equipment.identity_name if isinstance(manual,ManualEquipmentSession)
                              and not manual.invalidated else None)
                    if self.active_equipment_verified or selected:
                        from forgely_vision_guidance import reference_for
                        profile_name=selected or self.item.get().strip()
                        self.workshop_readings.configure(
                            (source_context, profile_name),
                            reference_for(profile_name) or complete_learning_profile(profile_name))
                    # Read the jet and the pool *before* the item name appears.
                    # These values are provisional and must never drive advice
                    # or item statistics until the item/logo is confirmed.
                    pairing=getattr(self,'fusion_pairing',None)
                    if (isinstance(pairing,FusionPairing) and self.active_equipment_verified and self.live_jet is not None
                            and (jet!=self.live_jet or puits!=self.live_pool)):
                        pairing.preserve(self.item.get(),frame_id if frame_id is not None else self.latest_observation_id,
                            {'jet':dict(self.live_jet),'pool':self.live_pool})
                    previous_sample=self.workshop_readings.sample
                    stable=self.workshop_readings.observe(jet,puits,
                        sequence=frame_id if source_context is not None else None)
                    if not stable and jet and puits is not None:
                        # Ask for another distinct capture now, instead of
                        # waiting for the long idle refresh after a rune.
                        getattr(self,'confirmation_requested',threading.Event()).set()
                    if stable:
                        self._copilot_masked=False
                        jet,puits=self.workshop_readings.snapshot()
                        self._stable_numeric_frame=(source_context,frame_id,self.item.get())
                        if (isinstance(visual_reading,ConfirmedAtelierRead)
                                and visual_reading.numeric[1] is not None
                                and self.workshop_readings.atomic_snapshot
                                and (self.active_equipment_verified or
                                     isinstance(getattr(self,'measured_goals',None),MeasuredGoals)
                                     and self.measured_goals.targets)):
                            self._confirmed_atelier_read=visual_reading
                    sample=self.workshop_readings.sample
                    if self.active_equipment_verified and previous_sample != sample:
                        # Do not display old verified jet/pool as current while
                        # the new OCR values are still being confirmed.
                        self.live_jet=None;self.live_pool=None
                        self.live_after_fusion=True
                    if stable and self.active_equipment_verified:
                        if self.pending_transition is not None:
                            pending=self.pending_transition
                            # A real history transition and a different stable
                            # snapshot are both required for contextual storage.
                            if self.item.get()==pending['item'] and self.workshop_readings.atomic_snapshot:
                                try:
                                    Forgely.record_learning(self,pending['item'],pending['rune'],pending['outcome'],
                                        pending['before'],{'jet':dict(jet),'pool':puits},observation_id=pending.get('observation_id'))
                                    self.status.set(f'Contexte avant/après sauvegardé : {self.context_saved}')
                                except (ValueError,TypeError,KeyError):
                                    self.context_rejected += 1
                                self.pending_transition=None
                            elif self.item.get()!=pending['item'] or not self.workshop_readings.atomic_snapshot:
                                self.pending_transition=None
                                self.context_rejected += 1
                        if self.pending_transition is None:
                            self.live_jet=dict(jet)
                            self.live_pool=puits
                            self.live_after_fusion=False
                            self.pre_fusion_sample=None
                    # A missing item cannot authorize a recommendation, even
                    # when the provisional jet and pool are perfectly stable.
                    if not self.active_equipment_verified:
                        self.live_jet=None
                        self.live_pool=None
                        self.live_after_fusion=True
                    self.overlay.state_color('active')
                    self.refresh_strategy();self.render_plan()
                    measured=getattr(self,'measured_goals',None)
                    maybe_prompt_goals(self)
                    jet_text=', '.join(f'{k} {v}' for k,v in jet.items()) if jet else 'illisible'
                    puits_text=f'{puits:g}' if puits is not None else 'inconnu'
                    if not self.active_equipment_verified:
                        phase=self.waiting_for_item_label() or 'Identification en cours'
                        state=(f'jet et puits provisoires stabilisés · {phase}'
                               if stable else f'lecture provisoire · {phase}')
                    else:
                        state=('lecture stabilisée' if self.live_jet is not None and self.live_pool is not None
                               else 'Jet partiel · fais défiler les lignes à lire ou à revérifier')
                    self.atelier_info_label.configure(text=f'Atelier détecté · Reliquat lu : {puits_text} · Jet lu : {jet_text} · {state}')
                elif kind=='reading_review_status':
                    self.reading_review_status=data
                    self.refresh_reading_reviews()
                elif kind=='pool_tracking':
                    self.pool_tracking_status=data
                elif kind=='catalogue':
                    self.vision.load()
                    ok=len(data['ok']); bad=len(data['errors'])
                    self.status.set(f'Catalogue : {ok} icône(s) importée(s), {bad} non trouvée(s) · stockage local')
                    self.visual_label.configure(text=f'Catalogue : {ok} rune(s) · {len(self.vision.labels())} nom(s) reconnu(s) · calibrage position toujours nécessaire')
                    messagebox.showinfo('Catalogue DOFUS 3',
                        f'{ok} icône(s) téléchargée(s) et enregistrée(s) localement.\n'
                        f'{bad} recherche(s) infructueuse(s).\n\n'
                        'Voir %LOCALAPPDATA%\\Forgely\\catalogue_dofus3\\rapport.json pour le détail.')
                elif kind=='catalogue_error':
                    self.status.set('Import impossible : '+data)
                    messagebox.showerror('Catalogue',data)
                elif kind=='exported':
                    self.status.set('Diagnostic exporté localement : '+data)
                    messagebox.showinfo('Images OCR enregistrées',
                        'Les images de diagnostic sont prêtes.\n\nDossier :\n' + data)
                    try:
                        import os
                        os.startfile(data)
                    except (OSError, AttributeError):
                        pass
                elif kind=='game_title': self.window_name.set(data)
                elif kind=='fast_preview_clear':
                    frame_id, mailbox = data
                    if mailbox is self.frame_mailbox and frame_id >= self.last_displayed_result_frame_id:
                        self.clear_fast_preview()
                elif kind in ('fast_preview', 'fast_changes'):
                    frame_id, captured_ns, event, generation, title, icon, mailbox = data
                    if (frame_id <= self.last_full_event_frame_id or
                        frame_id < self.last_displayed_result_frame_id or
                        not self.preview_is_current(generation, title, icon, mailbox)):
                        continue
                    self.last_displayed_result_frame_id = frame_id
                    self.fast_preview_visible = True
                    # A new visible result makes the previous advice obsolete
                    # before the slower, complete history analysis finishes.
                    # Preserve the pre-fusion numbers for pairing/learning;
                    # the masked flag prevents advising from those old values.
                    if not numeric_snapshot_covers(self,(mailbox,generation,title),frame_id):
                        getattr(self,'pool_refresh_requested',threading.Event()).set()
                        self._copilot_masked = True
                        getattr(self,'confirmation_requested',threading.Event()).set()
                        self.refresh_strategy()
                    delay_ns = forgely_perf_ns() - captured_ns
                    self.fast_preview_performance.record('capture_vers_affichage', delay_ns)
                    if kind == 'fast_changes':
                        changes, stable = event
                        label = ' · '.join(f'{value:+d} {stat}' for stat, value in changes[:4])
                        self.detect_label.configure(text=label + ' · à vérifier')
                        confirmation = 'Variations lues deux fois' if stable else 'Lecture à confirmer'
                        self.detect_help.configure(text=confirmation + ' · rune et résultat SC/SN/EC non confirmés')
                    else:
                        label = event.rune or 'Rune inconnue'
                        self.detect_label.configure(text=f'{label} · {event.outcome} · à vérifier')
                        self.detect_help.configure(text='Lecture rapide provisoire · analyse complète en cours')
                    self.overlay.state_color('candidate')
                elif kind=='auto_event':
                    getattr(self,'pool_refresh_requested',threading.Event()).set()
                    getattr(self,'confirmation_requested',threading.Event()).set()
                    self.last_transition_audit=None
                    already_read=numeric_snapshot_covers(self,source_context,event_frame_id)
                    # Save last stable pre-fusion state BEFORE invalidating it.
                    before=(dict(self.live_jet),self.live_pool) if self.live_jet is not None and not already_read else None
                    pairing=getattr(self,'fusion_pairing',None)
                    cached=None
                    if isinstance(pairing,FusionPairing):
                        cached=pairing.take(self.item.get(),event_frame_id if event_frame_id is not None else self.latest_observation_id,
                            {'jet':before[0],'pool':before[1]} if before else None)
                        before=(dict(cached['jet']),cached['pool']) if cached else None
                    self.pre_fusion_sample=(tuple(sorted(before[0].items())),before[1]) if before else None
                    if not already_read and not learning_receipt and before and (self.workshop_readings.atomic_snapshot or cached is not None) and data.rune and self.active_equipment_verified and self.item.get().strip():
                        self.pending_transition={'item':self.item.get().strip(),
                            'rune':data.rune,'outcome':data.outcome,'sample':self.pre_fusion_sample,
                            'before':{'jet':before[0],'pool':before[1]},'observation_id':event_observation_id}
                    else:
                        self.pending_transition=None
                    if not already_read:
                        self._copilot_masked=False
                        self.live_after_fusion=True;self.live_jet=None;self.live_pool=None;self.workshop_readings.invalidate()
                        getattr(self,'confirmation_requested',threading.Event()).set()
                    self.refresh_strategy()
                    try:
                        if data.rune is None:
                            if not event_already_recorded:
                                insert_unassigned(data.outcome,data.evidence)
                            if show_event_result:
                                self.detect_label.configure(text=f'Action {data.outcome} · rune inconnue')
                                self.detect_help.configure(text=f'{unassigned_total()} action(s) en attente de rune · exclue(s) des statistiques')
                                self.status.set('Nouvelle ligne détectée · rune illisible : conservée à part, sans calcul de probabilité')
                                self.overlay.state_color('candidate')
                        else:
                            if not self.active_equipment_verified or not self.item.get().strip():
                                if not event_already_recorded:
                                    insert_unassigned(data.outcome,'Rune '+data.rune+' · item non identifié · '+data.evidence)
                                if show_event_result:
                                    self.detect_label.configure(text=f'{data.rune} · {data.outcome} · item inconnu')
                                    self.detect_help.configure(text='Tentative isolée : équipement à identifier via le logo flottant')
                                    self.overlay.state_color('candidate')
                                continue
                            if not event_already_recorded:
                                event_observation_id=insert_observation(self.item.get().strip(),data.rune,data.outcome,'ocr_auto',data.evidence)
                                review_event(self,event_observation_id,self.item.get().strip(),data.rune,data.outcome,event_frame_id)
                                if self.pending_transition is not None:self.pending_transition['observation_id']=event_observation_id
                                self.saved_auto += 1
                            if show_event_result:
                                self.detect_label.configure(text=f'{data.rune} · {data.outcome} ✓')
                                self.detect_help.configure(text=f'{self.saved_auto} action(s) automatiquement enregistrée(s) dans cette session')
                                self.status.set('Tentative enregistrée localement · '+data.rune+' · '+data.outcome)
                                self.overlay.state_color('active')
                            self.refresh_stats_now()
                    except Exception as exc: self.status.set('Enregistrement impossible : '+str(exc))
                elif kind=='candidate':
                    self.pending=data
                    label=data.rune if data.rune else 'Rune non reconnue'
                    self.detect_label.configure(text=f'{label}  ·  {data.outcome}')
                    self.detect_help.configure(text='Lecture OCR à vérifier avant enregistrement')
                    self.overlay.state_color('candidate')
                elif kind=='account_switch':
                    self._copilot_masked=False
                    self._icon_replacement=IconReplacement()
                    self._confirmed_atelier_read=None
                    manual_session=getattr(self,'manual_equipment',None)
                    if isinstance(manual_session,ManualEquipmentSession):
                        manual_session.invalidate('Compte changé : sélectionne à nouveau ton objet.')
                        self._verified_item_context=None
                    self.clear_fast_preview()
                    self.workshop_active=False
                    clear_fusion_pairing(self);self.active_equipment_verified=False
                    self.item_selection_source='none'
                    self.live_jet=None;self.live_pool=None
                    self.item_visual_tracker.reset()
                    self.current_slot_tracker.reset()
                    self.provisional_slot_id=None
                    self.trusted_history_name=None
                    self.pending_transition=None
                    self.item_icon_status='Nouveau compte : identification en cours'
                    self.status.set('Atelier détecté automatiquement : '+data)
                    self.window_name.set(data)
                elif kind=='atelier_waiting':
                    self.workshop_active=False
                    if not hard_capture_invalidation and self.retain_masked_copilot(data):continue
                    manual_session=getattr(self,'manual_equipment',None)
                    if isinstance(manual_session,ManualEquipmentSession):
                        manual_session.workshop_lost()
                        self._verified_item_context=None
                    self.clear_fast_preview()
                    self.workshop_active=False
                    self.workshop_readings.reset();clear_fusion_pairing(self)
                    self.first_item_name_seen=False
                    self.before_identity_reading=None
                    self.item_initial_reading=None
                    clear_fusion_pairing(self);self.active_equipment_verified=False
                    self.live_after_fusion=True;self.live_jet=None;self.live_pool=None;self.pre_fusion_sample=None
                    self.item_ocr_streak=0
                    self.item_ocr_last=None
                    self.item_visual_tracker.reset()
                    self.current_slot_tracker.reset()
                    self.trusted_history_name=None
                    self.trusted_history_generation=None
                    self.provisional_slot_id=None
                    self.current_slot_status='Atelier absent'
                    self.item_icon_status='Atelier absent'
                    self.atelier_info_label.configure(text='Atelier : non confirmé · Pas de collecte')
                    self.reason_label.configure(text=data)
                    self.game_state_label.configure(text='● Lecture du jeu en attente',fg=GOLD)
                    self.overlay.state_color('waiting')
                    self.refresh_strategy()
                elif kind=='atelier_masked':
                    # This message follows positive structural detection in
                    # the worker; unreadable numbers do not negate that fact.
                    self.workshop_active=True
                    self.retain_masked_copilot(data)
                    self.refresh_strategy()
                elif kind=='error':self.status.set('Capture : '+data)
                elif kind=='waiting_window':
                    self.workshop_active=False
                    self.status.set('En attente du jeu : '+data)
                    self.game_state_label.configure(text='● En pause · DOFUS non visible',fg=GOLD)
                    self.overlay.state_color('waiting')
                    if not self.retain_masked_copilot('Lecture du jeu en attente : '+data):
                        self.workshop_readings.invalidate()
                        self.live_jet=None;self.live_pool=None;self.live_after_fusion=True
                    self.refresh_strategy()
                elif kind=='fatal':
                    self.status.set('Observation stoppée : '+data)
                    self.running=False;self.stop_event.set();self.observe_button.configure(text='Démarrer l’observation');self.overlay.state_color('error')
                    self.game_state_label.configure(text='● Erreur de lecture',fg=RED)
                    self.refresh_strategy()
        except queue.Empty: pass
        finally:
            self._batch_ui_updates=False
        strategy_dirty=self._strategy_dirty is True
        if strategy_dirty:self.refresh_strategy()
        if self._plan_dirty is True:
            self.render_plan(self.current_proposal if strategy_dirty and not self.observation_only else None)
        if had_messages and getattr(self, 'dashboard', None) is not None:
            self.dashboard.sync()
        if had_messages:Forgely.sync_workshop_indicator(self)
        if self.winfo_exists():
            self.after(1 if not self.messages.empty() else 40,self.process_messages)

    def open_confirm(self):
        if self.pending is None:
            messagebox.showinfo('Pas de détection','Aucune tentative détectée. Tu peux enregistrer manuellement une tentative via Ajout rapide.')
            return
        c=self.pending
        popup=tk.Toplevel(self);popup.title('Vérifier une tentative');popup.configure(bg=BG);popup.geometry('465x355')
        popup.transient(self);popup.grab_set()
        self.label(popup,'Confirmer cette tentative',17,bold=True).pack(anchor='w',padx=20,pady=(20,12))
        self.label(popup,'Rune détectée : '+(c.rune or 'indéterminée'),11,color=MUTED).pack(anchor='w',padx=20)
        selected=tk.StringVar(value=c.rune or 'Vi'); result=tk.StringVar(value=c.outcome)
        self.make_combo(popup,selected,RUNES).pack(fill='x',padx=20,pady=13)
        self.label(popup,'Résultat',10,color=MUTED).pack(anchor='w',padx=20)
        self.make_combo(popup,result,('SC','SN','EC')).pack(fill='x',padx=20,pady=9)
        self.label(popup,'Confirme uniquement si la rune et le résultat sont corrects.',10,color=MUTED,wraplength=420).pack(anchor='w',padx=20,pady=9)
        row=tk.Frame(popup,bg=BG);row.pack(fill='x',padx=20,pady=12)
        def accept():
            try: insert_observation(self.item.get(),selected.get(),result.get(),'ocr_confirmed',c.evidence)
            except Exception as e: messagebox.showerror('Erreur',str(e));return
            self.pending=None;self.detect_label.configure(text='Tentative enregistrée ✓')
            self.detect_help.configure(text='Enregistrée localement et confirmée')
            Forgely.sync_workshop_indicator(self)
            self.refresh_stats();popup.destroy()
        def reject():
            self.pending=None;self.detect_label.configure(text='Détection ignorée');popup.destroy()
        self.button(row,'Ignorer',reject).pack(side='left')
        self.button(row,'Enregistrer localement',accept,primary=True).pack(side='right')

    def record_manual(self,outcome):
        if not self.item.get().strip():
            messagebox.showinfo('Équipement','Indique le nom de ton équipement avant de saisir une tentative.')
            return
        try:insert_observation(self.item.get(),self.rune.get(),outcome,'manual')
        except Exception as e:messagebox.showerror('Erreur',str(e));return
        self.status.set(f'Enregistré localement : {self.rune.get()} · {outcome}')
        self.refresh_stats_now()

    def refresh_stats(self):
        timer=getattr(self,'_stats_refresh_timer',None)
        if timer is not None:
            self.after_cancel(timer)
        self._stats_refresh_timer=None
        self.refresh_stats_now()
        self._stats_refresh_timer=self.after(2500,self.refresh_stats)

    def refresh_stats_now(self):
        # This card covers all local observations, including unattributed
        # activity; selecting an item must not attribute unknown attempts to it.
        n,counts=stats()
        unclassified=activity_total()
        if isinstance(getattr(self,'simulation_journal',None),SimulationJournal):
            virtual=sum(self._virtual_totals.values())
            detail=f'Réelles : {n+unclassified} · Simulées : {virtual} · Total : {n+unclassified+virtual}'
            if unclassified:detail+=f' · {unclassified} résultat(s) à déterminer'
            self.simulation_totals.set(detail)
        total=n+unclassified
        self.total_lbl.configure(text=f'{total} tentative'+('s' if total!=1 else ''))
        for kind in ('SC','SN','EC'):
            self.stats_labels[kind].configure(text=f'{counts[kind]/n:.0%}' if n else '—')
        if hasattr(self,'rune_prob_lbl'):
            chosen=self.rune.get().strip()
            rn,rc=stats(item=self.item.get().strip(),rune=chosen)
            info=rune_summary(chosen,rc)
            ref=info['reference']
            weight=(f'Poids {ref.weight:g} · bonus +{ref.gain:g}' if ref.weight is not None else 'Poids non vérifié')
            if rn:
                levels=info['observed']['levels']
                line=' · '.join(f"{k} {levels[k]['percentage']:.0f}%" for k in ('SC','SN','EC'))
                sc_ci=levels['SC']['ci95']
                text=(f'{chosen} · {weight}\n{rn} essais : {line}\n'
                      f'Intervalle SC (95%) : {sc_ci[0]:.0f}–{sc_ci[1]:.0f}%\n'
                      f'Fiabilité : {info["observed"]["quality"]}')
            else:
                text=f'{chosen} · {weight}\nAucune observation vérifiée sur cet item.'
            self.rune_prob_lbl.configure(text=text)

    def minimize_to_badge(self):
        Forgely.sync_workshop_indicator(self)
        self.overlay.deiconify();self.withdraw()

    def restore(self):
        self.deiconify();self.lift();self.overlay.withdraw()

    def close(self):
        close_review(self)
        if isinstance(getattr(self,'simulator',None),SimulationWorker):self.simulator.stop()
        self.live_laboratory.stop()
        self.stop_event.set()
        if hasattr(self,'overlay'):self.overlay.destroy()
        self.destroy()


if __name__=='__main__':
    Forgely().mainloop()
