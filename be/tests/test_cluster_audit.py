import json
from collections import Counter
from pathlib import Path
from urllib.parse import quote
from be.catalog import load_catalog, resolve_metadata
from be.config import DATA
from be.inference import Gallery


def test_sampling_covers_every_micro_with_five_files_or_every_available_file():
    rows=json.loads((DATA/'gallery_meta.json').read_text())
    audit=json.loads((DATA/'cluster_audit_samples_2026-10-18.json').read_text())
    review=json.loads((DATA/'cluster_audit_2026-10-18.json').read_text())
    counts=Counter((r['macro'],r['sub']) for r in rows)
    assert len(audit['samples'])==len(counts)==88
    assert sum(len(s['files']) for s in audit['samples'].values())==423
    for gid,s in audit['samples'].items():
        assert len(s['files'])==min(5,counts[(s['macro_id'],s['sub_id'])])
        assert len({f['filename'] for f in s['files']})==len(s['files'])
        assert len({f['dup_group'] for f in s['files']})==min(5,s['unique_groups'])
        for f in s['files']:
            assert {k:rows[f['index']][k] for k in ('filename','macro','sub','dup_group')}=={k:f[k] for k in ('filename','macro','sub','dup_group')}
        assert [f['filename'] for f in s['files']]==[o['filename'] for o in review['micros'][gid]['sample_observations']]
        assert all(o['observation'] for o in review['micros'][gid]['sample_observations'])


def test_catalog_cards_and_full_photos_use_reviewed_samples_from_the_same_macro():
    manifest=json.loads((DATA/'catalog_representatives.json').read_text())['sources']
    audit=json.loads((DATA/'cluster_audit_2026-10-18.json').read_text())
    assets=DATA.parent.parent/'fe/src/assets/catalog'
    assert manifest==json.loads((assets/'sources.json').read_text())['sources']
    gallery=Gallery()
    assert set(manifest)=={str(i) for i in range(26)}
    for mid,filename in manifest.items():
        chosen=audit['thumbnails'][mid]
        assert filename==chosen['filename']
        assert filename in [o['filename'] for o in audit['micros'][chosen['micro_id']]['sample_observations']]
        assert gallery.catalog[int(mid)]['thumb_url'].endswith('/'+quote(filename,safe=''))
        assert (assets/f'{mid}.webp').is_file()


def test_micro_handling_and_quotes_are_resolved_in_catalog_and_inference():
    entries=load_catalog()
    for entry in entries.values():
        for sub in entry['subs']:
            info,price=resolve_metadata(entry,sub['id'])
            assert sub['info']==info
            assert sub['price']==price
            assert info['do'] and info['dont']
    assert 'kapasitor' in entries[0]['info']['hazard_note']
    assert 'timbal' in entries[6]['info']['hazard_note']
    assert 'menghapus data' not in ' '.join(entries[5]['subs'][1]['info']['do'])
    assert entries[15]['price']['whole'] is None
    assert entries[7]['price']['scrap']['min']==7000
    assert entries[7]['price']['scrap']['max']==63000
    assert entries[22]['price']['scrap']['min']==7000
    assert entries[22]['price']['scrap']['max']==10000
    for entry in entries.values():
        for price in [entry['price']]+[s['price'] for s in entry['subs']]:
            if price['mode']=='ranges':
                for channel in ('whole','scrap'):
                    if price[channel]:assert price[channel]['scope']


def test_audit_script_sampling_is_reproducible():
    from be.scripts.sample_cluster_audit import sample_files
    rows=json.loads((DATA/'gallery_meta.json').read_text())
    audit=json.loads((DATA/'cluster_audit_samples_2026-10-18.json').read_text())
    for gid,sub in audit['samples'].items():
        sampled=sample_files(rows,sub['macro_id'],sub['sub_id'],audit['seed'])
        assert [index for index,_ in sampled]==[f['index'] for f in sub['files']]
