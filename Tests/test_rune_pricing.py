import pytest
from forgely_pricing import PriceBook,load_price_book,estimate_line_cost
from forgely_decision import advise,candidates


def test_user_prices_are_unit_prices_not_divided_by_rune_level():
    book=load_price_book()
    assert len(book.prices)==105
    assert book.unit_price('Fo')==36
    assert book.unit_price('Ra Vi')==2368
    assert book.server=='Tylezia'
    assert book.unit_price('Age')==74
    assert book.unit_price('Rune inconnue') is None


def test_estimate_is_explicitly_approximate_and_unknown_is_not_free():
    book=PriceBook({'Fo':36},server='Tylezia',observed_on='2026-11-08')
    row=estimate_line_cost('Fo',current=30,target=40,gain=1,success=.5,book=book)
    assert row['unit_price_kamas']==36
    assert row['minimum_runes']==10
    assert row['estimated_cost_kamas']==720
    assert row['includes_collateral_losses'] is False
    assert estimate_line_cost('Pa Fo',current=30,target=40,gain=3,success=.5,book=book)['estimated_cost_kamas'] is None


def test_price_parser_fails_closed_on_conflicts_and_nonfinite_numbers(tmp_path):
    for value in ('NaN','-2','inf'):
        path=tmp_path/'prices.csv'
        path.write_text('rune;prix_unitaire_kamas;serveur;date_releve;source\nFo;'+value+';Tylezia;2026-11-08;user\n',encoding='utf-8')
        with pytest.raises(ValueError):load_price_book(path)


def test_copilot_ignores_legacy_price_cost():
    book=PriceBook({'Fo':36,'Pa Fo':132,'Ra Fo':382},server='Tylezia',observed_on='2026-11-08')
    def model(rune):
        return dict(kind='local_dofocus_model',blocked=False,regime='normal',estimated=False,
                    display={'SC':'30','SN':'50','EC':'20'},probabilities={'SC':30,'SN':50,'EC':20})
    args=({'Force':30},{'Force':40},{'Force':40},0)
    proposal=advise(*args,simulation_for=model,price_book=book)
    assert 'pricing' not in proposal.estimates
    assert 'kamas' not in proposal.explanation



def test_prices_never_remove_the_only_legal_rune():
    book=PriceBook({'Fo':10**9},server='Tylezia',observed_on='2026-11-08')
    rows=candidates({'Force':39},{'Force':40},{'Force':40},0,price_book=book)
    assert rows and rows[0][1]=='Fo'



def test_prices_do_not_change_equal_priority_choices_including_matrix():
    args=({'Force':39,'Intelligence':39},{'Force':40,'Intelligence':40},
          {'Force':40,'Intelligence':40},0)
    baseline=advise(*args,predictive_policy=True)
    book=PriceBook({'Fo':1000,'Ine':1},server='Tylezia',observed_on='2026-11-08')
    priced=advise(*args,predictive_policy=True,price_book=book)
    assert baseline.rune=='Fo'
    assert priced.rune==baseline.rune
    # Missing prices cannot win a tie by being mistaken for zero.
    unknown=PriceBook({'Ine':1},server='Tylezia',observed_on='2026-11-08')
    assert advise(*args,predictive_policy=True,price_book=unknown).rune==baseline.rune


def test_prices_are_absent_from_main_and_floating_reports():
    from forgely_predictive import report_text
    book=PriceBook({'Fo':36},server='Tylezia',observed_on='2026-11-08')
    p=advise({'Force':39},{'Force':40},{'Force':40},0,price_book=book,predictive_policy=True)
    for compact in (False,True):
        text=report_text(p,{'Force':39},{'Force':40},{'Force':40},0,compact=compact)
        assert 'kamas' not in text and 'Tylezia' not in text


def test_sequence_ties_ignore_prices_and_preserve_validated_winner():
    def model(rune,winner=None):
        return dict(kind='local_dofocus_model',blocked=False,probabilities={'SC':30,'SN':50,'EC':20},
            sequence=dict(kind='sequence_rollouts',source='simulation',real_observations=0,
                          trials=16,completed=8,horizon=8,value=.5,mean_steps=4,
                          **({'validation':dict(accepted=True,selected=winner)} if winner else {})))
    args=({'Force':39,'Intelligence':39},{'Force':40,'Intelligence':40},
          {'Force':40,'Intelligence':40},0)
    book=PriceBook({'Fo':1000,'Ine':1},server='Tylezia',observed_on='2026-11-08')
    assert candidates(*args,simulation_for=model,price_book=book)[0][1]=='Fo'
    assert candidates(*args,simulation_for=lambda r:model(r,'Fo'),price_book=book)[0][1]=='Fo'
