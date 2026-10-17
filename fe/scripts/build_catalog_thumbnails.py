"""Build fixed, visually reviewed thumbnails. Never choose the first file implicitly."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageOps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--images-dir', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root/'be/data/catalog_representatives.json').read_text())
    selected = manifest['sources']
    rows = {r['filename']:r for r in json.loads((root/'be/data/gallery_meta.json').read_text())}
    assert set(selected) == {str(i) for i in range(26)}
    out = root/'fe/src/assets/catalog'
    out.mkdir(parents=True, exist_ok=True)
    for mid, filename in selected.items():
        assert rows[filename]['macro'] == int(mid), (mid, filename)
        with Image.open(args.images_dir/filename) as image:
            oriented = ImageOps.exif_transpose(image).convert('RGB')
            # Preserve the full object; a center crop can remove identifying features.
            thumb = ImageOps.pad(oriented, (192,192), method=Image.Resampling.LANCZOS, color='#edf2e9')
            thumb.save(out/f'{mid}.webp', 'WEBP', quality=82, method=6)
    (out/'sources.json').write_text(json.dumps({
        'description':'Fixed representatives individually inspected in the seeded visual audit.',
        'source_manifest':'be/data/catalog_representatives.json',
        'reviewed_on':manifest['reviewed_on'], 'dimensions':[192,192], 'sources':selected,
    }, ensure_ascii=False, indent=2)+'\n')
    print(f'{len(selected)} thumbnails; {sum(p.stat().st_size for p in out.glob("*.webp")):,} bytes')

if __name__ == '__main__':
    main()
