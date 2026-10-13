"""Blender-only import/export bridge for indexed audit_nif JSON snapshots.

Import writes a NEW .blend; export writes NEW JSON. It never writes NIF or OSD.
Stable point IDs recover original order and reject changed topology or UVs.
Optional dense per-vertex morphs become shape keys. See indexed-roundtrip.md.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys


def recover(source, ids, vertices, faces, uv_faces, weights, allow_weights=False):
    count = len(source['vertices'])
    if (len(ids) != count or len(vertices) != count or
            any(type(i) is not int for i in ids) or set(ids) != set(range(count))):
        raise ValueError('Original point IDs must be a complete bijection')
    if any(len(v) != 3 or any(not math.isfinite(x) for x in v) for v in vertices):
        raise ValueError('Invalid positions')
    if any(any(type(i) is not int or not 0 <= i < count for i in f) for f in faces):
        raise ValueError('Invalid face indices')
    mapped_faces = [[ids[i] for i in face] for face in faces]
    if mapped_faces != source['faces']:
        raise ValueError('Topology, face order or winding changed')
    before_uv = source.get('uv_faces')
    if (before_uv is None) != (uv_faces is None):
        raise ValueError('UV layer presence changed')
    if before_uv is not None:
        if len(before_uv) != len(uv_faces):
            raise ValueError('UV face count changed')
        for a, b in zip(before_uv, uv_faces):
            if len(a) != len(b):
                raise ValueError('UV loop count changed')
            for x, y in zip(a, b):
                if len(x) != 2 or len(y) != 2 or any(not math.isfinite(v) for v in y):
                    raise ValueError('Invalid UV coordinates')
                if max(abs(u-v) for u, v in zip(x, y)) > 1e-6:
                    raise ValueError('UV coordinates changed')
    if len(weights) != count:
        raise ValueError('Skin weight count changed')
    ordered = [None] * count
    ordered_weights = [None] * count
    bones = set(source.get('bones', []))
    for i, original in enumerate(ids):
        ordered[original] = list(vertices[i])
        ordered_weights[original] = weights[i]
        w = weights[i]
        if any(n not in bones or not math.isfinite(v) or v < 0 for n, v in w.items()):
            raise ValueError('Unknown bone or invalid weight')
        if source.get('skinned') and (len(w) > 4 or abs(sum(w.values())-1) > .002):
            raise ValueError('Skin weights must be normalized with at most four influences')
        old = source.get('weights', [{} for _ in ids])[original]
        if not allow_weights and any(abs(w.get(n, 0)-old.get(n, 0)) > 1e-6 for n in set(w)|set(old)):
            raise ValueError('Skin weights changed without --allow-weight-edits')
    result = copy.deepcopy(source)
    result.update(vertices=ordered, weights=ordered_weights)
    if ordered != source['vertices']:
        result.pop('normals', None)
        result['normals_status'] = 'regenerate normals and tangent frame during checked NIF write'
    return result


def import_scene(bpy, snapshot, signature):
    for row in snapshot['meshes']:
        mesh = bpy.data.meshes.new(row['name'])
        mesh.from_pydata(row['vertices'], [], row['faces'])
        mesh.update()
        if [list(p.vertices) for p in mesh.polygons] != row['faces']:
            raise ValueError('Blender changed imported face layout')
        obj = bpy.data.objects.new(row['name'], mesh)
        bpy.context.collection.objects.link(obj)
        obj['_indexed_source'] = signature
        obj['_indexed_name'] = row['name']
        attr = mesh.attributes.new('_original_vertex_id', 'INT', 'POINT')
        for i, item in enumerate(attr.data):
            item.value = i
        if row.get('uv_faces') is not None:
            layer = mesh.uv_layers.new(name='SourceUV')
            for polygon, uv in zip(mesh.polygons, row['uv_faces']):
                for loop, value in zip(polygon.loop_indices, uv):
                    layer.data[loop].uv = value
        for bone in row.get('bones', []):
            obj.vertex_groups.new(name=bone)
        for i, weights in enumerate(row.get('weights', [])):
            for bone, value in weights.items():
                obj.vertex_groups[bone].add([i], value, 'REPLACE')
        if row.get('morphs'):
            obj.shape_key_add(name='Basis')
            for name, deltas in row['morphs'].items():
                if len(deltas) != len(mesh.vertices):
                    raise ValueError('Morph count differs from mesh')
                key = obj.shape_key_add(name=name)
                if key.name != name:
                    raise ValueError('Blender changed a morph name')
                for point, base, delta in zip(key.data, row['vertices'], deltas):
                    if len(delta) != 3 or any(not math.isfinite(v) for v in delta):
                        raise ValueError('Invalid morph delta')
                    point.co = [a+b for a, b in zip(base, delta)]


def export_scene(bpy, snapshot, signature, allow_weights):
    out = copy.deepcopy(snapshot)
    out['producer'] = 'indexed_blender_bridge'
    out['nif_written'] = False
    for k, row in enumerate(snapshot['meshes']):
        matches = [o for o in bpy.data.objects if o.get('_indexed_name') == row['name']]
        if len(matches) != 1:
            raise ValueError('Missing or duplicated source mesh object')
        obj = matches[0]
        if obj.get('_indexed_source') != signature:
            raise ValueError('Source snapshot fingerprint differs')
        if any(abs(obj.matrix_world[i][j]-(1 if i == j else 0)) > 1e-7
               for i in range(4) for j in range(4)):
            raise ValueError('Object transform changed; explicit coordinate conversion required')
        if any(m.show_viewport or m.show_render for m in obj.modifiers):
            raise ValueError('Disable modifiers; bridge exports original basis only')
        mesh = obj.data
        attr = mesh.attributes.get('_original_vertex_id')
        if attr is None or attr.domain != 'POINT' or attr.data_type != 'INT':
            raise ValueError('Original vertex ID attribute missing or changed')
        ids = [x.value for x in attr.data]
        basis = mesh.shape_keys.key_blocks[0].data if mesh.shape_keys else mesh.vertices
        vertices = [list(v.co) for v in basis]
        uv = mesh.uv_layers.get('SourceUV')
        uv_faces = [[list(uv.data[i].uv) for i in p.loop_indices] for p in mesh.polygons] if uv else None
        groups = {g.index: g.name for g in obj.vertex_groups}
        weights = [{groups[g.group]: g.weight for g in v.groups if g.weight > 0} for v in mesh.vertices]
        result = recover(row, ids, vertices, [list(p.vertices) for p in mesh.polygons],
                         uv_faces, weights, allow_weights)
        if mesh.shape_keys:
            if any(key.relative_key != mesh.shape_keys.key_blocks[0]
                   for key in mesh.shape_keys.key_blocks[1:]):
                raise ValueError('Only shape keys relative to Basis are supported')
            morphs = {}
            for key in mesh.shape_keys.key_blocks[1:]:
                deltas = [None] * len(ids)
                for i, original in enumerate(ids):
                    deltas[original] = list(key.data[i].co-basis[i].co)
                    if any(not math.isfinite(v) for v in deltas[original]):
                        raise ValueError('Nonfinite shape-key coordinates')
                morphs[key.name] = deltas
            if set(morphs) != set(row.get('morphs', {})):
                raise ValueError('Morph names changed; update OSP explicitly through rebuild route')
            result['morphs'] = morphs
        elif row.get('morphs'):
            raise ValueError('Source morph shape keys were removed')
        out['meshes'][k] = result
    return out


def main():
    import bpy
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='mode', required=True)
    imp = sub.add_parser('import'); imp.add_argument('snapshot', type=Path)
    imp.add_argument('--blend', required=True, type=Path)
    exp = sub.add_parser('export'); exp.add_argument('snapshot', type=Path)
    exp.add_argument('--out', required=True, type=Path)
    exp.add_argument('--allow-weight-edits', action='store_true')
    args = ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    raw = args.snapshot.read_bytes(); snapshot = json.loads(raw.decode('utf-8-sig'))
    if snapshot.get('coordinate_space') != 'nif_shape_local' or not snapshot.get('meshes'):
        raise ValueError('Expected a nonempty NIF shape-local snapshot')
    names = [m['name'] for m in snapshot['meshes']]
    if len(names) != len(set(names)):
        raise ValueError('Source shape names must be unique')
    target = args.blend if args.mode == 'import' else args.out
    if target.exists() or target.resolve() == args.snapshot.resolve():
        raise ValueError('Refusing to overwrite source or existing output')
    if args.mode == 'import':
        if target.suffix.lower() != '.blend':
            raise ValueError('Import output must have a .blend extension')
        # Factory scene only: never clear or overwrite a user's loaded project.
        if bpy.data.filepath or any(o.type == 'MESH' and o.name != 'Cube' for o in bpy.data.objects):
            raise ValueError('Import requires --factory-startup in an unsaved scene')
        signature = hashlib.sha256(raw).hexdigest()
        import_scene(bpy, snapshot, signature)
        target.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target.resolve()))
    else:
        result = export_scene(bpy, snapshot, hashlib.sha256(raw).hexdigest(), args.allow_weight_edits)
        encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('x', encoding='utf-8') as f:
            f.write(encoded)
    print('INDEXED_BRIDGE', args.mode, 'complete; no NIF/OSD written')


if __name__ == '__main__':
    main()
