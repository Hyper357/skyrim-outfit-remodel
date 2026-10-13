"""Compare intended sRGB PNG bytes with decoded DDS mip 0. Requires Pillow."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from PIL import Image, ImageChops, ImageStat


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_png', type=Path)
    p.add_argument('dds', type=Path)
    p.add_argument('--rgb-mae-max', type=float, default=3.0)
    p.add_argument('--alpha-mae-max', type=float, default=.1)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    if a.report.exists():
        p.error('Report already exists; use a new output path')
    if a.rgb_mae_max < 0 or a.alpha_mae_max < 0:
        p.error('MAE thresholds must be nonnegative')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    r = dict(source_png=str(a.source_png), dds=str(a.dds), passed=False,
             acceptance='Encoded sRGB byte comparison at mip 0; not artistic approval, mip-chain or game acceptance')
    try:
        if a.source_png.suffix.lower() != '.png' or a.dds.suffix.lower() != '.dds':
            raise ValueError('Expected intended sRGB PNG and encoded DDS')
        b = a.dds.read_bytes()
        if b[:4] != b'DDS ' or b[84:88] != b'DX10' or struct.unpack_from('<I', b, 128)[0] != 99:
            raise ValueError('This helper expects BC7_UNORM_SRGB DX10 DDS')
        source = Image.open(a.source_png).convert('RGBA')
        target = Image.open(a.dds).convert('RGBA')
        if source.size != target.size:
            raise ValueError('Image dimensions differ')
        diff = ImageChops.difference(source, target)
        means = ImageStat.Stat(diff).mean
        r.update(source_sha256=sha(a.source_png), dds_sha256=sha(a.dds),
                 size=list(source.size), rgba_mae=means,
                 rgba_max=[v[1] for v in diff.getextrema()],
                 rgb_mae_max=a.rgb_mae_max, alpha_mae_max=a.alpha_mae_max)
        r['passed'] = sum(means[:3])/3 <= a.rgb_mae_max and means[3] <= a.alpha_mae_max
        if not r['passed']:
            r['error'] = 'Decoded colour/alpha exceeds requested byte-error tolerance'
    except (OSError, ValueError, struct.error) as e:
        r['error'] = str(e)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
