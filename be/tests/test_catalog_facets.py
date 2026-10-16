from be.catalog import load_catalog


def test_paper_labels_cover_catalog_without_noise():
    entries=load_catalog()
    assert set(entries)==set(range(26))
    assert entries[13]['facets']=={'groups':['internal'],'sizes':['small'],'risks':['valuable']}
    assert entries[22]['facets']=={'groups':['computing'],'sizes':['medium'],'risks':['high']}
    assert entries[17]['facets']['sizes']==['unidentified']
    for entry in entries.values():
        assert entry['facets']['groups']
        assert entry['facets']['sizes']
        assert entry['facets']['risks']==[entry['info']['risk_level']]


def test_multiple_labels_can_be_overridden_in_metadata(monkeypatch,tmp_path):
    import json
    from be import catalog
    from be.config import DATA
    (tmp_path/'catalog_facets.json').write_text((DATA/'catalog_facets.json').read_text())
    (tmp_path/'meta.json').write_text(json.dumps({'13':{'facets':{'groups':['internal','computing'],'sizes':['small','medium'],'risks':['valuable','medium']}}}))
    monkeypatch.setattr(catalog,'DATA',tmp_path)
    assert catalog.load_catalog()[13]['facets']=={'groups':['internal','computing'],'sizes':['small','medium'],'risks':['valuable','medium']}
