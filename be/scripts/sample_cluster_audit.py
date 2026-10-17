"""Reproduce the random file selection and contact sheets for visual metadata review."""
import argparse
import hashlib
import json
import random
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont


def sample_files(rows, macro_id, sub_id, seed=20261018):
    pool={}
    for i,row in enumerate(rows):
        if (row['macro'],row['sub'])==(macro_id,sub_id):
            pool.setdefault(row['dup_group'],[]).append((i,row))
    rng=random.Random(f'{seed}:{macro_id}_{sub_id}')
    chosen=[rng.choice(pool[d]) for d in rng.sample(sorted(pool),min(5,len(pool)))]
    selected={i for i,_ in chosen}
    remaining=[pair for group in pool.values() for pair in group if pair[0] not in selected]
    chosen+=rng.sample(remaining,min(5-len(chosen),len(remaining)))
    return chosen


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--images-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=20261018)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    rows=json.loads((root/'be/data/gallery_meta.json').read_text())
    meta=json.loads((root/'be/data/meta.json').read_text())
    groups=sorted({(r['macro'],r['sub']) for r in rows})
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    samples={}
    for mid,sid in groups:
        files=sample_files(rows,mid,sid,args.seed)
        members=[r for r in rows if (r['macro'],r['sub'])==(mid,sid)]
        samples[f'{mid}_{sid}']={'macro_id':mid,'sub_id':sid,'total_rows':len(members),
            'unique_groups':len({r['dup_group'] for r in members}),
            'files':[{'index':i,**r,'sha256':hashlib.sha256((args.images_dir/r['filename']).read_bytes()).hexdigest()} for i,r in files]}
    font=ImageFont.load_default(size=16)
    items=list(samples.items())
    for start in range(0,len(items),4):
        selected=items[start:start+4]
        sheet=Image.new('RGB',(1200,280*len(selected)),'#e9ece7');draw=ImageDraw.Draw(sheet)
        for y,(gid,sample) in enumerate(selected):
            draw.text((10,y*280+3),f"MICRO {gid} | {sample['unique_groups']} unique / {sample['total_rows']} files",font=font,fill='black')
            for x,f in enumerate(sample['files']):
                with Image.open(args.images_dir/f['filename']) as im:
                    thumb=ImageOps.contain(ImageOps.exif_transpose(im).convert('RGB'),(230,225))
                sheet.paste(thumb,(x*240+(240-thumb.width)//2,y*280+28+(225-thumb.height)//2))
                draw.text((x*240+8,y*280+255),f"{gid} / #{x+1} / row {f['index']}",font=font,fill='black')
            sample['contact_sheet']=f'contact-{start//4:02d}.jpg'
        sheet.save(out/f'contact-{start//4:02d}.jpg',quality=91)
    (out/'samples.json').write_text(json.dumps({'seed':args.seed,'samples':samples},ensure_ascii=False,indent=2)+'\n')
    print(f"{len(samples)} micro groups; {sum(len(s['files']) for s in samples.values())} files")

if __name__=='__main__':main()
