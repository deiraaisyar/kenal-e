"""Human-provided demo taxonomy. All handling text remains a draft."""
import json
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
        entry['info'].update(override.get('info', {}))
        entry['risk_level'] = entry['info']['risk_level']
        entry['bag'] = entry['info']['bag']
        entry['facets'] = {**facets[str(mid)], 'risks':[entry['risk_level']], **override.get('facets', {})}
        entry['price'] = valid_price(override.get('price', {}), entry['info'])
        entries[mid] = entry
    return entries

def valid_price(price, info):
    if not info.get('assessable') or not price.get('verified') or not price.get('show'):
        return {'mode':'none'}
    if price.get('mode') == 'no_value': return {'mode':'no_value','verified':True}
    lo, hi = price.get('min'), price.get('max')
    if price.get('mode') not in ('per_item','per_kg') or not price.get('source') or not price.get('source_date'):
        return {'mode':'none'}
    if not isinstance(lo,(int,float)) or not isinstance(hi,(int,float)) or not 0 <= lo <= hi:
        return {'mode':'none'}
    return {**price,'currency':'IDR','weight_input':price['mode']=='per_kg'}
