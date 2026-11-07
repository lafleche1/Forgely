"""Fast exact-frame cache for OCR regions; never reuse text after a pixel change."""
from time import monotonic

class ZoneCache:
    def __init__(self, refresh_seconds=12.0):
        self.refresh_seconds = refresh_seconds
        self.entries = {}
        self.hits = 0
        self.misses = 0

    def clear(self):
        self.entries.clear()

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

    def read(self, zone, image, reader):
        # Compute image bytes once per read, rather than comparing PIL images
        # and copying large RGB regions on every capture.
        now = monotonic()
        signature = (image.size, image.mode, image.tobytes())
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
