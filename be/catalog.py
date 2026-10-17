"""Human-provided demo taxonomy. All handling text remains a draft."""
import json
import math
from copy import deepcopy
from .config import DATA, ARTIFACTS

RISK = ['low','low','low','unknown','high','high','high','high','medium','low','low','low','low','valuable','medium','medium','medium','unknown','unknown','low','low','high','high','low','low','medium']
BAGS = {'high':'red','medium':'orange','valuable':'green','low':'gray','unknown':'white'}
HAZARDS = {4:'Risiko kebocoran atau termal',6:'Timbal dan asam sulfat',7:'Litium: risiko kebakaran termal',13:'Logam berat dan logam berharga',14:'Kaca bertimbal (CRT)',15:'Potensi merkuri pada lampu latar CCFL',16:'Potensi merkuri pada lampu latar CCFL',18:'Campuran; perlu pemilahan lanjut',21:'Mengandung baterai litium',22:'Litium: risiko kebakaran termal',23:'Mengandung baterai litium'}
DEVICE = {0:'microwave',1:'washer',2:'printer',3:'switch',4:'battery',5:'phone',6:'car-battery',7:'phone-battery',8:'record',9:'keyboard',10:'laptop',11:'disc',12:'speaker',13:'pcb',14:'monitor',15:'monitor',16:'monitor',17:'desktop',18:'mixed',19:'printer',20:'mouse',21:'phone',22:'phone-battery',23:'laptop',24:'speaker',25:'monitor'}

def load_catalog():
    names = json.loads((ARTIFACTS / 'meta.json').read_text())
    manifest = json.loads((ARTIFACTS / 'manifest.json').read_text())
    overrides = json.loads((DATA / 'meta.json').read_text()) if (DATA / 'meta.json').exists() else {}
    facets = json.loads((DATA / 'catalog_facets.json').read_text())['categories']
    registry_path = DATA / 'research_sources.json'
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
    entries = {}
    for mid in range(26):
        risk = RISK[mid]
        assessable = mid != 18
        do = ['Simpan terpisah dari sampah rumah tangga.', 'Tanyakan penerimaan barang kepada pengelola sebelum menyetor.'] if assessable and risk != 'unknown' else []
        dont = ['Jangan bakar atau bongkar sendiri.'] if do else []
        if mid in (5,10,21,23): do.append('Jika masih dapat diakses, cadangkan lalu hapus data pribadi sebelum diserahkan.')
        if mid in (4,6,7,22): dont.append('Jangan ditekan, ditusuk, atau dibuka.')
        if mid in (14,15,16,25): dont.append('Jangan pecahkan layar atau tabung.')
        entry = {'id':mid, 'name':names[str(mid)]['nama'], 'size':manifest['reference_report'][str(mid)]['independent_groups'], 'risk_level':risk,'bag':BAGS[risk],'device':DEVICE[mid], 'thumb_url':None,
                 'info':{'weee':'Perangkat elektronik dan komponennya','risk_level':risk,'bag':BAGS[risk],'hazard_note':HAZARDS.get(mid,''),'do':do,'dont':dont,'assessable':assessable,'verified':False},
                 'price':{'mode':'none'},'subs':[]}
        if mid in (10,23): entry['info']['hazard_note'] += ' Klasifikasi risiko perangkat berbaterai perlu ditinjau kembali.'
        override = overrides.get(str(mid), {})
        entry['name'] = override.get('name', entry['name'])
        entry['description'] = override.get('description', '')
        entry['label_status'] = override.get('label_status', 'draft')
        entry['proposal_facets'] = override.get('proposal_facets', facets[str(mid)])
        entry['info'].update(override.get('info', {}))
        entry['info']['description'] = entry['description']
        entry['risk_level'] = entry['info']['risk_level']
        entry['bag'] = entry['info']['bag']
        entry['facets'] = {**facets[str(mid)], 'risks':[entry['risk_level']], **override.get('facets', {})}
        entry['price'] = valid_price(override.get('price', {}), entry['info'], registry)
        for sid, metadata in override.get('subs', {}).items():
            sub = deepcopy(metadata)
            sub['id'] = int(sid)
            if sub.get('price_policy') == 'override':
                sub['price'] = valid_price(sub.get('price', {}), {**entry['info'], **sub.get('info', {})}, registry)
            entry['subs'].append(sub)
        entries[mid] = entry
    return entries

def valid_price(price, info, registry=None):
    if price.get('mode') == 'ranges':
        if not info.get('assessable'):
            return {'mode':'none'}
        result = {'mode':'ranges', 'whole':None, 'scrap':None,
                  'unavailable_reason':price.get('unavailable_reason', ''),
                  'condition_factors':None, 'estimate_only':True}
        for channel in ('whole', 'scrap'):
            quote = validated_quote(price.get(channel), channel, registry or {})
            result[channel] = quote
        return result if result['whole'] or result['scrap'] else {'mode':'none'}
    if not info.get('assessable') or not price.get('verified') or not price.get('show'):
        return {'mode':'none'}
    if price.get('mode') == 'no_value': return {'mode':'no_value','verified':True}
    lo, hi = price.get('min'), price.get('max')
    if price.get('mode') not in ('per_item','per_kg') or not price.get('source') or not price.get('source_date'):
        return {'mode':'none'}
    if not isinstance(lo,(int,float)) or not isinstance(hi,(int,float)) or not 0 <= lo <= hi:
        return {'mode':'none'}
    return {**price,'currency':'IDR','weight_input':price['mode']=='per_kg'}


def validated_quote(quote, channel, registry):
    """Show only numeric estimates traceable to matching public observations."""
    if not isinstance(quote, dict) or quote.get('status') != 'web_researched':
        return None
    ids = quote.get('observation_ids', [])
    observations = {row['id']:row for row in registry.get('observations', [])}
    if not ids or any(key not in observations for key in ids):
        return None
    rows = [observations[key] for key in ids]
    allowed = {'marketplace_asking'} if channel == 'whole' else {'collector_buy','collector_grade_buy'}
    if any(row.get('kind') not in allowed or row.get('unit') != quote.get('unit') for row in rows):
        return None
    lo, hi = quote.get('min'), quote.get('max')
    if any(isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) for v in (lo,hi)):
        return None
    if not 0 <= lo <= hi or quote.get('unit') not in ('item','kg'):
        return None
    if lo != min(row['amount_idr'] for row in rows) or hi != max(row['amount_idr'] for row in rows):
        return None
    source_ids = set(quote.get('source_ids', []))
    if source_ids != {row['source_id'] for row in rows}:
        return None
    sources = registry.get('sources', {})
    if any(key not in sources or not sources[key].get('url','').startswith('https://') for key in source_ids):
        return None
    return {**quote,'sources':[{'title':sources[key]['title'],'url':sources[key]['url']} for key in sorted(source_ids)],
            'currency':'IDR','estimate_only':True,'local_quote_verified':False}


def resolve_metadata(entry, sub_id):
    """Micro identity can block a parent price; it never invents condition factors."""
    info, price = deepcopy(entry['info']), deepcopy(entry['price'])
    sub = next((row for row in entry['subs'] if row['id'] == sub_id), None)
    if sub:
        info.update(sub.get('info', {}))
        info['description'] = sub.get('description', entry.get('description',''))
        if sub.get('price_policy') == 'blocked':
            price = {'mode':'none'}
        elif sub.get('price_policy') == 'override':
            price = deepcopy(sub.get('price', {'mode':'none'}))
    if not info.get('assessable'):
        price = {'mode':'none'}
    return info, price
