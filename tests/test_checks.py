"""Synthetic failure/contract tests. No third-party assets or external runtimes."""
import copy
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'skyrim-outfit-remodel'
sys.path.insert(0, str(SKILL / 'scripts'))
import audit_mesh
import audit_bodyslide as bs
import build_bodyslide as builder
import compare_mesh
import manifest


def mesh():
    return {'name':'Equipment', 'vertices':[[0,0,0],[1,0,0],[1,1,0],[0,1,0]],
            'faces':[[0,1,2,3]], 'uv_faces':[[[0,0],[1,0],[1,1],[0,1]]],
            'normals':[[0,0,1]]*4, 'weights':[{'Bone':1.0} for _ in range(4)],
            'skinned':True, 'bones':['Bone'], 'matrix_world':None}


def snapshot():
    return {'schema':1,'coordinate_space':'test_local','meshes':[mesh()]}


def s8(value):
    value=value.encode('ascii'); return struct.pack('<B',len(value))+value


def osd(index=1,version=1):
    return b'\x00DSO'+struct.pack('<II',version,1)+s8('EquipmentSize')+struct.pack('<HH3f',1,index,0.0,0.0,0.5)


def trip(index=1):
    return b'PIRT'+struct.pack('<H',1)+s8('Equipment')+struct.pack('<H',1)+s8('Size')+struct.pack('<fHH3h',0.01,1,index,0,0,50)


class MeshTests(unittest.TestCase):
    def test_valid_quad_has_open_boundary(self):
        result=audit_mesh.audit(snapshot())
        self.assertTrue(result['pass'])
        self.assertEqual(result['meshes'][0]['triangles_equivalent'],2)
        self.assertEqual(result['meshes'][0]['boundary_edges'],4)
        self.assertEqual(result['pose_test'],'not_run')

    def test_invalid_geometry_and_duplicates(self):
        for face,error in [([0,0,1],'invalid_faces'),([0,1,99],'invalid_faces'),([0,1,2,3],'duplicate_faces')]:
            value=mesh();value['faces'].append(face);value['uv_faces'].append([[0,0]]*len(face))
            self.assertTrue(any(error in e for e in audit_mesh.audit_mesh(value)['errors']))
        value=mesh();value['vertices']=[[0,0,0]]*4
        self.assertIn('degenerate_faces:1',audit_mesh.audit_mesh(value)['errors'])

    def test_nonfinite_coordinates_and_uv(self):
        value=mesh();value['vertices'][0][0]=float('nan');value['uv_faces'][0][0][0]=float('inf')
        report=audit_mesh.audit_mesh(value)
        self.assertIn('nonfinite_or_invalid_coordinates',report['errors'])
        self.assertIn('invalid_uv_corners',report['errors'])

    def test_weights_reject_zero_negative_nonfinite_unknown_and_five(self):
        cases=[({},'unweighted_vertices:1'),({'Bone':-1},'invalid_weights:1'),
               ({'Bone':math.inf},'invalid_weights:1'),({'Wrong':1},'unknown_bones:Wrong'),
               ({'Bone':0.5},'weights_not_normalized')]
        for weights,error in cases:
            with self.subTest(error=error):
                value=mesh();value['weights'][0]=weights
                self.assertIn(error,audit_mesh.audit_mesh(value)['errors'])
        value=mesh();value['bones']=[str(i) for i in range(5)];value['weights']=[{b:0.2 for b in value['bones']}]*4
        self.assertIn('too_many_bone_influences',audit_mesh.audit_mesh(value)['errors'])

    def test_bad_counts_and_static_mesh(self):
        value=mesh();value['weights']=[]
        self.assertIn('weight_vertex_count_mismatch',audit_mesh.audit_mesh(value)['errors'])
        value['skinned']=False
        self.assertFalse(audit_mesh.audit_mesh(value)['errors'])
        value['normals']=[]
        self.assertIn('invalid_normals',audit_mesh.audit_mesh(value)['errors'])

    def test_degenerate_uv_is_warning_not_visual_acceptance(self):
        value=mesh();value['uv_faces']=[[[0,0]]*4]
        result=audit_mesh.audit({'meshes':[value]})
        self.assertTrue(result['pass'])
        self.assertIn('degenerate_uv_faces:1',result['meshes'][0]['warnings'])
        self.assertEqual(result['uv_overlap_test'],'not_run')

    def test_empty_or_duplicate_shape_fails(self):
        self.assertFalse(audit_mesh.audit({'meshes':[]})['pass'])
        self.assertFalse(audit_mesh.audit({'meshes':[mesh(),mesh()]})['pass'])


class ProtectionTests(unittest.TestCase):
    def test_protected_move_requires_explicit_allow_map(self):
        before=snapshot();after=copy.deepcopy(before);after['meshes'][0]['vertices'][1][2]=0.1
        self.assertFalse(compare_mesh.compare(before,after)['pass'])
        self.assertTrue(compare_mesh.compare(before,after,{'Equipment':[1]})['pass'])

    def test_uv_topology_or_space_changes_fail_even_if_movement_allowed(self):
        before=snapshot()
        for key in ['uv_faces','faces','coordinate_space']:
            after=copy.deepcopy(before)
            if key=='coordinate_space':after[key]='world'
            elif key=='faces':after['meshes'][0][key]=[[0,1,2],[0,2,3]]
            else:after['meshes'][0][key][0][0]=[0.1,0.1]
            self.assertFalse(compare_mesh.compare(before,after,{'Equipment':[0,1,2,3]})['pass'])

    def test_count_invalid_allow_empty_and_tolerance_fail(self):
        before=snapshot();after=copy.deepcopy(before);after['meshes'][0]['vertices'].pop()
        self.assertFalse(compare_mesh.compare(before,after)['pass'])
        self.assertFalse(compare_mesh.compare(before,before,{'Equipment':[99]})['pass'])
        self.assertFalse(compare_mesh.compare({'meshes':[]},{'meshes':[]})['pass'])
        with self.assertRaises(ValueError):compare_mesh.compare(before,before,tolerance=-1)

    def test_nonfinite_move_can_be_reported_without_nan_json(self):
        before=snapshot();after=copy.deepcopy(before);after['meshes'][0]['vertices'][0][0]=math.inf
        result=compare_mesh.compare(before,after)
        self.assertFalse(result['pass'])
        json.dumps(result,allow_nan=False)


class MorphTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.base=self.root/'CalienteTools'/'BodySlide'/'ShapeData'/'Outfit';self.base.mkdir(parents=True)
        (self.base/'source.nif').write_bytes(b'SYNTHETIC PLACEHOLDER - not a NIF')
        (self.base/'source.osd').write_bytes(osd())
        self.osp=self.root/'project.osp'
        self.osp.write_text('<SliderSetInfo version="1"><SliderSet name="Test"><DataFolder>Outfit</DataFolder><SourceFile>source.nif</SourceFile><OutputPath>meshes/Outfit</OutputPath><OutputFile GenWeights="true">outfit</OutputFile><Shape target="Equipment">Equipment</Shape><Slider name="Size"><Data target="Equipment" local="true">source.osd/EquipmentSize</Data></Slider></SliderSet></SliderSetInfo>',encoding='utf8')

    def test_local_osp_and_osd_validated_against_source(self):
        result=bs.inspect(self.osp,'Test',self.root,snapshot())
        self.assertTrue(result['pass']);self.assertTrue(result['coverage']['osd_indices'])
        self.assertEqual(result['coverage']['actual_build'],'not_run')

    def test_bad_index_truncation_version_and_wrong_container_fail(self):
        (self.base/'source.osd').write_bytes(osd(index=4))
        with self.assertRaises(ValueError):bs.inspect(self.osp,'Test',self.root,snapshot())
        for raw in [osd()[:-1],osd(version=2),b'OTHER']:
            (self.base/'source.osd').write_bytes(raw)
            with self.assertRaises(ValueError):bs.osd_entries(self.base/'source.osd')

    def test_unknown_project_or_external_data_not_silently_accepted(self):
        with self.assertRaises(ValueError):bs.inspect(self.osp,'Missing',self.root)
        text=self.osp.read_text(encoding='utf8').replace('local="true"','local="false"')
        self.osp.write_text(text,encoding='utf8')
        self.assertFalse(bs.inspect(self.osp,'Test',self.root)['pass'])

    def test_trip_requires_runtime_snapshot_and_rejects_wrong_indices(self):
        path=self.root/'outfit.tri';path.write_bytes(trip())
        with self.assertRaises(ValueError):bs.inspect(self.osp,'Test',self.root,snapshot(),path)
        self.assertTrue(bs.inspect(self.osp,'Test',self.root,snapshot(),path,snapshot())['pass'])
        path.write_bytes(trip(index=4))
        with self.assertRaises(ValueError):bs.inspect(self.osp,'Test',self.root,snapshot(),path,snapshot())

    def test_head_tri_trailing_bytes_and_duplicate_indices_rejected(self):
        path=self.root/'bad.tri'
        for raw in [b'FRTRI003',trip()+b'extension',trip()[:-1]]:
            path.write_bytes(raw)
            with self.assertRaises(ValueError):bs.trip_entries(path)
        with self.assertRaises(ValueError):bs.validate_diffs([(1,0,0,0),(1,0,0,1)],4)

    def test_trip_optional_empty_and_nonempty_uv_blocks(self):
        path=self.root/'uv.tri';path.write_bytes(trip()+struct.pack('<H',0))
        self.assertEqual(bs.trip_entries(path)['uv'],{})
        uv=struct.pack('<H',1)+s8('Equipment')+struct.pack('<H',1)+s8('UVSize')+struct.pack('<fHH2h',0.01,1,2,10,-20)
        path.write_bytes(trip()+uv)
        result=bs.inspect(self.osp,'Test',self.root,snapshot(),path,snapshot())
        self.assertTrue(result['pass']);self.assertEqual(result['trip']['uv'],{'Equipment':1})
        bad_uv=uv[:-6]+struct.pack('<H2h',99,10,-20);path.write_bytes(trip()+bad_uv)
        with self.assertRaises(ValueError):bs.inspect(self.osp,'Test',self.root,snapshot(),path,snapshot())

    def test_osp_target_alias_resolves_to_actual_source_shape(self):
        text=self.osp.read_text(encoding='utf8').replace('target="Equipment"','target="Alias"')
        self.osp.write_text(text,encoding='utf8')
        self.assertTrue(bs.inspect(self.osp,'Test',self.root,snapshot())['pass'])

    def test_unknown_schema_and_escaping_output_path_fail(self):
        text=self.osp.read_text(encoding='utf8')
        for edited in [text.replace('version="1"','version="2"'),text.replace('meshes/Outfit','../outside')]:
            self.osp.write_text(edited,encoding='utf8')
            with self.assertRaises(ValueError):bs.inspect(self.osp,'Test',self.root,snapshot())

    def test_empty_snapshot_cannot_claim_morph_index_coverage(self):
        with self.assertRaises(ValueError):bs.inspect(self.osp,'Test',self.root,{'meshes':[]})

    def test_constant_hidden_nonzero_geometry_is_reported_as_dependency(self):
        text=self.osp.read_text(encoding='utf8').replace('<Slider name="Size">','<Slider name="Size" hidden="true" small="100" big="100">')
        self.osp.write_text(text,encoding='utf8')
        report=bs.inspect(self.osp,'Test',self.root,snapshot())
        self.assertTrue(report['pass'])
        self.assertEqual(report['constant_hidden_geometry'][0]['coefficient'],1)
        self.assertIn('raw_zero_basis_differs_from_default_corrected_basis',report['warnings'])

    def test_weight_dependent_zap_invert_and_zero_hidden_are_not_constant_geometry(self):
        for attrs in ['hidden="true" small="100" big="0"','hidden="true" small="0" big="0"',
                      'hidden="true" small="100" big="100" zap="true"',
                      'hidden="true" small="100" big="100" invert="true"',
                      'hidden="true" small="100" big="100" uv="true"']:
            slider=bs.ET.fromstring('<Slider '+attrs+'/>')
            self.assertIsNone(bs.constant_hidden_geometry(slider),attrs)

    def test_unsafe_resource_paths_rejected(self):
        for value in ['../outside','C:/outside','C:outside','/outside','\\\\server\\file','safe/../outside','']:
            with self.subTest(path=value),self.assertRaises(ValueError):bs.relative(value)


class ManifestTests(unittest.TestCase):
    def test_missing_extra_changed_and_self_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);one=root/'one.txt';one.write_text('one',encoding='utf8')
            target=root/'manifest.json';data={'files':manifest.files(root,target)};audit_mesh.write(target,data)
            (root/'nested').mkdir()
            alternate=root/'nested'/'..'/'manifest.json'
            self.assertEqual(manifest.files(root,alternate),data['files'])
            self.assertTrue(manifest.verify(root,data,target)['pass'])
            one.write_text('changed',encoding='utf8');(root/'extra.txt').write_text('x',encoding='utf8')
            result=manifest.verify(root,data,target);self.assertEqual(result['changed'],['one.txt']);self.assertEqual(result['extra'],['extra.txt'])
            one.unlink();self.assertEqual(manifest.verify(root,data,target)['missing'],['one.txt'])

    def test_manifest_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp,self.assertRaises(ValueError):
            manifest.verify(tmp,{'files':{'../bad':{}}})


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.exe=self.root/'fake.exe';self.exe.write_bytes(b'not executable')

    def test_existing_or_unsafe_stage_cannot_launch(self):
        with patch.object(builder.subprocess,'run') as run:
            with self.assertRaises(ValueError):builder.build(self.exe,'Test','Preset',self.root,['meshes/a.nif'])
            with self.assertRaises(ValueError):builder.build(self.exe,'Test','Preset',self.root/'new',['../bad'])
            run.assert_not_called();self.assertFalse((self.root/'new').exists())

    def test_exit_zero_without_outputs_is_failure(self):
        with patch.object(builder.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'',b'')):
            result=builder.build(self.exe,'Test','Preset',self.root/'new',['meshes/a.nif'])
        self.assertFalse(result['pass']);self.assertEqual(len(result['missing_or_empty']),1)

    def test_fresh_output_has_hash_and_does_not_claim_mesh_or_game(self):
        def fake_run(command,**kwargs):
            target=Path(command[command.index('--targetdir')+1])/'meshes'/'a.nif'
            target.parent.mkdir();target.write_bytes(b'synthetic output')
            return subprocess.CompletedProcess(command,0,b'build',b'')
        with patch.object(builder.subprocess,'run',side_effect=fake_run):
            result=builder.build(self.exe,'Test','Preset',self.root/'new',['meshes/a.nif'])
        self.assertTrue(result['pass']);self.assertEqual(len(result['outputs'][0]['sha256']),64)
        self.assertEqual(result['mesh_validation'],'not_run');self.assertEqual(result['game_test'],'not_run')

    def test_timeout_remains_failure_with_logs(self):
        with patch.object(builder.subprocess,'run',side_effect=subprocess.TimeoutExpired(['fake'],1,output=b'partial')):
            result=builder.build(self.exe,'Test','Preset',self.root/'new',['meshes/a.nif'],timeout=1)
        self.assertFalse(result['pass']);self.assertIsNone(result['returncode'])
        self.assertEqual((self.root/'new'/'stdout.log').read_bytes(),b'partial')


class PackagingTests(unittest.TestCase):
    def test_utf8_local_markdown_links_and_no_machine_paths(self):
        for path in ROOT.rglob('*'):
            if '.local-validation' in path.parts or '.git' in path.parts:continue
            if path.suffix not in ('.md','.py','.yaml','.yml','.json'):continue
            text=path.read_text(encoding='utf-8-sig')
            if path.suffix=='.md':
                self.assertNotRegex(text,r'[A-Za-z]:[/\\]Users[/\\][^\s/\\<>]+',str(path))
                for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
                    if '://' in link or link.startswith('#'):continue
                    target=(path.parent/link.split('#',1)[0]).resolve()
                    self.assertTrue(target.is_file(),f'{path}: broken link {link}')

    def test_entry_metadata_and_default_prompt(self):
        text=(SKILL/'SKILL.md').read_text(encoding='utf8')
        self.assertTrue(text.startswith('---\nname: skyrim-outfit-remodel\n'))
        self.assertLess(len(text.splitlines()),100)
        ui=(SKILL/'agents'/'openai.yaml').read_text(encoding='utf-8-sig')
        self.assertIn('$skyrim-outfit-remodel',ui)
        self.assertIn('全身装备重塑',ui)
        json.loads((SKILL/'assets'/'job.template.json').read_text(encoding='utf8'))


if __name__=='__main__':
    unittest.main()
