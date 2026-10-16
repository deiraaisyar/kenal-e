"""Align names using original cache filenames, never assume CSV export row order."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from be.config import ARTIFACTS, DATA

def prepare(filenames):
    names=np.load(filenames,allow_pickle=False)
    with (ARTIFACTS/'facets_level2.csv').open() as f:
        rows={row['filename']:row for row in csv.DictReader(f)}
    with np.load(ARTIFACTS/'reference.npz',allow_pickle=False) as data:
        assert len(names)==len(data['macro'])==len(rows)
        assert set(names.tolist())==set(rows)
        result=[]
        for index,name in enumerate(names):
            row=rows[str(name)]
            for column,key in [('level1_macro_id','macro'),('level2_sub_id','sub'),('dup_group_id','dup_group')]:
                assert int(row[column])==int(data[key][index]),f'Alignment mismatch at {index}: {key}'
            result.append({'filename':str(name),'macro':int(row['level1_macro_id']),'sub':int(row['level2_sub_id']),'dup_group':int(row['dup_group_id'])})
    (DATA/'gallery_meta.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Aligned gallery metadata:',len(result),'rows')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--filenames',required=True,type=Path)
    prepare(p.parse_args().filenames)
