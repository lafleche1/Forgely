"""Windows-only selection of DOFUS game windows without a character name.

Selection uses foreground DOFUS window if available; otherwise the single
matching window, or the largest candidate. Do not mistake the app itself for
DOFUS. The optional executable-name verification is intentionally not required:
Windows permissions / the game launcher may block process name reads.
"""
from __future__ import annotations
import re

# Character - class - 3.7.13.17 - Release / Beta patterns observed in DOFUS 3.
DOFUS_TITLE = re.compile(r'\bDOFUS\b|\b\d+\.\d+\.\d+(?:\.\d+)?\s*-\s*(?:Release|Beta)\b', re.I)


def looks_like_dofus(title: str) -> bool:
    return bool(title and DOFUS_TITLE.search(title) and not title.lower().startswith('forgely'))


def select_window(windows, active_handle=None):
    """Select a plausible active DOFUS window, or None.

    It is safer not to select a minimized/very small game window. When two
    candidates are similarly likely with no foreground match, return None.
    """
    candidates = [w for w in windows if looks_like_dofus(w.title)
                  and w.width >= 300 and w.height >= 300 and not w.isMinimized]
    if not candidates:
        return None
    if active_handle is not None:
        for w in candidates:
            if getattr(w, '_hWnd', None) == active_handle:
                return w
    if len(candidates) == 1:
        return candidates[0]
    # User may alt-tab to Forgely: prefer last active game handle provided by caller.
    return None


class NativeWindow:
    """Minimal HWND adapter, independent of pygetwindow enumeration."""
    def __init__(self, handle, title, rect, minimized=False):
        self._hWnd = handle
        self.title = title
        self.left, self.top, right, bottom = rect
        self.width = right - self.left
        self.height = bottom - self.top
        self.isMinimized = minimized


def native_windows():
    """Enumerate visible top-level HWNDs with pointer-sized Windows signatures."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    found = []

    @callback_type
    def visit(hwnd, unused):
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            return True
        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        if rect.right - rect.left < 300 or rect.bottom - rect.top < 300:
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, len(buf))
        found.append(NativeWindow(int(hwnd), buf.value,
                                  (rect.left, rect.top, rect.right, rect.bottom)))
        return True

    if not user32.EnumWindows(visit, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return found


def list_dofus_windows():
    """Identify Dofus.exe HWNDs without relying on pygetwindow or character names."""
    try:
        windows = native_windows()
    except (OSError, AttributeError):
        import pygetwindow as gw
        windows = gw.getAllWindows()
    return [w for w in windows if is_game_window(w)
            and w.width >= 300 and w.height >= 300 and not w.isMinimized]


def foreground_handle():
    import ctypes
    return ctypes.windll.user32.GetForegroundWindow()


def list_selectable_windows():
    """Visible desktop windows for explicit user selection; never auto-pick unrelated apps."""
    import pygetwindow as gw
    return [w for w in gw.getAllWindows() if w.title.strip()
            and w.width >= 300 and w.height >= 300 and not w.isMinimized
            and not w.title.lower().startswith('forgely')]


def window_by_handle(handle, windows):
    return next((w for w in windows if getattr(w, '_hWnd', None) == handle), None)


def process_executable(handle):
    """Read the full image name for the PID owning an HWND (64-bit safe)."""
    if not handle:
        return ''
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                       wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(wintypes.HWND(handle), ctypes.byref(pid))
        if not pid.value:
            return ''
        process = kernel32.OpenProcess(0x1000, False, pid.value)
        if not process:
            return ''
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(buffer))
            if kernel32.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
                return buffer.value.rsplit('\\', 1)[-1].lower()
        finally:
            kernel32.CloseHandle(process)
    except (OSError, AttributeError, ValueError):
        pass
    return ''


def is_game_window(window):
    """Accept a verified game executable OR the distinctive DOFUS 3 title.

    A process lookup may return a launcher/helper executable, or be denied by
    Windows. The DOFUS version/Release window title is a reliable independent
    fallback, provided the window is not one of our own windows.
    """
    title = getattr(window, 'title', '') or ''
    if title.casefold().startswith('forgely'):
        return False
    exe = process_executable(getattr(window, '_hWnd', 0))
    if exe in ('dofus.exe', 'dofus unity.exe', 'dofusunity.exe') or exe.startswith('dofus'):
        return True
    # Strict versioned title fallback, not a generic substring like "Dofus".
    return bool(re.search(r'\b\d+\.\d+\.\d+(?:\.\d+)?\s*-\s*(?:Release|Beta)\b', title, re.I))


def auto_game_window(windows, foreground=None, last_handle=None):
    candidates=[w for w in windows if w.width>=300 and w.height>=300
                and not w.isMinimized and is_game_window(w)]
    for handle in (foreground,last_handle):
        for w in candidates:
            if handle is not None and getattr(w,'_hWnd',None)==handle:
                return w
    return candidates[0] if len(candidates)==1 else None


def is_own_foreground(handle):
    """Allow the app's own overlay to be foreground, never another application."""
    try:
        import ctypes, os
        from ctypes import wintypes
        pid=wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(wintypes.HWND(handle),ctypes.byref(pid))
        return pid.value == os.getpid()
    except Exception:
        return False
