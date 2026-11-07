"""Conservative rolling OCR history monitor (never certifies a rune outcome).

Rows are ordered, repetitions are significant.  A new batch is emitted only
once after two matching reads; uncertainty is explicit when OCR or scrolling
prevents reliable alignment.
"""
from forgely_history_summary import summarize_history


def tokens(text):
    result = []
    for line in (text or '').splitlines():
        parsed = summarize_history(line)['recent_changes']
        if len(parsed) == 1:
            result.append(parsed[0])
    return result


def _extension(old, new):
    """Return (additions, direction, overlap) only for a defensible alignment."""
    if not old:
        return None
    if old == new:
        return ([], 'identique', len(old))
    candidates = []
    # Growing history, or history scrolling out at the opposite edge.
    for overlap in range(min(len(old), len(new)), 0, -1):
        if old[-overlap:] == new[:overlap] and len(new) > overlap:
            candidates.append((new[overlap:], 'bas', overlap))
        if old[:overlap] == new[-overlap:] and len(new) > overlap:
            candidates.append((new[:-overlap], 'haut', overlap))
    if not candidates:
        return None
    best = max(c[2] for c in candidates)
    top = [c for c in candidates if c[2] == best]
    # A single repeated stat is not enough to anchor a scrolled history.
    if best < 2 or len({(c[1], tuple(c[0])) for c in top}) != 1:
        return None
    return top[0]


class HistoryDeltaMonitor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.previous = None
        self.pending = None
        self.confirmed_batches = 0
        self.uncertain_changes = 0
        self.total_observed_new_rows = 0
        self.last_confirmed = []
        self.last = {'status': 'reference_non_etablie', 'new_changes': [], 'certified': False}

    def _report(self, status, current, **fields):
        self.last = {
            'status': status, 'visible': len(current), 'new_changes': [],
            'last_confirmed_changes': list(self.last_confirmed),
            'confirmed_batches': self.confirmed_batches,
            'observed_new_rows': self.total_observed_new_rows,
            'uncertain_transitions': self.uncertain_changes,
            'certified': False, **fields,
        }
        return self.last

    def observe(self, text):
        current = tokens(text)
        if self.previous is None:
            self.previous = current
            return self._report('reference_initiale', current)
        if current == self.previous:
            self.pending = None
            return self._report('historique_inchange', current)
        if self.pending is not None and current == self.pending['snapshot']:
            candidate = self.pending
            self.pending = None
            self.previous = current
            if candidate['additions']:
                self.confirmed_batches += 1
                self.total_observed_new_rows += len(candidate['additions'])
                self.last_confirmed = list(candidate['additions'])
                return self._report('nouvelles_lignes_confirmees_2_lectures', current,
                                    new_changes=list(candidate['additions']),
                                    direction=candidate['direction'],
                                    overlap=candidate['overlap'])
            self.uncertain_changes += 1
            return self._report('nouvelle_reference_apres_changement_ambigu', current)
        match = _extension(self.previous, current)
        if match is not None:
            additions, direction, overlap = match
            self.pending = {'snapshot': current, 'additions': additions,
                            'direction': direction, 'overlap': overlap}
            return self._report('extension_a_confirmer', current,
                                candidate_changes=list(additions),
                                direction=direction, overlap=overlap)
        # Require two identical observations before rebaselining a scroll/OCR
        # mismatch. Never treat the unaligned rows as confirmed rune attempts.
        self.uncertain_changes += 1
        self.pending = {'snapshot': current, 'additions': [],
                        'direction': 'ambigu', 'overlap': 0}
        return self._report('changement_ambigu_a_confirmer', current,
                            reason='OCR, lignes repetees ou defilement sans ancrage fiable')
