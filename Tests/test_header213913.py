from pathlib import Path
from PIL import Image
from forgely_workshop_layout import WorkshopLocator
from forgely_atelier import focus_workshop,read_atelier,choose_reliquat
from forgely_ocr_backend import extract_text
from forgely_jet import parse_jet


def test_video_header_is_not_mistaken_for_a_table_row():
    image=Image.open(Path(__file__).with_name('213913.png'))
    locator=WorkshopLocator()
    normalized=locator.normalize(image,'video')
    assert locator.transform is not None
    scale,dx,dy=locator.transform
    assert abs(137*scale+dy-161)<15
    result=read_atelier(focus_workshop(normalized),extract_text,history_ocr=lambda _: '',five_zones=True)
    jet=parse_jet(result.effects)
    assert jet['Vitalité']==280
    assert jet['Agilité']==39
    assert choose_reliquat(result.effects,result.reliquat)==4
