"""Run with Blender --background --disable-autoexec file.blend --python THIS -- --out SNAPSHOT."""
import argparse
import sys
from pathlib import Path


def main():
    import bpy
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from audit_mesh import write, audit
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True); p.add_argument('--report')
    p.add_argument('--objects',nargs='+',help='Exact mesh object names; default all meshes')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    objects=[o for o in bpy.data.objects if o.type=='MESH' and (not args.objects or o.name in args.objects)]
    if args.objects and set(args.objects)-{o.name for o in objects}:
        raise ValueError('Requested mesh objects not found')
    result={'schema':1,'producer':'blender_probe','blender_version':bpy.app.version_string,
            'coordinate_space':'object_local_basis','meshes':[]}
    for obj in objects:
        mesh=obj.data
        armatures=[m.object for m in obj.modifiers if m.type=='ARMATURE' and m.object]
        bones=sorted({b.name for a in armatures for b in a.data.bones})
        groups={g.index:g.name for g in obj.vertex_groups}
        weights=[{groups[g.group]:g.weight for g in v.groups if groups[g.group] in bones} for v in mesh.vertices]
        uv=mesh.uv_layers.active
        row={'name':obj.name,'vertices':[list(v.co) for v in mesh.vertices],
             'faces':[list(f.vertices) for f in mesh.polygons],
             'uv_faces':[[list(uv.data[i].uv) for i in f.loop_indices] for f in mesh.polygons] if uv else None,
             'normals':[list(v.normal) for v in mesh.vertices], 'weights':weights,
             'skinned':bool(armatures),'bones':bones,'matrix_world':[list(r) for r in obj.matrix_world],
             'modifiers':[{'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render} for m in obj.modifiers],
             'non_deform_groups':sorted(set(groups.values())-set(bones)),
             'shape_keys':{k.name:{'vertices':len(k.data),'value':k.value} for k in mesh.shape_keys.key_blocks} if mesh.shape_keys else {},
             'basis_only':True,'evaluated_surface':'not_sampled'}
        result['meshes'].append(row)
    write(args.out,result)
    if args.report:
        write(args.report,audit(result))
    print('REM0DEL_PROBE',len(objects),'mesh objects; source blend not saved')


if __name__=='__main__':
    main()
