from PIL import Image, ImageDraw
from forgely_jet import read_current_jet_ocr, parse_jet


def outlined_column():
    image = Image.new('RGB', (200, 580), '#38394e')
    ImageDraw.Draw(image).rectangle((3, 42, 195, 64), outline='#cccccc')
    return image


def test_selected_line_recovers_from_two_agreeing_enlarged_pixel_variants():
    image = outlined_column()
    calls = []
    def ocr(patch):
        calls.append(patch.size)
        if patch.width > image.width:
            return '180 Vitalité'
        return '40 Intelligence\n38 Sagesse\n1 PA' if patch.height == image.height else ''
    values = parse_jet(read_current_jet_ocr(image, ocr))
    assert values == {'Vitalité': 180, 'Intelligence': 40, 'Sagesse': 38, 'PA': 1}
    assert sum(w > image.width for w, h in calls) == 2


def test_enlarged_disagreement_never_confirms_a_value():
    image = outlined_column()
    zoom_calls = 0
    def ocr(patch):
        nonlocal zoom_calls
        if patch.width <= image.width:
            return ''
        zoom_calls += 1
        return f'{180 if zoom_calls == 1 else 130} Vitalité'
    assert parse_jet(read_current_jet_ocr(image, ocr)) == {}
