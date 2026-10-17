import csv
import json
from copy import deepcopy
import pytest
from be.catalog import load_catalog, resolve_metadata, valid_price
from be.config import DATA


def registry():
    return json.loads((DATA/'research_sources.json').read_text())


def metadata():
    return json.loads((DATA/'meta.json').read_text())


def test_all_micro_groups_match_original_csv_without_renumbering():
    original={}
    path=DATA.parent.parent/'ai/artifacts/facets_level2.csv'
    # Runtime deployments need only bundled artifacts; this is repository validation.
    with path.open() as f:
        for row in csv.DictReader(f):
            original[row['level2_global_id']]=int(row['level2_size'])
    authored={s['global_id']:s['reference_rows'] for m in metadata().values() for s in m['subs'].values()}
    assert len(authored)==88
    assert authored==original
    assert all(s['condition_tier'] is None for m in metadata().values() for s in m['subs'].values())


def test_source_links_and_macro_facets_are_traceable():
    authored, sources=metadata(), registry()['sources']
    paper=json.loads((DATA/'catalog_facets.json').read_text())['categories']
    for mid,entry in authored.items():
        assert entry['description'] and entry['name']
        assert entry['info']['verified'] is False
        assert set(entry['info']['source_ids'])<=set(sources)
        assert entry['facets']==entry['proposal_facets']
        if mid!='26':
            assert entry['proposal_facets']['groups']==paper[mid]['groups']
            assert entry['proposal_facets']['sizes']==paper[mid]['sizes']
        for sub in entry['subs'].values():
            assert sub['name'] and sub['description'] and sub['facets']
            assert set(sub['source_ids'])<=set(sources)


def test_published_fixed_prices_are_not_expanded_into_made_up_ranges():
    price=load_catalog()[20]['price']
    assert price['mode']=='ranges'
    assert price['scrap']['min']==price['scrap']['max']==500
    assert price['scrap']['unit']=='kg'
    assert price['whole'] is None


@pytest.mark.parametrize('mutation', ['missing_observation','wrong_unit','wrong_amount','wrong_kind','nan','source_mismatch'])
def test_research_quotes_fail_closed(mutation):
    quote=deepcopy(metadata()['9']['price'])
    if mutation=='missing_observation':quote['scrap']['observation_ids']=['unknown']
    if mutation=='wrong_unit':quote['scrap']['unit']='item'
    if mutation=='wrong_amount':quote['scrap']['max']=999999
    if mutation=='wrong_kind':quote['scrap']['observation_ids']=['market_keyboard1']
    if mutation=='nan':quote['scrap']['min']=float('nan')
    if mutation=='source_mismatch':quote['scrap']['source_ids']=['bandung']
    result=valid_price(quote,{'assessable':True},registry())
    assert result['scrap'] is None
    assert result['whole'] is not None


def test_unknown_mixed_and_ambiguous_micro_do_not_get_parent_prices():
    entries=load_catalog()
    assert 26 not in entries
    assert entries[18]['price']=={'mode':'none'}
    for macro,sub in [(5,1),(21,1),(21,2),(23,2)]:
        info,price=resolve_metadata(entries[macro],sub)
        assert info['risk_level']=='unknown'
        assert info['assessable'] is False
        assert price=={'mode':'none'}
    assert resolve_metadata(entries[13],1)[1]=={'mode':'none'}
    assert resolve_metadata(entries[13],2)[1]=={'mode':'none'}


def test_micro_quote_does_not_mutate_parent_or_neighbor():
    entries=load_catalog()
    assert entries[5]['price']=={'mode':'none'}
    assert resolve_metadata(entries[5],0)[1]['scrap']['min']==4000
    assert resolve_metadata(entries[5],1)[1]=={'mode':'none'}
    assert entries[5]['info']['risk_level']=='high'
    assert entries[5]['price']=={'mode':'none'}


def test_two_price_channels_keep_different_units_and_dont_invent_condition():
    entry=load_catalog()[9]
    assert entry['price']['whole']['unit']=='item'
    assert entry['price']['scrap']['unit']=='kg'
    assert entry['price']['condition_factors'] is None
    assert valid_price(metadata()['9']['price'],{'assessable':False},registry())=={'mode':'none'}
