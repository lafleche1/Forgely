"""Read visible stat losses/gains without inventing rune outcomes."""
import re
from forgely_jet import parse_jet, norm


def summarize_history(text):
    lines = [line.strip() for line in (text or '').splitlines() if line.strip()]
    changes = []
    for line in lines:
        # An OCR line can contain an icon before the signed value.
        # Require an EXPLICIT sign; a bare value is not a historical delta.
        if not re.search(r'(?<!\d)[+-]\s*(?:[^\W\d_]{1,2}\s+)?\d+', line):
            continue
        # OCR can insert one icon glyph between a sign and its value:
        # "+ À 30 Initiative" is an observed +30, not an unsigned 30.
        cleaned = re.sub(r'(?<!\w)([+-])\s+[^\W\d_]{1,2}\s+(?=\d)', r'\1', line)
        parsed = parse_jet(cleaned)
        if len(parsed) == 1:
            stat, value = next(iter(parsed.items()))
            if value != 0:
                changes.append((stat, value))
    folded = norm(text or '')
    return {
        'visible_stat_changes': len(changes),
        'recent_changes': changes[:8],
        'reliquat_mentioned': bool(re.search(r'\b(?:reliquat|rel[i1]quat)\b', folded)),
        'has_explicit_outcome': bool(re.search(r'\b(?:echec|succes|reussite)\b', folded)),
        'rune_attempt_confirmed': False,
    }
