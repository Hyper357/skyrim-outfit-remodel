"""Read-only checks for the portable mesh snapshot described in tools.md."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def finite_vector(v, size):
    return isinstance(v, (list, tuple)) and len(v) == size and all(isinstance(x, (int, float)) and math.isfinite(x) for x in v)


def area3(a, b, c):
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    return math.sqrt(sum(x*x for x in (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]))) / 2


def audit_mesh(mesh, max_influences=4, tolerance=0.005, epsilon=1e-7):
    errors, warnings = [], []
    vertices, faces = mesh.get('vertices', []), mesh.get('faces', [])
    nv = len(vertices)
    if not nv or not faces:
        errors.append('empty_geometry')
    coordinates_ok = all(finite_vector(v, 3) for v in vertices)
    if not coordinates_ok:
        errors.append('nonfinite_or_invalid_coordinates')
    valid_faces = []
    bad_faces = 0
    for face in faces:
        if len(face) < 3 or len(set(face)) != len(face) or any(type(i) is not int or not 0 <= i < nv for i in face):
            bad_faces += 1
        else:
            valid_faces.append(face)
    if bad_faces:
        errors.append(f'invalid_faces:{bad_faces}')
    edges, used = Counter(), set()
    degenerate = 0
    for face in valid_faces:
        used.update(face)
        for a, b in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((a, b)))] += 1
        if coordinates_ok and sum(area3(vertices[face[0]], vertices[face[i]], vertices[face[i+1]]) for i in range(1, len(face)-1)) <= 1e-12:
            degenerate += 1
    duplicate_faces = len(valid_faces) - len({tuple(sorted(f)) for f in valid_faces})
    if degenerate:
        errors.append(f'degenerate_faces:{degenerate}')
    if duplicate_faces:
        errors.append(f'duplicate_faces:{duplicate_faces}')
    loose = nv-len(used)
    if loose:
        warnings.append(f'loose_vertices:{loose}')
    nonmanifold = sum(n > 2 for n in edges.values())
    if nonmanifold:
        warnings.append(f'edges_with_more_than_two_faces:{nonmanifold}')
    uv = mesh.get('uv_faces')
    uv_degenerate = 0
    if uv is None or len(uv) != len(faces):
        errors.append('missing_or_mismatched_uv_faces')
    else:
        for face, corners in zip(faces, uv):
            if len(corners) != len(face) or not all(finite_vector(c, 2) for c in corners):
                errors.append('invalid_uv_corners')
                break
            # Absolute fan areas: a screening metric, not a UV overlap/stretch test.
            a = corners[0]
            area = sum(abs((corners[i][0]-a[0])*(corners[i+1][1]-a[1])-(corners[i][1]-a[1])*(corners[i+1][0]-a[0]))/2 for i in range(1, len(corners)-1))
            uv_degenerate += area <= 1e-14
        if uv_degenerate:
            warnings.append(f'degenerate_uv_faces:{uv_degenerate}')
    weights = mesh.get('weights', [])
    influences, sums, unweighted, invalid = [], [], 0, 0
    unknown = set()
    if mesh.get('skinned'):
        if len(weights) != nv:
            errors.append('weight_vertex_count_mismatch')
        else:
            bones = set(mesh.get('bones', []))
            for row in weights:
                if not isinstance(row, dict) or any(not isinstance(w, (int, float)) or not math.isfinite(w) or w < 0 for w in row.values()):
                    invalid += 1
                    continue
                active = {b:w for b,w in row.items() if w > epsilon}
                unknown.update(set(active)-bones)
                total = sum(active.values())
                if not math.isfinite(total):
                    invalid += 1
                    continue
                unweighted += not active
                sums.append(total)
                influences.append(len(active))
            if invalid:
                errors.append(f'invalid_weights:{invalid}')
            if unweighted:
                errors.append(f'unweighted_vertices:{unweighted}')
            if influences and max(influences) > max_influences:
                errors.append('too_many_bone_influences')
            if any(abs(s-1) > tolerance for s in sums):
                errors.append('weights_not_normalized')
            if unknown:
                errors.append('unknown_bones:' + ','.join(sorted(unknown)))
    normals = mesh.get('normals')
    if normals is not None and (len(normals) != nv or not all(finite_vector(n, 3) for n in normals)):
        errors.append('invalid_normals')
    return {'name':mesh.get('name'), 'vertices':nv, 'faces':len(faces),
            'triangles_equivalent':sum(len(f)-2 for f in valid_faces),
            'quads':sum(len(f)==4 for f in valid_faces), 'boundary_edges':sum(n==1 for n in edges.values()),
            'loose_vertices':loose, 'max_influences':max(influences, default=0),
            'weight_sum_range':[min(sums),max(sums)] if sums else None,
            'hashes':{k:digest(mesh.get(k)) for k in ('vertices','faces','uv_faces','weights','bones','matrix_world')},
            'errors':errors,'warnings':warnings}


def audit(snapshot):
    meshes = snapshot.get('meshes', [])
    rows = [audit_mesh(m) for m in meshes]
    names = [m.get('name') for m in meshes]
    errors = []
    if not meshes:
        errors.append('no_meshes')
    if len(names) != len(set(names)):
        errors.append('duplicate_mesh_names')
    return {'schema':1,'pass':bool(rows) and not errors and all(not r['errors'] for r in rows),
            'errors':errors,'meshes':rows,'scope':'numeric_snapshot_checks_only',
            'uv_overlap_test':'not_run','pose_test':'not_run','game_test':'not_run'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('snapshot'); p.add_argument('--out', required=True)
    args=p.parse_args(); result=audit(read(args.snapshot)); write(args.out,result)
    print(json.dumps({'pass':result['pass'],'meshes':len(result['meshes'])}))
    return 0 if result['pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
