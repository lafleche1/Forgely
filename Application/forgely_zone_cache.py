"""Fast exact-frame cache for OCR regions; never reuse text after a pixel change."""
from time import monotonic

class ZoneCache:
    def __init__(self, refresh_seconds=12.0):
        self.refresh_seconds = refresh_seconds
        self.entries = {}
        self.confirmed_numeric = {}
        self.hits = 0
        self.misses = 0

    def clear(self):
        self.entries.clear()
        self.confirmed_numeric.clear()

    def discard(self,zone):
        self.entries.pop(zone,None)
        self.confirmed_numeric.pop(zone,None)

    def confirm_numeric(self, entries):
        """Pin only actually confirmed jet/pool OCR, under exact source pixels."""
        self.confirmed_numeric={zone:entry for zone,entry in entries
                                if zone in ('effects','current_jet','reliquat')}

    def should_read(self, zone, image):
        entry = self.entries.get(zone)
        if entry is None:
            return True
        signature, _, timestamp = entry
        if monotonic() - timestamp >= self.refresh_seconds:
            return True
        # PIL's tobytes is native code; equality is exact, not a perceptual
        # hash. Any pixel change triggers OCR, including a minus sign.
        return signature != (image.size, image.mode, image.tobytes())

    def remember(self, zone, image, text):
        self.entries[zone] = ((image.size, image.mode, image.tobytes()), text, monotonic())

    def get(self, zone):
        entry = self.entries.get(zone)
        return entry[1] if entry else None

    def retry_unresolved(self,zone,interval=1.0):
        """Expire an incomplete result without repeatedly OCRing good zones."""
        entry=self.entries.get(zone)
        if entry is None or monotonic()-entry[2]<interval:return False
        self.entries.pop(zone,None)
        self.confirmed_numeric.pop(zone,None)
        return True

    def read(self, zone, image, reader):
        # Compute image bytes once per read, rather than comparing PIL images
        # and copying large RGB regions on every capture.
        now = monotonic()
        signature = (image.size, image.mode, image.tobytes())
        confirmed=self.confirmed_numeric.get(zone)
        if confirmed is not None and confirmed[0]==signature:
            self.hits+=1
            # Preserve the original provenance for a subsequent confirmation.
            self.entries[zone]=confirmed
            return confirmed[1]
        previous = self.entries.get(zone)
        # Incomplete effects OCR is rechecked soon, even with identical pixels.
        # Avoid expensive identical-image OCR retries every 750 ms.
        # Changed pixels always invalidate the cache immediately. A periodic
        # retry is retained for unresolved readings, but at most every 8 s.
        ttl = self.refresh_seconds
        # Text on an unchanged panel cannot acquire new rune events.
        # Recheck periodically only as a safeguard against OCR errors.
        if zone == 'effects' and previous:
            from forgely_jet import parse_jet
            parsed = parse_jet(previous[1])
            if not parsed or 'Vitalité' not in parsed or 'Tacle' not in parsed:
                ttl = min(ttl, 8.0)
        if previous and previous[0] == signature and now - previous[2] < ttl:
            self.hits += 1
            return previous[1]
        self.misses += 1
        result = reader(image)
        self.entries[zone] = (signature, result, monotonic())
        return result
