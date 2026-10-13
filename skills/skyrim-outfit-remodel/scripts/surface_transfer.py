"""Apply an explicit surface map to positions, named skin weights and dense morphs.

Standard library, JSON in/out, new outputs only. Does not discover correspondences,
edit NIF/OSD, deploy, or prove animation behavior. See fitted-clothing.md.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def vector(value):
    if len(value) != 3 or any(not isinstance(v, (int, float)) or isinstance(v, bool)
                              or not math.isfinite(v) for v in value):
        raise ValueError('Expected a finite three-vector')
    return list(value)


def mapping_row(row, count):
    ids, weights = row['indices'], row['weights']
    if not ids or len(ids) != len(weights):
        raise ValueError('Empty or inconsistent correspondence')
    if any(type(i) is not int or not 0 <= i < count for i in ids):
        raise ValueError('Donor index out of range')
    if any(not isinstance(w, (int, float)) or isinstance(w, bool)
           or not math.isfinite(w) or w < 0 for w in weights):
        raise ValueError('Invalid barycentric weight')
    if abs(sum(weights) - 1) > 1e-6:
        raise ValueError('Barycentric weights must sum to one')
    return ids, weights


def interpolate(values, row):
    ids, weights = mapping_row(row, len(values))
    selected = [vector(values[i]) for i in ids]
    return vector([sum(v[k] * w for v, w in zip(selected, weights)) for k in range(3)])


def skin(values, row):
    ids, weights = mapping_row(row, len(values))
    result = {}
    for i, factor in zip(ids, weights):
        donor = values[i]
        if not donor or any(not isinstance(name, str) or not name or
                            not isinstance(w, (float, int)) or isinstance(w, bool)
                            or not math.isfinite(w) or w < 0 for name, w in donor.items()):
            raise ValueError('Invalid named donor skin weights')
        if abs(sum(donor.values()) - 1) > .002:
            raise ValueError('Donor skin weights are not normalized')
        for name, weight in donor.items():
            result[name] = result.get(name, 0) + factor * weight
    strongest = sorted(((n, w) for n, w in result.items() if w > 0),
                       key=lambda item: (-item[1], item[0]))[:4]
    total = sum(w for _, w in strongest)
    if total <= 0:
        raise ValueError('Unweighted output vertex')
    return {n: w / total for n, w in strongest}


def synchronize_delta(lower, lower_boundary, upper_boundary, falloff):
    """Correct a nearby lower delta using the paired boundary's discrepancy."""
    if not math.isfinite(falloff) or not 0 <= falloff <= 1:
        raise ValueError('Falloff must lie in [0,1]')
    lower, a, b = map(vector, (lower, lower_boundary, upper_boundary))
    return vector([x + falloff * (z - y) for x, y, z in zip(lower, a, b)])


def transfer(data):
    vertices, correspondence = data['donor_vertices'], data['map']
    if not vertices or not correspondence:
        raise ValueError('Empty donor or correspondence')
    for v in vertices:
        vector(v)
    out = {'schema': 1, 'vertices': [], 'morphs': {}, 'nif_written': False,
           'pose_test': 'not_run', 'game_test': 'not_run'}
    for row in correspondence:
        p, offset = interpolate(vertices, row), vector(row.get('offset', [0, 0, 0]))
        out['vertices'].append(vector([a+b for a, b in zip(p, offset)]))
    if 'donor_weights' in data:
        if len(data['donor_weights']) != len(vertices):
            raise ValueError('Donor skin count differs')
        out['weights'] = [skin(data['donor_weights'], row) for row in correspondence]
    for name, deltas in data.get('donor_morphs', {}).items():
        if len(deltas) != len(vertices):
            raise ValueError('Morph length differs from donor vertices')
        for delta in deltas:
            vector(delta)
        out['morphs'][name] = [interpolate(deltas, row) for row in correspondence]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', type=Path)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    if args.out.exists() or args.out.resolve() == args.source.resolve():
        raise ValueError('Refusing to overwrite any input or existing output')
    raw = args.source.read_bytes()
    out = transfer(json.loads(raw.decode('utf-8-sig')))
    out['input_sha256'] = hashlib.sha256(raw).hexdigest()
    encoded = json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as f:
        f.write(encoded)
    print(json.dumps({'vertices': len(out['vertices']), 'morphs': len(out['morphs'])}))


if __name__ == '__main__':
    main()
