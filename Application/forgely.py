"""Forgely local beta. No telemetry, cloud, OpenAI, game automation or input.
Optional explicit network action imports public item images; observation remains offline.
"""
from __future__ import annotations
from time import perf_counter_ns as forgely_perf_ns
from forgely_performance import PerformanceTracker
from forgely_zone_cache import ZoneCache
from forgely_pipeline import FrameMessageSink,AcceptedRuneEvent,VerifiedItemContext,bind_event_item
import io
from pathlib import Path
from datetime import datetime
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from forgely_observation_mode import load_observation_mode, save_observation_mode
from forgely_data import connect, insert_observation, insert_unassigned, unassigned_total, stats, recent, RUNES, DB_FILE, DATA_DIR
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
from forgely_atelier import read_atelier, crop_zone, parse_reliquat, choose_reliquat, title_candidates, focus_workshop
from forgely_jet import parse_jet
from forgely_item_references import download_references
from forgely_profile_guidance import compare as compare_theoretical_profile
from forgely_workshop_readings import WorkshopReadings
from forgely_equipment_session import ManualEquipmentSession
from forgely_measured_goals import MeasuredGoals,current_snapshot,bound_session
from forgely_continuous_identity import (crop_current_item, current_icon,
    effect_signature, CurrentSlotTracker, match_current_item,
    remember_current_item, remember_provisional)
from forgely_item_icons import icon_distance
from forgely_ocr_diagnostic import evaluate as evaluate_ocr
from forgely_probabilites import reference as rune_reference, summary as rune_summary
from forgely_decision import advise, Proposal
from forgely_rules import MODES as OBJECTIVE_MODES, objective_mode
from forgely_copilote import MODES, player_signal
from forgely_context import save_transition, context_rates
from forgely_learning import complete_learning_profile
from forgely_expert import build_dashboard, render_dashboard, audit_transition, rules_text
from forgely_simulation_live import SimulationWorker
from forgely_simulation_journal import SimulationJournal
from forgely_labo_live import LiveLaboratory
from forgely_tools import (read_settings,save_settings,STRATEGIES,
    export_observations_csv,export_item_summary,backup_local,import_bounds_csv,
    natural_bounds,illustrative_scenario,advisory_status)
from forgely_gallery import verify_goal,save_success,list_successes,export_gallery_json

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
        from forgely_tools import activate_tylezia_reference
        activate_tylezia_reference()
        self.theme_name=load_theme()
        set_palette(self.theme_name)
        self.title('Forgely · L’atelier - v22.14')
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
        self.equipment_mode=tk.StringVar(value='manual')
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
        self.simulator=SimulationWorker(on_ready=self.publish_simulation,
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
        self.rune_center=None
        self.visual_state="Non configuré"
        # Keep the manually selected window when restarting observation.
        old_manual_handle=None
        self.capture=GameCapture()
        self.capture.manual_handle=None
        self.saved_auto=0
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
        self.active_equipment_verified=False
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
        self.workshop_readings=WorkshopReadings(required_frames=3)
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
        self.live_laboratory=LiveLaboratory()
        self.live_laboratory.start()
        try:
            import json
            calibration=json.loads((DATA_DIR/'calibration_rune.json').read_text(encoding='utf8'))
            self.rune_center=(float(calibration['x']),float(calibration['y']))
        except (OSError,ValueError,KeyError,TypeError):pass
        if self.plan: self.item.set(self.plan.get("item", ""))
        # A saved plan is not proof that the same item is currently in the workshop.
        self.active_equipment_verified=False
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

    def render_plan(self):
        if getattr(self, 'dashboard', None) is not None:
            self.dashboard.sync()
        if self.observation_only:
            title,detail='Collecte active','Aucun objectif de rune suggéré dans ce mode.'
        else:
            proposal=self.strategy_current()
            title=proposal.summary
            detail='Référence Dofocus · '+proposal.explanation[:170]+('… Voir le détail.' if len(proposal.explanation)>170 else '')
        if hasattr(self,'plan_item_lbl'):
            manual=getattr(self,'manual_equipment',None)
            from forgely_dashboard import current_card
            card=current_card(self)
            self.plan_item_lbl.configure(text=card['title'])
            self.plan_action_lbl.configure(text=title)
            self.plan_explain_lbl.configure(text=detail)

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
        self._simulation_key=None
        if self.observation_only:
            return None
        from forgely_pricing import book_from_settings,active_price_book
        settings=read_settings()
        price_book=book_from_settings(settings) or active_price_book()
        advice_mode=settings.get('strategy','Chances maximales')
        measured=getattr(self,'measured_goals',None)
        if isinstance(measured,MeasuredGoals) and measured.targets:
            goal_mode=getattr(self,'goal_mode',None)
            return measured.proposal(current_snapshot(self),
                item=self.item.get() if self.active_equipment_verified else None,
                mode=advice_mode,price_book=price_book)
        """Only stable post-fusion OCR, confirmed equipment and saved goal can drive advice."""
        if not self.plan or not self.active_equipment_verified or self.item.get()!=self.plan.get('item'):
            return advise({}, {}, pool=None)
        targets={k:v['target'] for k,v in self.plan.get('stats',{}).items() if v.get('target') is not None}
        jets=self.live_jet or {}
        pool=self.live_pool
        if self.live_after_fusion:
            return advise(jets,targets,pool=pool,after_fusion=True)
        rune_counts=None
        def records_for(rune):
            nonlocal rune_counts
            if rune_counts is None:
                from forgely_data import stats_by_rune
                rune_counts=stats_by_rune(item=self.item.get().strip())
            return dict(rune_counts.get(rune, {'SC':0,'SN':0,'EC':0}))
        # No claim of EXO without a verified complete natural profile.
        # A partial imported CSV is useful for known overmax lines only.
        bounds=natural_bounds(self.item.get().strip())
        experience_lookup=getattr(self.live_laboratory,'experience',None)
        experience_bounds=complete_learning_profile(self.item.get().strip())
        simulator=getattr(self,'simulator',None)
        simulation_context=(simulator.context(self.item.get().strip(),jets,pool,targets,revision=self.live_laboratory.revision)
            if isinstance(simulator,SimulationWorker) else None)
        self._simulation_key=simulation_context.key if simulation_context else None
        from forgely_pricing import active_price_book
        proposal=advise(jets,targets,pool=pool,counts_for=records_for,price_book=price_book,mode=advice_mode,
            predictive_policy=True,
            natural_max=experience_bounds or ({s:v[1] for s,v in bounds.items()} if bounds else None),
            item=self.item.get().strip(),profile_complete=bool(experience_bounds),
            contextual_for=lambda rune: self.live_laboratory.estimate(self.item.get().strip(),rune,jets,pool),
            experience_for=(lambda rune:experience_lookup(self.item.get().strip(),rune,jets,pool,targets,experience_bounds))
                if callable(experience_lookup) else None,
            simulation_for=simulation_context.evidence if simulation_context else None)
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
            after_fusion=False if snapshot else self.live_after_fusion,last_transition=audit)
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

    def refresh_strategy(self):
        if getattr(self, 'dashboard', None) is not None:
            self.dashboard.sync()
        if self.observation_only:
            self.current_proposal=None
            if getattr(self,'strategy_headline',None) is not None and self.strategy_headline.winfo_exists():
                self.strategy_headline.configure(text='Observation passive : aucun conseil')
            if getattr(self,'strategy_explanation',None) is not None and self.strategy_explanation.winfo_exists():
                self.strategy_explanation.configure(text='Les tentatives continuent à être collectées localement.')
            if hasattr(self,'advice_heading'):
                self.advice_heading.configure(text='OBSERVATION PASSIVE  /  COLLECTE UNIQUEMENT')
                self.home_advice_label.configure(text='Observation sans conseils',fg=GOLD)
                self.home_advice_detail.configure(text='Détection des tentatives et statistiques locales actives. Aucune rune recommandée.')
                self.player_risk_label.configure(text='Mode collecte : recommandations désactivées')
                self._update_main_rune_icon('')
            if hasattr(self,'overlay'):
                self.overlay.show_advice(self.waiting_for_item_label() or 'Observation', 'collecte')
            return
        if hasattr(self,'advice_heading'):
            self.advice_heading.configure(text='PROCHAINE RUNE')
        proposal=self.strategy_current()
        self.current_proposal=proposal
        if getattr(self,'strategy_headline',None) is not None and self.strategy_headline.winfo_exists():
            self.strategy_headline.configure(text=proposal.summary)
        if getattr(self,'strategy_explanation',None) is not None and self.strategy_explanation.winfo_exists():
            self.strategy_explanation.configure(text=proposal.explanation)
        targets={k:v['target'] for k,v in (self.plan or {}).get('stats',{}).items() if v.get('target') is not None}
        measured=getattr(self,'measured_goals',None)
        snapshot=current_snapshot(self) if isinstance(measured,MeasuredGoals) and measured.targets else None
        if isinstance(measured,MeasuredGoals) and measured.targets:targets=measured.targets
        signal=player_signal(proposal,snapshot[0] if snapshot else self.live_jet,targets,
            snapshot[1] if snapshot else self.live_pool,
            self.active_equipment_verified or snapshot is not None,
            False if snapshot else self.live_after_fusion,self.goal_mode.get())
        from forgely_predictive import report_text
        from forgely_vision_guidance import reference_for
        report_jet=snapshot[0] if snapshot else self.live_jet or {}
        report_pool=snapshot[1] if snapshot else self.live_pool
        report_bounds=reference_for(self.item.get()) if self.active_equipment_verified else {}
        report_max={k:max(v) for k,v in report_bounds.items()} or None
        tracking=getattr(self,'pool_tracking_status',None)
        pool_origin=('calculé' if isinstance(tracking,dict) and tracking.get('origin')=='calculated' else 'lu')
        self.predictive_report=report_text(proposal,report_jet,targets,report_max,report_pool,pool_origin=pool_origin)
        self.predictive_report=self.expert_detail(proposal,self.predictive_report)
        compact_report=report_text(proposal,report_jet,targets,report_max,report_pool,pool_origin=pool_origin,compact=True)
        if getattr(self,'strategy_explanation',None) is not None and self.strategy_explanation.winfo_exists():
            self.strategy_explanation.configure(text=self.predictive_report)
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
            self.player_risk_label.configure(text=f'Risque indicatif : {signal.risk} · {self.goal_mode.get()}{classification}')
        if hasattr(self,'home_advice_label'):
            self.home_advice_label.configure(text=signal.title,fg=GOLD if signal.stop else GREEN if proposal.rune else GOLD)

            sequence=(proposal.estimates or {}).get('objective',{}).get('sequence')
            if sequence:
                detail=signal.detail+' Anticipation : jusqu’à '+str(sequence['horizon'])+' poses pour atteindre tout le jet.'
            else:
                detail=signal.detail+'  '+proposal.explanation
            self.home_advice_detail.configure(text=compact_report)
            self._update_main_rune_icon(proposal.rune if not signal.stop else '')
        if hasattr(self,'overlay'):
            self.overlay.show_advice(self.waiting_for_item_label() or ('STOP' if signal.stop else signal.title), signal.risk)
        if getattr(self, 'dashboard', None) is not None:
            self.dashboard.fit_advice()

    def _update_main_rune_icon(self, rune: str):
        """Display only a uniquely matched local rune icon; no invented substitutes."""
        if not hasattr(self, 'main_rune_icon'):
            return
        path = rune_icon_path(rune or '')
        if path is not None:
            try:
                with Image.open(path) as source:
                    picture = source.convert('RGBA')
                    picture.thumbnail((58, 58), Image.Resampling.LANCZOS)
                    self.main_rune_photo = ImageTk.PhotoImage(picture)
                self.main_rune_icon.configure(image=self.main_rune_photo, text='', width=64, height=64)
                return
            except (OSError, ValueError, tk.TclError):
                pass
        self.main_rune_photo = None
        self.main_rune_icon.configure(image='', text='FM', width=5, height=3)

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
        self.workshop_readings.reset()
        self.active_equipment_verified=False
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
        if goals_only and current_snapshot(self) is not None:
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
        self.plan=save_plan(self.item.get(),values,item_id=equipment.item_id)
        self.perfect_goal_checked.set(False)
        self.goal_mode.set('')
        self.status.set('Jet cible enregistré pour '+equipment.name+' · Détection automatique conservée')
        self.render_plan();self.refresh_strategy()
        if start and not self.running:self.after(0,self.toggle_observer)

    def prompt_measured_goals(self):
        snapshot=current_snapshot(self)
        if snapshot is None:return
        session=self.measured_goals
        if self.overlay.goal_editing:return
        session.prompted=True
        revision=session.revision
        jet=dict(snapshot[0])
        from forgely_perfect_goal import perfect_goal
        try:allowed=perfect_goal(self)[2]
        except ValueError:allowed={}
        def save(targets):
            session.save(targets,jet,revision,allowed=allowed)
            perfect=bool(self.perfect_goal_checked.get() and targets==allowed)
            self.goal_mode.set('Jet parfait' if perfect else '')
            self.perfect_goal_checked.set(perfect)
            self.overlay.close_targets()
            self.status.set('Jet souhaité enregistré · conseils automatiques actifs')
            self.render_plan();self.refresh_strategy()
            self.after(100,self.resume_game_after_targets)
        self.overlay.deiconify()
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
            from forgely_perfect_goal import signature_equipment
            inferred=signature_equipment(measured.signature)
            if (measured.icon is not None and self.active_equipment_verified
                    and key_for(self.item.get())==key_for(name)) or (
                    measured.icon is not None and inferred is not None and key_for(inferred.identity_name)==key_for(name)):
                measured.save(targets,observed,measured.revision,allowed=targets)
            else:
                measured.targets={}
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
        plan=save_plan(equipment.identity_name,values,item_id=equipment.item_id)
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
        self.active_equipment_verified=False
        self._verified_item_context=None
        self.live_jet=None;self.live_pool=None;self.live_after_fusion=True
        self.pending_transition=None;self.pre_fusion_sample=None
        self.workshop_readings.reset();self.item_visual_tracker.reset()
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
                self.workshop_readings.reset()
            self._verified_item_context=None
            self.live_jet=None;self.live_pool=None;self.live_after_fusion=True
            if session.invalidated:
                self.pending_transition=None
                self.workshop_readings.reset()
                self.status.set(session.reason)
            elif slot_icon is not None:
                self.confirmation_requested.set()
        else:
            self.item.set(session.equipment.identity_name)
            if source_context is not None:
                mailbox,generation,title=source_context
                self._verified_item_context=VerifiedItemContext(mailbox,generation,title,
                    frame_id,session.equipment.identity_name,slot_icon.copy(),tuple(signature))
            snapshot=(self.workshop_readings.snapshot()
                      if self.workshop_readings.context is not None else None)
            if snapshot and self.pending_transition is None:
                self.live_jet,self.live_pool=snapshot
                self.live_after_fusion=False
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
        self.label(popup,'Historique local des tentatives confirmées',17,bold=True).pack(anchor='w',padx=20,pady=16)
        box=tk.Text(popup,bg=PANEL,fg=FG,insertbackground=FG,font=('Consolas',11),relief='flat',padx=15,pady=12)
        box.pack(fill='both',expand=True,padx=20,pady=(0,20))
        rows=recent(100)
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
        self.label(popup,'Conseils et prix des runes',17,bold=True).pack(anchor='w',padx=20,pady=(17,8))
        economic_mode=tk.StringVar(value=settings['strategy'])
        choice=ttk.Combobox(popup,textvariable=economic_mode,values=MODES,state='readonly')
        choice.pack(fill='x',padx=20)
        choice.bind('<<ComboboxSelected>>',lambda event: save_settings({'strategy':economic_mode.get()}))
        self.label(popup,price_reference_label(settings),10,color=MUTED,wraplength=470).pack(anchor='w',padx=20,pady=8)
        self.label(popup,'Budget optimisé favorise la progression par kama. Les probabilités de passage restent inchangées.',10,color=MUTED,wraplength=470).pack(anchor='w',padx=20)
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
                observation_delay_ms=self.last_observation_delay_ms)
            lines=['ÉTAT : '+report.level,
                   'FENÊTRE : '+(self.last_capture_title or 'Non détectée'),
                   'CAPTURE : '+self.capture.debug_stage,
                   'TESSERACT : '+ocr_engine_status(),
                   'MOTIF OBSERVATEUR : '+self.last_reason,
                   'LECTURE RAPIDE (PROVISOIRE) : '+getattr(self, 'fast_preview_reason', 'Non démarrée'),
                   'DÉTAILS LECTURE RAPIDE : '+repr(getattr(self, 'fast_preview_details', {})),
                   'PERFORMANCES LECTURE RAPIDE (ms) : '+repr(self.fast_preview_performance.snapshot() if hasattr(self, 'fast_preview_performance') else {}),
                   'LECTURES : '+str(self.scan_count),
                   'RETARD DERNIÈRE OBSERVATION : '+(f'{self.last_observation_delay_ms:.0f} ms' if self.last_observation_delay_ms is not None else 'Non mesuré'),
                   'CAPTURES AVEC INFOBULLE SUSPECTÉE : '+str(self.occluded_observations),
                   'CAPTURES INCHANGÉES SANS OCR : '+str(getattr(self,'_unchanged_frames_skipped',0)),
                   'CHANGEMENTS VISUELS OBSERVÉS : '+str(getattr(self,'_visual_changes_seen',0)),
                   'FILTRE RAPIDE : comparaison tolérante dans le thread de capture (120 ms)',
                   'CAPTURES MASQUÉES ÉCARTÉES : '+str(getattr(self,'_occluded_frames_rejected',0)),
                   'OCR CADENCE SÉCURITÉ : 12 s sans changement visuel',
                   'OCR SUR IMAGE ANCIENNE (> 1 s) : '+str(getattr(self,'_ocr_stale_frames',0)),
                   'ÂGE DERNIÈRE IMAGE APRÈS OCR : '+str(getattr(self,'_last_ocr_frame_age_ms',None))+' ms',
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
        if self.running:
            self.stop_event.set();self.running=False
            self.frame_mailbox.invalidate('Observation arrêtée')
            self.clear_fast_preview()
            self.observe_button.configure(text='Démarrer l’observation')
            self.overlay.state_color('paused')
            self.status.set('Observation arrêtée · Toutes les données restent locales')
            self.game_state_label.configure(text='● Observateur arrêté',fg=MUTED)
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
        self.workshop_readings.reset();self.workshop_active=False
        self.first_item_name_seen=False;self.before_identity_reading=None;self.item_initial_reading=None
        self.history_has_attempts=False
        self.live_jet=None;self.live_pool=None;self.live_after_fusion=True;self.pre_fusion_sample=None
        self.last_transition_audit=None
        # Never carry a previous session's verified item into a new capture.
        self.active_equipment_verified=False
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
        self.fast_preview_performance = PerformanceTracker()
        self.fast_preview_reason = 'En attente du premier historique stable'
        self.fast_preview_details = {}
        self.last_full_event_frame_id = 0
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
        threading.Thread(target=self.capture_worker,daemon=True).start()
        threading.Thread(target=self.fast_preview_worker,daemon=True).start()
        threading.Thread(target=self.observer_worker,daemon=True).start()
        if self.auto_floating.get():
            # Defer the transition until the start button callback is finished.
            self.after(150,self.minimize_to_badge)
            self.after(250,self.resume_game_after_targets)

    def capture_worker(self):
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
                refresh = started - self._capture_gate_last_sent_ns >= self._capture_gate_force_ns
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
                    self.fast_slot_evidence=rapid_slot.observe(
                        current_icon(im) if workshop_visual_fallback(im) else None,
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
            stop_event.wait(self._capture_interval)
        capture.close()

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
                result = reader.read(image, title, extract_text)
                if generation != mailbox.generation() or stop_event.is_set():
                    reader.reset()
                    continue
                self.fast_preview_performance.record('historique_et_rune', forgely_perf_ns() - started)
                self.fast_preview_reason = reader.reason
                self.fast_preview_details = reader.diagnostic
                if result.context_reset:
                    self.messages.put(('fast_preview_clear', (frame_id, mailbox)))
                if result.needs_confirmation:
                    self.confirmation_requested.set()
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

    def observer_worker(self):
        from forgely_learning import FusionContextTracker
        from forgely_dofocus import natural_profile
        fusion_contexts = FusionContextTracker()
        from forgely_pool_observer import PoolObserver
        pool_observer=PoolObserver()
        pool_cycle=0
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
                atelier = read_atelier(im, extract_text, zone_cache, title_cache)
                if stop_event.is_set():
                    break
                if mailbox is not self.frame_mailbox or generation != mailbox.generation():
                    continue
                perf.record("atelier_et_ocr", forgely_perf_ns() - t_ocr)
                for phase,duration in getattr(atelier,'timings',{}).items():
                    perf.record('atelier_'+phase,duration)
                if getattr(atelier,'recovery_pending',False):
                    self.confirmation_requested.set()
                # This is diagnostic only: never claim a late OCR reading is
                # an instant rune result. A newer frame is already in the mailbox.
                self._last_ocr_frame_age_ms = round((forgely_perf_ns() - frame_started_ns) / 1_000_000, 1)
                if self._last_ocr_frame_age_ms > 1000:
                    self._ocr_stale_frames += 1
                # Count completed OCR passes, including unsuccessful workshop detection.
                # This counter is independent of the Tk message queue and of scans.
                self.completed_ocr_attempts = getattr(self, 'completed_ocr_attempts', 0) + 1
                self.last_ocr_attempt_reason = ('Atelier reconnu' if atelier.active
                                                else 'Atelier non confirmé : ' + atelier.reason)
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
                review_service=getattr(self,'reading_reviews',None)
                numeric_reading=(parse_jet(atelier.effects),choose_reliquat(atelier.effects,atelier.reliquat))
                if atelier.active and review_service is not None:
                    try:
                        from forgely_vision_guidance import reference_for,merge_observation
                        confirmed=getattr(self,'_verified_item_context',None)
                        expected=(reference_for(confirmed.item) if isinstance(confirmed,VerifiedItemContext)
                                  and confirmed.mailbox is mailbox and confirmed.generation==generation
                                  and confirmed.title==title else {})
                        review=review_service.observe(crop_zone(im,'review_effects'),crop_zone(im,'reliquat'),
                            atelier.effects,atelier.reliquat,context=title+' · '+str(getattr(self,'last_item_candidate','')),
                            token=frame_id,expected=expected)
                        if review is not None:
                            jets,puits,source=merge_observation(numeric_reading[0],review['visual_jet'],
                                                              numeric_reading[1],review['visual_pool'])
                            numeric_reading=(jets,puits)
                            review['numeric_source']=source
                            review['eligible_for_live_reading']=source=='hybrid'
                            messages.put(('reading_review_status',review))
                    except Exception as exc:
                        messages.put(('reading_review_status',{'error':str(exc)[:180],'used_for_advice':False}))
                if not atelier.active or (getattr(atelier,'readable',True) is False and not numeric_reading[0]):
                    pool_observer.reset()
                    if atelier.active:
                        capture.reacquire_layout.set()
                        self.confirmation_requested.set()
                        self.last_ocr_attempt_reason=atelier.reason
                        self.last_ocr_text=('HISTORIQUE\n'+atelier.history+'\nEFFETS\n'+atelier.effects+'\nRUNES (Pa / Ra)\n'+atelier.runes+'\nRELIQUAT\n'+atelier.reliquat+'\nVISION\nLecture non exploitable')
                        messages.put(('atelier_waiting',atelier.reason))
                    fusion_contexts.reset()
                    zone_cache.clear()
                    missed_workshop += 1
                    if missed_workshop >= 3:
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
                            self.workshop_readings.reset()
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
                effects_lower = atelier.effects.casefold()
                occluded = any(token in effects_lower for token in (
                    'prix moyen', 'quantité en', 'quantite en', 'comparer avec',
                    'poids 10', 'valeurs théor', 'valeurs theor',
                    'niveau 1', 'panoplie', 'quantité en banque', 'quantite en banque',
                    'quantité en inventaire', 'quantite en inventaire'))
                if occluded:
                    self.occluded_observations += 1
                    self._occluded_frames_rejected += 1
                    # Do not keep a tooltip-contaminated OCR result in cache.
                    zone_cache.entries.pop('effects', None)
                # Resolve verified current-slot references before spending time
                # on header OCR. Unknown/ambiguous icons retain the OCR path.
                t_icon = forgely_perf_ns()
                slot_icon = current_icon(im)
                signature = effect_signature(atelier.effects)
                manual_session=getattr(self,'manual_equipment',None)
                manual_selected=isinstance(manual_session,ManualEquipmentSession)
                visual_name = (match_current_item(slot_icon, signature)
                               if not manual_selected and slot_icon is not None and not occluded else None)
                perf.record("extraction_icone", forgely_perf_ns() - t_icon)
                # A known current-slot reference can identify the equipment.
                # Otherwise retain both OCR views of the active item heading.
                # Neither path bypasses temporal slot/name confirmation.
                try:
                    # Most forgemagie actions leave the item's name untouched.
                    # Avoid launching Tesseract twice for that identical region.
                    header_patch = crop_item_header(im)
                    header_key = (header_patch.size, header_patch.mode,
                                  header_patch.tobytes())
                    cached_header = self._item_header_cache
                    if manual_selected:
                        found,new_name,item_ocr=None,None,'Nom choisi dans le catalogue Forgely'
                    elif visual_name:
                        found, new_name, item_ocr = recognize_item_header(
                            im, extract_text, (), visual_name=visual_name)
                    elif cached_header is not None and cached_header[0] == header_key:
                        found, new_name, item_ocr = cached_header[1]
                        self._item_header_cache_hits += 1
                    else:
                        found, new_name, item_ocr = recognize_item_header(
                            im, extract_text, item_list())
                        self._item_header_cache = (
                            header_key, (found, new_name, item_ocr))
                        self._item_header_cache_misses += 1
                except (OSError, ValueError, RuntimeError) as exc:
                    self._item_header_cache = None
                    found, new_name, item_ocr = None, None, 'OCR nom indisponible: ' + str(exc)
                if stop_event.is_set() or mailbox is not self.frame_mailbox or generation != mailbox.generation():
                    continue
                history_identity = None
                # Read the ACTUAL equipment slot even if the FM history is empty
                # or contains an old item's heading. No game interaction.
                historical_names = visible_history_names(history_text, item_list())
                latest_history_candidate = latest_visible_history_name(history_text, item_list())
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
                    slot_icon, history_identity, history_icon, signature, historical_names, corroborated_history_name, latest_history_candidate))))
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
                       + 'HISTORIQUE\n'+history_text+'\nEFFETS\n'+atelier.effects+'\nRUNES (Pa / Ra)\n'+rune_text+'\nRELIQUAT\n'+atelier.reliquat+'\nVISION\n'+vision_note)
                event = self.track.observe(history_text,selected_rune)
                context_item = bind_event_item(getattr(self,'_verified_item_context',None),
                    mailbox,generation,title,frame_id,slot_icon,signature,found or new_name)
                context_jet = parse_jet(atelier.effects)
                pool_cycle+=1
                pool_name=context_item or (manual_session.equipment.identity_name if manual_selected
                    and not manual_session.invalidated else None)
                if pool_name is None:
                    from forgely_perfect_goal import signature_equipment
                    inferred=signature_equipment(signature)
                    pool_name=inferred.identity_name if inferred is not None else None
                pool_profile=complete_learning_profile(pool_name) if pool_name else None
                numeric_jet,numeric_pool=numeric_reading
                pool_complete=bool(pool_profile and set(pool_profile)<=numeric_jet.keys()
                                   and slot_icon is not None and not occluded)
                pool_context=(id(mailbox),generation,title,pool_name,
                              slot_icon.tobytes() if slot_icon is not None else None)
                tracking=pool_observer.observe(pool_context,history_text,numeric_jet,numeric_pool,event,
                                               pool_complete,pool_cycle)
                if tracking['pending']:self.confirmation_requested.set()
                if numeric_pool is None and tracking['origin']=='calculated' and tracking['value'] is not None:
                    numeric_pool=float(tracking['value'])
                messages.put(('observation',(frame_id,frame_started_ns,'pool_tracking',tracking)))
                if not occluded:
                    messages.put(('observation',(frame_id,frame_started_ns,'atelier_read',(numeric_jet,numeric_pool))))
                profile=complete_learning_profile(context_item) if context_item else None
                from forgely_dofocus import normalise_jet
                complete=profile is not None and set(profile).issubset(normalise_jet(context_jet) or {}) and not occluded
                transition = fusion_contexts.observe(context_item if complete else None,
                    history_text, context_jet, choose_reliquat(atelier.effects, atelier.reliquat), event)
                if transition is not None and event is None:
                    messages.put(('learning_transition', (context_item, transition)))
                if fusion_contexts.pending_event is not None:
                    self.confirmation_requested.set()
                if (self.track.pending_count or
                    (self.track.baseline is None and self.track._init_count == 1) or
                    self.history_delta_monitor.pending is not None):
                    # Request independent OCR on a fresh capture, without
                    # waiting for the twelve-second idle refresh.
                    zone_cache.entries.pop('history', None)
                    self.confirmation_requested.set()
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

    def record_learning(self,item,rune,outcome,before,after):
        """Persist once, publish new experience, then refresh visible advice."""
        from forgely_online_experience import OnlineExperience
        if not OnlineExperience(max_samples=1).observe(1,item,rune,outcome,before,after):
            raise ValueError('Transition contradictoire ou incomplète : exclue de l’apprentissage')
        from forgely_dofocus import normalise_jet
        profile=complete_learning_profile(item)
        if not profile or any(not set(profile).issubset(normalise_jet(state['jet']) or {}) for state in (before,after)):
            raise ValueError('Profil complet et toutes ses lignes lus avant/après requis pour apprendre')
        started=forgely_perf_ns()
        delta=save_transition(item,rune,outcome,before,after,event_confirmed=True)
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
        self.learning_summary.set(summary)
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

    def process_messages(self):
        pump_started=forgely_perf_ns()
        try:
            for index in range(64):
                if index and forgely_perf_ns()-pump_started >= 8_000_000:
                    break
                kind,data=self.messages.get_nowait()
                source_context=None
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
                if kind=='capture_invalidated':
                    mailbox,generation,reason=data
                    if mailbox is not self.frame_mailbox or generation!=mailbox.generation():
                        continue
                    kind,data='atelier_waiting',reason
                if kind=='accepted_event':
                    receipt=data
                    event=receipt.event
                    learning_receipt=True
                    try:
                        if receipt.item and event.rune:
                            insert_observation(receipt.item,event.rune,event.outcome,'ocr_auto',event.evidence)
                            self.saved_auto+=1
                            if receipt.transition is not None:
                                try:
                                    self.record_learning(receipt.item,event.rune,event.outcome,
                                        receipt.transition['before'],receipt.transition['after'])
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
                    kind,data='auto_event_frame',(receipt.frame_id,event)
                if kind=='learning_transition':
                    context_item, transition = data
                    try:
                        self.record_learning(context_item,transition['rune'],transition['outcome'],
                            transition['before'],transition['after'])
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
                if kind == 'observation':
                    frame_id, frame_started_ns, kind, data = data
                    # Keep the two most recent samples for stability checks,
                    # but discard stale UI work. Do not discard rune events.
                    if frame_id < self.latest_observation_id - 1:
                        continue
                    self.last_observation_delay_ms = (
                        forgely_perf_ns() - frame_started_ns) / 1_000_000
                if kind=='item_visual':
                    known, new_name, raw, slot_icon, history_identity, history_icon, signature, historical_names, corroborated_history_name, latest_history_candidate = data
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
                    stable, changed=self.current_slot_tracker.observe(slot_icon, signature)
                    if changed:
                        self.clear_fast_preview()
                        # A different icon in the actual workshop means a new
                        # item, even if the history still shows the OLD name.
                        self.active_equipment_verified=False
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
                        self.workshop_readings.reset()
                        self.before_identity_reading=None
                        self.refresh_strategy()
                    if slot_icon is None:
                        self.workshop_readings.reset()
                        self.live_jet=None;self.live_pool=None;self.live_after_fusion=True
                        self.clear_fast_preview()
                        self.current_slot_status='Icône absente ou illisible'
                        self.last_item_candidate=''
                        self.item_icon_status='Emplacement actuel non lisible'
                        if self.current_slot_tracker.misses>=3:
                            self.workshop_readings.reset()
                            self.active_equipment_verified=False
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
                            self.confirmation_requested.set()
                        self.item_icon_status='Stabilisation de l’icône actuelle'
                        self.refresh_strategy()
                        continue
                    # Strict icon-first identification. Never derive an item's
                    # name from rune history, even when a historical row matches.
                    # A named reference must already exist in the icon catalogue.
                    matched=match_current_item(slot_icon, self.current_slot_tracker.signature)
                    # The old reference is not allowed to survive a strong
                    # change of natural effect ranges. Never recycle its pool.
                    if matched:
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
                            self.active_equipment_verified=False
                            self.item_selection_source='none'
                            self.live_jet=None; self.live_pool=None
                            self.live_after_fusion=True; self.pending_transition=None
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
                            else self.item_visual_tracker.observe(name,slot_icon))
                    threshold=1 if fast_slot and matched else 3
                    self.item_icon_status=f'Objet actuel et nom cohérents · {min(streak,threshold)}/{threshold}'
                    if streak<threshold:
                        if getattr(self, 'confirmation_requested', None) is not None:
                            self.confirmation_requested.set()
                        self.refresh_strategy()
                        continue
                    try:
                        # Never register a name from stale history. The current
                        # slot icon and a confirmed source are mandatory.
                        registered=register_item(name)
                        name=registered[1]
                        remember_current_item(name,slot_icon,self.current_slot_tracker.signature)
                        if item_icon(name) is None:
                            register_item_with_icon(name,slot_icon)
                    except (ValueError,OSError,__import__('sqlite3').Error) as exc:
                        self.item_icon_status='Conflit ou erreur : '+str(exc)
                        self.active_equipment_verified=False
                        self.refresh_strategy()
                        continue
                    self.provisional_slot_id=None
                    self.item_icon_status='Icône de l’atelier reconnue : '+name
                    if source_context is not None:
                        context_mailbox,context_generation,context_title=source_context
                        self._verified_item_context=VerifiedItemContext(context_mailbox,context_generation,
                            context_title,frame_id,name,slot_icon.copy(),tuple(self.current_slot_tracker.signature))
                    if self.item.get()!=name or not self.active_equipment_verified:
                        self.item.set(name)
                        self.active_equipment_verified=True
                        self.item_selection_source='ocr'
                        stable_snapshot=(self.workshop_readings.snapshot()
                                         if self.workshop_readings.context is not None else None)
                        if stable_snapshot and self.pending_transition is None:
                            self.live_jet,self.live_pool=stable_snapshot
                            self.live_after_fusion=False
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
                elif kind=='atelier_read':
                    jet,puits=data
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
                    previous_sample=self.workshop_readings.sample
                    stable=self.workshop_readings.observe(jet,puits,
                        sequence=frame_id if source_context is not None else None)
                    if (not stable and jet and puits is not None and
                            self.workshop_readings.streak < self.workshop_readings.required_frames):
                        # Ask for another distinct capture now, instead of
                        # waiting for the long idle refresh after a rune.
                        self.confirmation_requested.set()
                    if stable:
                        jet,puits=self.workshop_readings.snapshot()
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
                                    self.record_learning(pending['item'],pending['rune'],pending['outcome'],
                                        pending['before'],{'jet':dict(jet),'pool':puits})
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
                    matching_plan=(self.active_equipment_verified and self.plan and self.plan.get('item')==self.item.get()
                                   and any(v.get('target') is not None for v in self.plan.get('stats',{}).values()))
                    if (stable and not matching_plan and isinstance(measured,MeasuredGoals) and measured.icon is not None
                            and not measured.targets and not measured.prompted and not self.observation_only):
                        self.after(0,self.prompt_measured_goals)
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
                    self.last_transition_audit=None
                    # Save last stable pre-fusion state BEFORE invalidating it.
                    before=(dict(self.live_jet),self.live_pool) if self.live_jet is not None else None
                    self.pre_fusion_sample=(tuple(sorted(before[0].items())),before[1]) if before else None
                    if not learning_receipt and before and self.workshop_readings.atomic_snapshot and data.rune and self.active_equipment_verified and self.item.get().strip():
                        self.pending_transition={'item':self.item.get().strip(),
                            'rune':data.rune,'outcome':data.outcome,'sample':self.pre_fusion_sample,
                            'before':{'jet':before[0],'pool':before[1]}}
                    else:
                        self.pending_transition=None
                    self.live_after_fusion=True;self.live_jet=None;self.live_pool=None;self.workshop_readings.invalidate()
                    self.confirmation_requested.set()
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
                                insert_observation(self.item.get().strip(),data.rune,data.outcome,'ocr_auto',data.evidence)
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
                    manual_session=getattr(self,'manual_equipment',None)
                    if isinstance(manual_session,ManualEquipmentSession):
                        manual_session.invalidate('Compte changé : sélectionne à nouveau ton objet.')
                        self._verified_item_context=None
                    self.clear_fast_preview()
                    self.workshop_active=False
                    self.active_equipment_verified=False
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
                    manual_session=getattr(self,'manual_equipment',None)
                    if isinstance(manual_session,ManualEquipmentSession):
                        manual_session.workshop_lost()
                        self._verified_item_context=None
                    self.clear_fast_preview()
                    self.workshop_active=False
                    self.workshop_readings.reset()
                    self.first_item_name_seen=False
                    self.before_identity_reading=None
                    self.item_initial_reading=None
                    self.active_equipment_verified=False
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
                    self.game_state_label.configure(text='● Atelier non confirmé',fg=GOLD)
                    self.overlay.state_color('waiting')
                elif kind=='error':self.status.set('Capture : '+data)
                elif kind=='waiting_window':
                    self.status.set('En attente du jeu : '+data)
                    self.game_state_label.configure(text='● En pause · DOFUS non visible',fg=GOLD)
                    self.overlay.state_color('waiting')
                elif kind=='fatal':
                    self.status.set('Observation stoppée : '+data)
                    self.running=False;self.stop_event.set();self.observe_button.configure(text='Démarrer l’observation');self.overlay.state_color('error')
                    self.game_state_label.configure(text='● Erreur de lecture',fg=RED)
        except queue.Empty: pass
        if getattr(self, 'dashboard', None) is not None:
            self.dashboard.sync()
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
            self.overlay.state_color('active' if self.running else 'paused')
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
        self.refresh_stats()

    def refresh_stats(self):
        timer=getattr(self,'_stats_refresh_timer',None)
        if timer is not None:
            self.after_cancel(timer)
        self._stats_refresh_timer=None
        self.refresh_stats_now()
        self._stats_refresh_timer=self.after(2500,self.refresh_stats)

    def refresh_stats_now(self):
        n,counts=stats(item=self.item.get().strip())
        if isinstance(getattr(self,'simulation_journal',None),SimulationJournal):
            name=self.item.get().strip()
            ident=self.simulator.item_id(name) if name else None
            virtual=self._virtual_totals.get(ident,0) if name else sum(self._virtual_totals.values())
            self.simulation_totals.set(f'Réelles : {n} · Simulées : {virtual} · Total : {n+virtual}')
        self.total_lbl.configure(text=f'{n} tentative'+('s' if n!=1 else ''))
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
        self.overlay.state_color('active' if self.running else 'paused')
        self.overlay.deiconify();self.withdraw()

    def restore(self):
        self.deiconify();self.lift();self.overlay.withdraw()

    def close(self):
        if isinstance(getattr(self,'simulator',None),SimulationWorker):self.simulator.stop()
        self.live_laboratory.stop()
        self.stop_event.set()
        if hasattr(self,'overlay'):self.overlay.destroy()
        self.destroy()


if __name__=='__main__':
    Forgely().mainloop()
