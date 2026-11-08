"""Display mode regressions, runnable with unittest without OCR dependencies."""
import ast
import ctypes
from pathlib import Path
import queue
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import forgely_windows as windows
from forgely_pipeline import FrameMessageSink


def capture_namespace():
    source = Path(__file__).resolve().parents[1] / 'forgely.py'
    tree = ast.parse(source.read_text(encoding='utf8'))
    names = {'GameCapture', 'GameNotForeground', 'LatestFrameMailbox'}
    body = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in names]
    app = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Forgely')
    body += [n for n in app.body if isinstance(n, ast.FunctionDef) and n.name == 'capture_worker']
    ns = dict(vars(windows), threading=threading, Image=Image, focus_workshop=lambda im: im)
    # Decorators are evaluated only after the production helper is available.
    exec(compile(ast.Module(body=body, type_ignores=[]), str(source), 'exec'), ns)
    return ns


class DisplayModes(unittest.TestCase):
    def api(self, outer=(100, 50, 1116, 889), client=(0, 0, 1000, 800), origin=(108, 81)):
        def rect_result(values):
            def fill(handle, pointer):
                rect = pointer._obj
                rect.left, rect.top, rect.right, rect.bottom = values
                return 1
            return fill
        def screen(handle, pointer):
            pointer._obj.x += origin[0]
            pointer._obj.y += origin[1]
            return 1
        return SimpleNamespace(GetWindowRect=Mock(side_effect=rect_result(outer)),
            GetClientRect=Mock(side_effect=rect_result(client)), ClientToScreen=Mock(side_effect=screen))

    def test_win32_client_corners_use_screen_coordinates(self):
        api = self.api(outer=(-1936, -8, 16, 1111), client=(0, 0, 1920, 1080), origin=(-1920, 23))
        outer, client = windows.read_window_bounds(12, api)
        self.assertEqual(outer, (-1936, -8, 16, 1111))
        self.assertEqual(client, (-1920, 23, 0, 1103))

    def test_win32_failures_never_guess_border_sizes(self):
        for name in ('GetWindowRect', 'GetClientRect', 'ClientToScreen'):
            api = self.api()
            setattr(api, name, Mock(return_value=0))
            with self.subTest(api=name), self.assertRaises(OSError):
                windows.read_window_bounds(12, api)

    def test_empty_and_inconsistent_client_bounds_rejected(self):
        for size in ((0, 0, 0, 0), (0, 0, 1920, 1080)):
            with self.subTest(size=size), self.assertRaises(OSError):
                windows.read_window_bounds(12, self.api(client=size))

    def test_dpi_context_is_scoped_and_restored_after_error(self):
        api = SimpleNamespace(SetThreadDpiAwarenessContext=Mock(return_value=123))
        with patch.object(ctypes, 'WinDLL', return_value=api, create=True):
            with self.assertRaises(ValueError):
                with windows.physical_pixels():
                    raise ValueError('capture failed')
        calls = api.SetThreadDpiAwarenessContext.call_args_list
        self.assertEqual(calls[0].args[0].value, ctypes.c_void_p(-4).value)
        self.assertEqual(calls[-1].args, (123,))

    def test_dpi_v1_fallback(self):
        api = SimpleNamespace(SetThreadDpiAwarenessContext=Mock(side_effect=[None, 123, 123]))
        with patch.object(ctypes, 'WinDLL', return_value=api, create=True):
            with windows.physical_pixels():
                pass
        self.assertEqual(api.SetThreadDpiAwarenessContext.call_args_list[1].args[0].value,
                         ctypes.c_void_p(-3).value)

    def test_windowed_geometry_excludes_title_and_borders(self):
        w = windows.NativeWindow(12, 'DOFUS', (100, 50, 1116, 889),
                                 client_rect=(108, 81, 1108, 881))
        self.assertEqual((w.left, w.top, w.width, w.height), (108, 81, 1000, 800))
        self.assertEqual(w.outer_rect, (100, 50, 1116, 889))

    def test_fullscreen_geometry_and_negative_monitor(self):
        w = windows.NativeWindow(12, 'DOFUS', (-1920, 0, 0, 1080),
                                 client_rect=(-1920, 0, 0, 1080))
        self.assertEqual((w.left, w.top, w.width, w.height), (-1920, 0, 1920, 1080))

    def test_capture_automatically_uses_client_surface_in_both_modes_and_backends(self):
        for outer, client in (((100, 50, 1116, 889), (108, 81, 1108, 881)),
                              ((-1920, 0, 0, 1080), (-1920, 0, 0, 1080))):
            for foreground in (True, False):
                with self.subTest(client=client, foreground=foreground):
                    ns = capture_namespace()
                    w = windows.NativeWindow(12, 'DOFUS', outer, client_rect=client)
                    frame = Image.new('RGB', (w.width, w.height), 'blue')
                    frame.paste('white', (w.width//3, 0, w.width//2, w.height))
                    full = Image.new('RGB', (outer[2]-outer[0], outer[3]-outer[1]), 'red')
                    full.paste(frame, (client[0]-outer[0], client[1]-outer[1]))
                    ns.update(foreground_handle=lambda: 12 if foreground else 99,
                        list_dofus_windows=lambda: [w],
                        foreground_belongs_to_game=lambda *args: foreground,
                        capture_window_native=lambda *args: full,
                        read_window_bounds=lambda handle: (outer, client))
                    cap = ns['GameCapture']()
                    cap._foreground_image = Mock(return_value=frame)
                    # Geometry-only fixture: workshop recognition is tested separately.
                    cap._focus_workshop = Mock(side_effect=lambda image,handle:image)
                    result, title = cap.capture()
                    self.assertEqual(result.size, frame.size)
                    self.assertEqual(result.tobytes(), frame.tobytes())
                    self.assertEqual((title, cap.last_handle), ('DOFUS', 12))

    def test_native_backend_crops_same_surface_as_foreground(self):
        ns = capture_namespace()
        w = windows.NativeWindow(12, 'DOFUS', (100, 50, 1116, 889),
                                 client_rect=(108, 81, 1108, 881))
        full = Image.new('RGB', (1016, 839), 'red')
        full.paste('blue', (8, 31, 1008, 831))
        full.paste('white', (400, 31, 600, 831))
        native = Mock(return_value=full)
        ns['capture_window_native'] = native
        cap = ns['GameCapture']()
        result = cap._native_image(w)
        self.assertEqual(result.size, (1000, 800))
        self.assertEqual(result.getpixel((0, 0)), (0, 0, 255))
        self.assertEqual(result.getpixel((999, 799)), (0, 0, 255))
        native.assert_called_once_with(12, 1016, 839)

    def test_native_black_client_rejected_despite_visible_decorations(self):
        ns = capture_namespace()
        w = windows.NativeWindow(12, 'DOFUS', (0, 0, 1016, 839),
                                 client_rect=(8, 31, 1008, 831))
        full = Image.new('RGB', (1016, 839), 'white')
        full.paste('black', (8, 31, 1008, 831))
        ns['capture_window_native'] = Mock(return_value=full)
        self.assertIsNone(ns['GameCapture']()._native_image(w))

    def test_native_wrong_size_is_rejected_without_padded_pixels(self):
        ns = capture_namespace()
        w = windows.NativeWindow(12, 'DOFUS', (0, 0, 1016, 839),
                                 client_rect=(8, 31, 1008, 831))
        ns['capture_window_native'] = Mock(return_value=Image.new('RGB', (800, 600)))
        self.assertIsNone(ns['GameCapture']()._native_image(w))

    def test_mode_switch_invalidates_old_ocr_even_with_same_visual_signature(self):
        ns = capture_namespace()
        stop = threading.Event()
        mailbox = ns['LatestFrameMailbox']()
        old = Image.new('RGB', (1000, 800))
        new = Image.new('RGB', (1920, 1080))
        title = 'DOFUS'
        mailbox.publish(old, title, 1, 0)
        stale_results = queue.Queue()
        stale_sink = FrameMessageSink(stale_results, mailbox, mailbox.generation(), title, stop)
        obj = SimpleNamespace(stop_event=stop, confirmation_requested=threading.Event(),
            capture=Mock(last_handle=12), frame_mailbox=mailbox, messages=queue.Queue(),
            _capture_interval=0, _capture_gate_reference='same', _capture_gate_last_sent_ns=100,
            _capture_gate_force_ns=12_000_000_000, _visual_changes_seen=0,
            _capture_gate_changes=0, _unchanged_frames_skipped=0,
            _capture_gate_identity=None)
        obj.capture.capture.side_effect = [(old, title), (new, title)]
        ns.update(workshop_change_signature=lambda im: 'same',
                  workshop_significantly_changed=lambda *args: False,
                  forgely_perf_ns=lambda: 200)
        waits = []
        def finish(*_):
            waits.append(1)
            if len(waits) == 2:
                stop.set()
        with patch.object(stop, 'wait', side_effect=finish):
            ns['capture_worker'](obj)
        self.assertGreater(mailbox.generation(), 0)
        self.assertIs(mailbox.snapshot()[1][1], new)
        # A slow OCR job from before the resize cannot publish its result.
        stop.clear()
        stale_sink.put(('auto_event_frame', (1, 'old rune result')))
        self.assertTrue(stale_results.empty())

    def test_resize_during_capture_is_rejected(self):
        ns = capture_namespace()
        w = windows.NativeWindow(12, 'DOFUS', (0, 0, 1000, 800),
                                 client_rect=(0, 0, 1000, 800))
        ns.update(foreground_handle=lambda: 12, list_dofus_windows=lambda: [w],
                  foreground_belongs_to_game=lambda *args: True,
                  read_window_bounds=lambda handle: ((0, 0, 1920, 1080), (0, 0, 1920, 1080)))
        cap = ns['GameCapture']()
        cap._foreground_image = Mock(return_value=Image.new('RGB', (1000, 800)))
        with self.assertRaises(ns['GameNotForeground']):
            cap.capture()


if __name__ == '__main__':
    unittest.main()
