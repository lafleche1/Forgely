"""Named equipment catalogue and target validation, independent of OCR and Tk."""
from dataclasses import dataclass, replace
from collections import Counter
import re
from pathlib import Path
import csv
from forgely_items import key_for
from forgely_plan import STATS

ROOT = Path(__file__).resolve().parent
CATEGORIES = ('Coiffe','Cape','Anneau','Amulette','Ceintures','Bottes','Arme')
TYPE_CATEGORIES = {16:'Coiffe',17:'Cape',9:'Anneau',1:'Amulette',10:'Ceintures',11:'Bottes',
                   **{i:'Arme' for i in (2,3,4,5,6,7,8,19,22)}}


def category_for_type(type_id):
    return TYPE_CATEGORIES.get(int(type_id))


@dataclass(frozen=True)
class Equipment:
    item_id: int
    name: str
    icon_id: int
    type_id: int
    level: int
    category: str
    ambiguous_name: bool = False

    @property
    def identity_name(self):
        return self.name+f' [objet {self.item_id}]' if self.ambiguous_name else self.name


class EquipmentCatalog:
    def __init__(self, path=ROOT/'catalogue_objets_noms_fr.csv'):
        items=[]
        with Path(path).open(encoding='utf-8-sig',newline='') as stream:
            for row in csv.DictReader(stream,delimiter=';'):
                category=category_for_type(row['type_id'])
                if category and row['nom_fr'].strip():
                    items.append(Equipment(int(row['item_id']),row['nom_fr'].strip(),
                        int(row['icon_id']),int(row['type_id']),int(row['niveau']),category))
        counts=Counter(key_for(x.name) for x in items)
        items=[replace(x,ambiguous_name=counts[key_for(x.name)]>1) for x in items]
        self.items=tuple(sorted(items,key=lambda x:(key_for(x.name),x.item_id)))
        self._by_id={x.item_id:x for x in self.items}
        self._keys={x.item_id:key_for(x.name) for x in self.items}

    def get(self,item_id):
        return self._by_id.get(int(item_id))

    def search(self,category,query=''):
        words=key_for(query).split()
        return [x for x in self.items if x.category==category and
                all(word in self._keys[x.item_id] for word in words)]

    def icon_path(self,item,directory=ROOT/'assets'/'equipment_icons'):
        path=Path(directory)/f'{item.icon_id}.png'
        return path if path.is_file() else None


def target_values(values):
    clean={}
    for stat,value in values.items():
        if stat not in STATS:
            raise ValueError('Caractéristique inconnue : '+stat)
        value=str(value).strip()
        if not value:continue
        try: target=int(value)
        except (ValueError,TypeError):
            raise ValueError('Indique un entier pour '+stat) from None
        if not -20000<=target<=20000:
            raise ValueError('Objectif hors limites pour '+stat)
        clean[stat]=(None,target)
    if not clean:raise ValueError('Renseigne au moins une caractéristique cible.')
    return clean

from functools import lru_cache

@lru_cache(maxsize=1)
def _bundled_profiles():
    by_id={};names={}
    path=ROOT/'assets'/'equipment_bounds.csv'
    try:
        with path.open(encoding='utf-8',newline='') as stream:
            for row in csv.DictReader(stream):
                ident=int(row['item_id'])
                by_id.setdefault(ident,{})[row['statistique']]=(int(row['min']),int(row['max']))
        catalogue=EquipmentCatalog()
        for item in catalogue.items:
            if not item.ambiguous_name:
                names[key_for(item.name)]=by_id.get(item.item_id,{})
            names[key_for(item.identity_name)]=by_id.get(item.item_id,{})
    except (OSError,ValueError,KeyError):return {},{}
    return by_id,names


def equipment_bounds(item):
    return dict(_bundled_profiles()[0].get(item.item_id,{}))


def bundled_bounds(name):
    return dict(_bundled_profiles()[1].get(key_for(name),{}))
