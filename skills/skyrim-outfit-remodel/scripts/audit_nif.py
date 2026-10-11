"""Read NIF via an external PyNifly installation. Never save or rewrite the NIF."""
import argparse
import hashlib
from pathlib import Path
import sys
from audit_mesh import audit, write


def load_reader(root,dll):
    sys.path.insert(0,str(Path(root).resolve()))
    from pyn import pynifly
    pynifly.NifFile.Load(str(Path(dll).resolve()))
    return pynifly


def snapshot_file(reader,path):
    nf=reader.NifFile(str(Path(path).resolve()))
    snapshot={'schema':1,'producer':'PyNifly_read_only','coordinate_space':'nif_shape_local',
              'game':nf.game,'source_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'meshes':[]}
    for shape in nf.shapes:
        verts=shape.verts; faces=[list(t) for t in shape.tris];uv=shape.uvs
        weights=[{} for _ in verts]
        for bone,entries in shape.bone_weights.items():
            for i,w in entries:
                if not 0<=i<len(verts):
                    raise ValueError('Bone weight vertex index out of range')
                weights[i][bone]=w
        extras=[]
        for parent in (shape,nf.root):
            for extra in parent.extra_data(blockname='NiStringExtraData'):
                extras.append({'name':extra.name,'value':extra.string_data})
        snapshot['meshes'].append({'name':shape.name,'vertices':[list(v) for v in verts],'faces':faces,
          'uv_faces':[[list(uv[i]) for i in face] for face in faces] if len(uv)==len(verts) else None,
          'normals':[list(n) for n in shape.normals],'weights':weights,'skinned':bool(shape.bone_names),
          'bones':list(shape.bone_names),'matrix_world':None,'textures':shape.textures,
          'partitions':[p.id for p in shape.partitions],'extra_strings':extras})
    return snapshot


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('nif');p.add_argument('--pynifly-root',required=True);p.add_argument('--dll',required=True)
    p.add_argument('--out',required=True);p.add_argument('--snapshot')
    args=p.parse_args(); before=hashlib.sha256(Path(args.nif).read_bytes()).hexdigest()
    reader=load_reader(args.pynifly_root,args.dll);snapshot=snapshot_file(reader,args.nif)
    result=audit(snapshot); result['game']=snapshot['game']; result['source_sha256']=before
    result['resources']=[{k:m[k] for k in ('name','textures','partitions','extra_strings')} for m in snapshot['meshes']]
    result['source_unchanged']=before==hashlib.sha256(Path(args.nif).read_bytes()).hexdigest()
    result['skin_transforms_test']='not_run';result['partition_face_coverage']='not_run'
    result['resource_winner_test']='not_run';result['reader_dll_sha256']=hashlib.sha256(Path(args.dll).read_bytes()).hexdigest()
    if args.snapshot: write(args.snapshot,snapshot)
    write(args.out,result);print({'pass':result['pass'],'source_unchanged':result['source_unchanged']})
    return 0 if result['pass'] and result['source_unchanged'] else 2


if __name__=='__main__':
    raise SystemExit(main())
