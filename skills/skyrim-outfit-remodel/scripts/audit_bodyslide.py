"""Audit a named OSP project, local OSD datasets and optional BodySlide TRIP morph indices."""
import argparse
import io
import math
from pathlib import Path, PureWindowsPath
import struct
import xml.etree.ElementTree as ET
from audit_mesh import read, write


def relative(text):
    value=text.replace('\\','/')
    if not value or PureWindowsPath(value).is_absolute() or PureWindowsPath(value).drive or value.startswith('/') or '..' in value.split('/'):
        raise ValueError('Unsafe or empty resource path: '+text)
    return Path(value)


def take(stream,fmt):
    size=struct.calcsize(fmt); data=stream.read(size)
    if len(data)!=size: raise ValueError('Truncated morph data')
    return struct.unpack(fmt,data)


def string8(stream,encoding='utf8'):
    size,=take(stream,'<B');data=stream.read(size)
    if len(data)!=size: raise ValueError('Truncated morph name')
    return data.decode(encoding)


def osd_entries(path):
    stream=io.BytesIO(Path(path).read_bytes())
    if stream.read(4)!=b'\x00DSO': raise ValueError('Not supported OSD format')
    version,count=take(stream,'<II')
    if version!=1: raise ValueError('OSD version requires investigation: '+str(version))
    result={}
    for _ in range(count):
        name=string8(stream); n,=take(stream,'<H')
        if name in result: raise ValueError('Duplicate OSD dataset: '+name)
        result[name]=[take(stream,'<H3f') for _ in range(n)]
    if stream.read(): raise ValueError('Unexpected trailing OSD data')
    return result


def trip_block(stream,dimensions):
    count,=take(stream,'<H'); result={}
    for _ in range(count):
        name=string8(stream,'iso-8859-15');nm,=take(stream,'<H')
        if name in result: raise ValueError('Duplicate TRIP shape')
        result[name]={}
        for _ in range(nm):
            morph=string8(stream,'iso-8859-15');scale,=take(stream,'<f');nv,=take(stream,'<H')
            if not math.isfinite(scale): raise ValueError('Nonfinite TRIP scale')
            if morph in result[name]: raise ValueError('Duplicate TRIP morph')
            result[name][morph]=[(row[0],*(x*scale for x in row[1:])) for row in (take(stream,'<H'+str(dimensions)+'h') for _ in range(nv))]
    return result


def trip_entries(path):
    stream=io.BytesIO(Path(path).read_bytes())
    if stream.read(4)!=b'PIRT': raise ValueError('Not BodySlide TRIP; head TRI needs its own reader')
    position=trip_block(stream,3)
    # BodySlide v5.9.1 writes a UV block even when its shape count is zero.
    # Older position-only files may end here. A partial/unknown tail is rejected.
    uv=trip_block(stream,2) if stream.tell()<len(stream.getbuffer()) else {}
    if stream.read(): raise ValueError('Unexpected TRIP extension; investigate before acceptance')
    return {'position':position,'uv':uv}


def counts(snapshot):
    rows=snapshot['meshes']; result={m['name']:len(m['vertices']) for m in rows}
    if not rows: raise ValueError('Empty snapshot cannot validate morph indices')
    if len(rows)!=len(result): raise ValueError('Duplicate snapshot shape names')
    return result


def validate_diffs(diffs,count):
    if any(not 0<=d[0]<count or not all(math.isfinite(x) for x in d[1:]) for d in diffs):
        raise ValueError('Morph indices out of range or nonfinite offsets')
    if len({d[0] for d in diffs})!=len(diffs): raise ValueError('Duplicate vertex indices in morph')


def inspect(osp,project,data_root,source_snapshot=None,tri=None,runtime_snapshot=None):
    root=ET.parse(osp).getroot()
    if root.tag!='SliderSetInfo' or root.get('version')!='1':
        raise ValueError('Only SliderSetInfo version 1 is supported; investigate legacy/newer schemas')
    sets=[s for s in root.findall('SliderSet') if s.get('name')==project]
    if len(sets)!=1: raise ValueError('Project name missing or duplicated')
    s=sets[0];folder=relative(s.findtext('DataFolder',''));source=relative(s.findtext('SourceFile',''))
    base=Path(data_root)/'CalienteTools'/'BodySlide'/'ShapeData'/folder
    errors=[]; datasets=[]; cache={}
    if not (base/source).is_file(): errors.append('source_nif_missing')
    shape_targets={x.get('target') or (x.text or '').strip():(x.text or '').strip() for x in s.findall('Shape')}
    if not shape_targets or any(not k or not v for k,v in shape_targets.items()): errors.append('empty_shape_mapping')
    if len(shape_targets)!=len(s.findall('Shape')): errors.append('duplicate_shape_targets')
    source_counts=counts(source_snapshot) if source_snapshot is not None else None
    if source_counts and not set(shape_targets.values()).issubset(source_counts): errors.append('source_shapes_missing')
    for slider in s.findall('Slider'):
        for d in slider.findall('Data'):
            if d.get('local') not in ('true','1'):
                errors.append('external_dataset_requires_manual_resolution:'+str(d.text));continue
            text=(d.text or '').replace('\\','/')
            if '/' not in text:
                errors.append('dataset_reference_requires_investigation:'+text);continue
            filepart,entry=text.rsplit('/',1)
            path=base/relative(filepart)
            if not path.is_file():
                errors.append('dataset_file_missing:'+filepart);continue
            if path.suffix.lower()!='.osd':
                errors.append('unsupported_dataset_container:'+filepart);continue
            if path not in cache: cache[path]=osd_entries(path)
            if entry not in cache[path]:
                errors.append('dataset_entry_missing:'+entry);continue
            target=d.get('target')
            if target not in shape_targets: errors.append('dataset_target_unknown:'+str(target))
            if source_counts:
                shape_name=shape_targets.get(target)
                if shape_name not in source_counts: errors.append('dataset_shape_not_in_snapshot:'+str(shape_name))
                else: validate_diffs(cache[path][entry],source_counts[shape_name])
            datasets.append({'slider':slider.get('name'),'target':target,'entry':entry,'diffs':len(cache[path][entry])})
    tri_summary=None
    if tri:
        if not runtime_snapshot: raise ValueError('--tri requires --runtime-snapshot of the final game NIF')
        runtime_counts=counts(runtime_snapshot); trip=trip_entries(tri); tri_summary={}
        for kind,shapes in trip.items():
            tri_summary[kind]={}
            for shape,morphs in shapes.items():
                if shape not in runtime_counts: raise ValueError('TRIP shape missing from runtime snapshot: '+shape)
                for diffs in morphs.values(): validate_diffs(diffs,runtime_counts[shape])
                tri_summary[kind][shape]=len(morphs)
    output=s.find('OutputFile')
    if output is None: errors.append('missing_output_file')
    elif not (output.text or '').strip() or len(relative(output.text).parts)!=1:
        errors.append('output_file_must_be_a_nonempty_basename')
    if s.findtext('OutputPath'): relative(s.findtext('OutputPath'))
    return {'pass':not errors,'errors':errors,'project':project,'source':str(folder/source),
            'output_path':s.findtext('OutputPath'),'output_file':output.text if output is not None else None,
            'output_options':dict(output.attrib) if output is not None else {},'shapes':shape_targets,
            'sliders':[{'name':x.get('name'),**x.attrib} for x in s.findall('Slider')],
            'datasets':datasets,'trip':tri_summary,
            'coverage':{'osp_local_references':True,'osd_indices':source_counts is not None,
                        'trip_indices':tri is not None,'index_semantics':'not_tested','actual_build':'not_run','game':'not_run'}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('osp');p.add_argument('--project',required=True);p.add_argument('--data-root',required=True)
    p.add_argument('--source-snapshot');p.add_argument('--tri');p.add_argument('--runtime-snapshot');p.add_argument('--out',required=True)
    a=p.parse_args()
    try:
        result=inspect(a.osp,a.project,a.data_root,read(a.source_snapshot) if a.source_snapshot else None,a.tri,read(a.runtime_snapshot) if a.runtime_snapshot else None)
    except (ValueError,OSError,ET.ParseError,struct.error,UnicodeError,KeyError) as exc:
        result={'pass':False,'errors':[str(exc)]}
    write(a.out,result);print({'pass':result['pass']});return 0 if result['pass'] else 2


if __name__=='__main__':
    raise SystemExit(main())
