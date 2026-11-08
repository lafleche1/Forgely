"""Unit rune-price observations. Currency estimates never alter model probabilities."""
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache
from math import ceil,isfinite
import csv
import unicodedata

DEFAULT_PATH=Path(__file__).parent/'assets'/'prices'/'tylezia-20261108.csv'


def _key(name):
    name=' '.join(unicodedata.normalize('NFC',str(name)).split())
    if name.casefold().startswith('rune '):name=name[5:]
    return name.casefold()


@dataclass(frozen=True)
class PriceBook:
    prices: dict
    server: str
    observed_on: str
    source: str='captures_utilisateur_transcrites'

    def __post_init__(self):
        clean={}
        for name,value in self.prices.items():
            if (not _key(name) or type(value) not in (int,float)
                    or not isfinite(value) or not 0<value<=10**12):
                raise ValueError('Prix unitaire invalide')
            if _key(name) in clean and clean[_key(name)]!=value:
                raise ValueError('Prix contradictoires')
            clean[_key(name)]=value
        object.__setattr__(self,'prices',clean)

    def unit_price(self,rune):
        return self.prices.get(_key(rune))


@lru_cache(maxsize=8)
def _read_book(path,mtime,size):
    prices={};metadata=None
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream,delimiter=';'):
            try:
                name=row['rune'];price=float(row['prix_unitaire_kamas'])
                current=(row['serveur'],row['date_releve'],row['source'])
            except (KeyError,ValueError,TypeError) as exc:
                raise ValueError('Catalogue de prix invalide') from exc
            if metadata is not None and metadata!=current:
                raise ValueError('Métadonnées de prix incohérentes')
            metadata=current
            if _key(name) in prices and prices[_key(name)]!=price:
                raise ValueError('Prix contradictoires')
            prices[_key(name)]=price
    if not metadata or not prices:raise ValueError('Catalogue vide')
    return PriceBook(prices,server=metadata[0],observed_on=metadata[1],source=metadata[2])


def load_price_book(path=DEFAULT_PATH):
    path=Path(path).resolve();stat=path.stat()
    return _read_book(str(path),stat.st_mtime_ns,stat.st_size)


def book_from_settings(settings):
    prices=settings.get('prices')
    if not isinstance(prices,dict) or (not prices and not settings.get('price_reference')):return None
    known={k:v for k,v in prices.items() if type(v) in (int,float) and isfinite(v) and v>0}
    try:return PriceBook(known,server=settings.get('price_server','Manuel'),
        observed_on=settings.get('price_reference_date','non renseignée'),
        source=settings.get('price_source','saisie_utilisateur'))
    except ValueError:return None


def active_price_book():
    from forgely_tools import read_settings
    preferred=book_from_settings(read_settings())
    if preferred is not None:return preferred
    try:return load_price_book()
    except (OSError,ValueError):return None


def estimate_line_cost(rune,*,current,target,gain,success,book):
    price=book.unit_price(rune)
    count=ceil(max(0,target-current)/gain)
    probability=(success if type(success) in (int,float) and isfinite(success) and 0<success<=1 else None)
    return dict(server=book.server,observed_on=book.observed_on,source=book.source,
        unit_price_kamas=price,minimum_runes=count,
        nominal_cost_kamas=price*count if price is not None else None,
        estimated_cost_kamas=price*count/probability if price is not None and probability else None,
        success_model=probability,includes_collateral_losses=False,constant_current_odds=True,
        is_game_probability=False)


def price_ties(rows,book,priority=None):
    """Price only breaks equal-priority ties; unknown prices preserve the ranking."""
    if book is None:return rows
    from itertools import groupby
    result=[]
    for _,group in groupby(rows,key=priority or (lambda row:round(row[0],12))):
        group=list(group)
        if all(book.unit_price(row[1]) is not None for row in group):
            group.sort(key=lambda row:(ceil(max(0,row[9]-row[8])/row[4].gain)*book.unit_price(row[1]),row[1]))
        result.extend(group)
    return result



def economic_scores(rows,book,mode):
    """Indicative utility per unit price; never assumes unknown prices are free."""
    if mode!='Budget optimisé' or book is None or not rows:return rows
    if any(book.unit_price(row[1]) is None for row in rows):return rows
    return [((row[0]/(1+book.unit_price(row[1])) if row[0]>0 else row[0]),*row[1:]) for row in rows]
