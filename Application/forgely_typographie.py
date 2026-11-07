"""Police ronde et lisible, sans distribution de polices tierces."""
import tkinter.font as tkfont

def families(root):
    try:
        installed=set(tkfont.families(root))
    except Exception:
        installed=set()
    def first(*names):
        return next((n for n in names if n in installed), "TkDefaultFont")
    return {
        "display": first("Segoe UI Semibold", "Segoe UI", "Inter", "DejaVu Sans", "Arial"),
        "body": first("Segoe UI", "Inter", "DejaVu Sans", "Arial", "TkDefaultFont"),
    }
