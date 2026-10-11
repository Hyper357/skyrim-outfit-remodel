"""Compare indexed snapshots. Allowed position changes need an explicit mesh-to-index map."""
import argparse
import math
from audit_mesh import read, write


def compare(before,after,allowed=None,tolerance=1e-6):
    allowed=allowed or {}
    errors=[]; rows=[]
    if not math.isfinite(tolerance) or tolerance<0:
        raise ValueError('Tolerance must be finite and nonnegative')
    if not before.get('meshes') or not after.get('meshes'):
        errors.append('no_meshes')
    if before.get('coordinate_space')!=after.get('coordinate_space'):
        errors.append('coordinate_space_changed')
    if len({m['name'] for m in before['meshes']}) != len(before['meshes']) or len({m['name'] for m in after['meshes']}) != len(after['meshes']):
        errors.append('duplicate_mesh_names')
    left={m['name']:m for m in before['meshes']}; right={m['name']:m for m in after['meshes']}
    if set(left)!=set(right):
        errors.append('mesh_set_changed')
    if set(allowed)-set(left):
        errors.append('allow_map_unknown_mesh')
    for name in sorted(set(left)&set(right)):
        a,b=left[name],right[name]; failed=[]
        for key in ('faces','uv_faces','weights','bones','matrix_world','skinned'):
            if a.get(key)!=b.get(key):
                failed.append(key+'_changed')
        allowed_ids=set(allowed.get(name,[]))
        if any(type(i) is not int or not 0<=i<len(a['vertices']) for i in allowed_ids):
            failed.append('invalid_allowed_index')
        if len(a['vertices'])!=len(b['vertices']):
            failed.append('vertex_count_changed'); maximum=None
        else:
            deltas=[math.dist(v,w) for v,w in zip(a['vertices'],b['vertices'])]
            if any(not math.isfinite(d) for d in deltas):
                failed.append('nonfinite_displacement')
            protected=[d for i,d in enumerate(deltas) if i not in allowed_ids]
            maximum=max(protected,default=0) if all(math.isfinite(d) for d in protected) else None
            if maximum is not None and maximum>tolerance:
                failed.append('protected_vertices_moved')
        rows.append({'name':name,'errors':failed,'max_protected_displacement':maximum})
    return {'pass':not errors and all(not r['errors'] for r in rows),'errors':errors,'meshes':rows,
            'scope':'index_identity_assumed; no shape keys, normals, materials or animation acceptance'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('before');p.add_argument('after');p.add_argument('--allow-indices')
    p.add_argument('--tolerance',type=float,default=1e-6);p.add_argument('--out',required=True)
    args=p.parse_args()
    if not math.isfinite(args.tolerance) or args.tolerance<0:
        p.error('Tolerance must be finite and nonnegative')
    result=compare(read(args.before),read(args.after),read(args.allow_indices) if args.allow_indices else {},args.tolerance)
    write(args.out,result);print(result['pass']);return 0 if result['pass'] else 2


if __name__=='__main__':
    raise SystemExit(main())
