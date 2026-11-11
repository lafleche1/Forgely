"""Locate the workshop header by geometry, then verify independent FM regions.

No full-screen OCR. Only a confirmed, coherent layout may be normalized.
Ambiguous layouts retain no learned transform and cannot borrow an old frame.
"""
from time import monotonic
from PIL import Image, ImageFilter
from forgely_atelier import workshop_visual_fallback


def header_bands(image):
    """Candidate purple horizontal strips; never proof of a workshop alone."""
    width = min(400, image.width)
    height = max(1, round(image.height * width / image.width))
    small = image.convert('RGB').resize((width, height))
    pixels = small.getdata()
    mask = Image.new('L', small.size)
    mask.putdata([255 if 28 <= r <= 145 and 28 <= g <= 145 and
                  48 <= b <= 170 and b >= r+8 and b >= g+8 else 0
                  for r, g, b in pixels])
    # Close the small holes made by header letters without joining panels
    # separated by the larger dark gaps in DOFUS's layout.
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    data = mask.tobytes()
    active = {}
    bands = []
    for y in range(height):
        row = data[y*width:(y+1)*width]
        runs = set()
        left = 0
        while left < width:
            left = row.find(b'\xff', left)
            if left < 0:
                break
            right = row.find(b'\x00', left)
            if right < 0:
                right = width
            if width*.20 <= right-left <= width*.70:
                runs.add((left, right))
            left = right+1
        for run in list(active):
            if run not in runs:
                top = active.pop(run)
                if 3 <= y-top <= height*.12:
                    bands.append((*run, top, y))
        for run in runs:
            active.setdefault(run, y)
    for (left, right), top in active.items():
        if 3 <= height-top <= height*.12:
            bands.append((left, right, top, height))
    ratio = image.width / width
    return [(left*ratio, right*ratio, top*ratio, bottom*ratio)
            for left, right, top, bottom in bands]


class WorkshopLocator:
    def __init__(self):
        self.context = None
        self.transform = None
        self.verified = False
        self.last_search = -1e10

    @staticmethod
    def _apply(image, transform):
        scale, dx, dy = transform
        return image.transform(image.size, Image.Transform.AFFINE,
            (scale*1648/image.width, 0, dx, 0, scale*928/image.height, dy),
            Image.Resampling.BILINEAR)

    def normalize(self, image, context=None):
        identity = (context, image.size)
        if identity != self.context:
            self.context = identity
            self.transform = None
            self.last_search = -1e10
        self.verified = False
        if self.transform is not None:
            candidate = self._apply(image, self.transform)
            if workshop_visual_fallback(candidate):
                self.verified = True
                return candidate
            self.transform = None
        default_ok=workshop_visual_fallback(image)
        now = monotonic()
        if now-self.last_search < 1.0:
            self.verified=default_ok
            return image
        self.last_search = now
        matches = []
        for left, right, top, bottom in header_bands(image):
            scale = (right-left) / (1006-274)
            # A quest panel can touch the workshop's left edge. Closing the
            # purple mask then merges both headers. Recover width from the
            # uninterrupted RIGHT panel edge instead of including that neighbor.
            rgb = image.convert('RGB')
            edge_x = max(0, min(image.width-1, round(right-10)))
            # Header letters split a colour band into shorter strips. Recover
            # its actual top along the uninterrupted right panel edge. Body
            # rows then extend back to that same top and fail header geometry.
            panel_top = round(top)
            while panel_top > 0:
                r,g,b = rgb.getpixel((edge_x,panel_top-1))
                if not (12<=r<=150 and 12<=g<=150 and b>=r+8 and b>=g+8):
                    break
                panel_top -= 1
            # Preserve the existing subpixel alignment of intact headers.
            # A few pixels lost to antialiasing are already tolerated; only
            # a materially truncated strip needs the recovered panel top.
            if top-panel_top > 12*scale:
                top = panel_top
            edge_end = round(top)
            misses = 0
            for y in range(max(0,round(top)), image.height):
                r,g,b = rgb.getpixel((edge_x,y))
                purple = 12<=r<=150 and 12<=g<=150 and b>=r+8 and b>=g+8
                misses = 0 if purple else misses+1
                if misses>10:
                    break
                if purple:
                    edge_end=y+1
            edge_scale = (edge_end-top)/(763-137)
            if .45<=edge_scale<=2.5:
                scale = edge_scale
                inferred_left = right-scale*(1006-274)
                if inferred_left < left-12:
                    continue  # Tall, narrow inventory panel, not the workshop.
                left = inferred_left
            if not .45 <= scale <= 2.5:
                continue
            # A chat bar near the bottom can mimic a workshop header, but
            # its supposed full workshop would extend beyond the capture.
            # Reject it instead of creating a second ambiguous match that
            # prevents caching the real workshop's alignment.
            if top+(763-137)*scale > image.height+12*scale:
                continue
            # A body panel can share the header colour, but not its strip geometry.
            if not .55*37*scale <= bottom-top <= 1.6*37*scale:
                continue
            transform = (scale, left-scale*274, top-scale*137)
            title = rgb.crop((round(left+(right-left)*.28), round(top),
                              round(left+(right-left)*.72), round(top+37*scale)))
            if sum(min(p)>205 for p in title.getdata()) < max(8, round(15*scale*scale)):
                continue
            candidate = self._apply(image, transform)
            if workshop_visual_fallback(candidate):
                matches.append((transform, candidate))
        # Never choose between two distinct workshops or incompatible layouts.
        if len(matches) == 1:
            self.transform, candidate = matches[0]
            self.verified = True
            return candidate
        if not matches and default_ok:self.verified=True
        return image
