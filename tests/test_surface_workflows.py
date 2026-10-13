import copy
import importlib.util
from pathlib import Path
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/skyrim-outfit-remodel/scripts'
def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name+'.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
surface = load('surface_transfer')
bridge = load('indexed_blender_bridge')


class SurfaceTests(unittest.TestCase):
    def data(self):
        return {'donor_vertices': [[0,0,0],[2,0,0],[0,2,0]],
                'donor_weights': [{'A':1},{'B':1},{'C':1}],
                'donor_morphs': {'Size': [[0,0,0],[0,0,2],[0,0,4]]},
                'map': [{'indices':[0,1,2], 'weights':[.5,.25,.25], 'offset':[0,0,.1]}]}

    def test_one_map_drives_base_skin_and_morph_without_adding_offset_to_delta(self):
        result = surface.transfer(self.data())
        self.assertEqual(result['vertices'], [[.5,.5,.1]])
        self.assertEqual(result['weights'], [{'A':.5,'B':.25,'C':.25}])
        self.assertEqual(result['morphs']['Size'], [[0,0,1.5]])
        self.assertFalse(result['nif_written'])

    def test_wrong_correspondence_and_morph_length_fail(self):
        for row in ({'indices':[99], 'weights':[1]}, {'indices':[0], 'weights':[-1]},
                    {'indices':[0], 'weights':[.5]}):
            data=self.data(); data['map']=[row]
            with self.assertRaises(ValueError): surface.transfer(data)
        data=self.data(); data['donor_morphs']['Size'].pop()
        with self.assertRaises(ValueError): surface.transfer(data)

    def test_top_four_are_selected_by_bone_name_then_normalized(self):
        values=[{'A':.3,'B':.25,'C':.2,'D':.15,'E':.1}]
        result=surface.skin(values, {'indices':[0], 'weights':[1]})
        self.assertEqual(set(result), {'A','B','C','D'})
        self.assertAlmostEqual(sum(result.values()),1)

    def test_overflowing_offsets_do_not_produce_infinite_json(self):
        data=self.data(); data['donor_vertices']=[[0,0,1e308]]*3
        data['map'][0]['offset']=[0,0,1e308]
        with self.assertRaises(ValueError): surface.transfer(data)

    def test_seam_boundary_and_falloff_delta(self):
        self.assertEqual(surface.synchronize_delta([1,0,0],[1,0,0],[3,0,0],1),[3,0,0])
        self.assertEqual(surface.synchronize_delta([4,0,0],[1,0,0],[3,0,0],.5),[5,0,0])
        with self.assertRaises(ValueError): surface.synchronize_delta([0,0,0],[0,0,0],[0,0,0],2)


class IndexedBridgeTests(unittest.TestCase):
    def row(self):
        return {'vertices':[[0,0,0],[1,0,0],[0,1,0]], 'faces':[[0,1,2]],
                'uv_faces':[[[0,0],[1,0],[0,1]]], 'bones':['A'], 'skinned':True,
                'weights':[{'A':1}]*3, 'normals':[[0,0,1]]*3}

    def test_point_reordering_is_recovered_using_ids(self):
        row=self.row()
        result=bridge.recover(row,[2,0,1],[[0,1,0],[0,0,.1],[1,0,0]],[[1,2,0]],
                              row['uv_faces'],row['weights'])
        self.assertEqual(result['vertices'],[[0,0,.1],[1,0,0],[0,1,0]])
        self.assertNotIn('normals',result)

    def test_duplicate_ids_same_count_and_reversed_winding_fail(self):
        row=self.row()
        for ids,faces in (([0,0,2],row['faces']),([0,1,2],[[0,2,1]])):
            with self.assertRaises(ValueError):
                bridge.recover(row,ids,row['vertices'],faces,row['uv_faces'],row['weights'])

    def test_uv_edits_and_implicit_skin_edits_fail(self):
        row=self.row(); uv=copy.deepcopy(row['uv_faces']); uv[0][0][0]=.1
        with self.assertRaises(ValueError):
            bridge.recover(row,[0,1,2],row['vertices'],row['faces'],uv,row['weights'])
        row['bones'].append('B'); weights=[{'A':.5,'B':.5}]*3
        with self.assertRaises(ValueError):
            bridge.recover(row,[0,1,2],row['vertices'],row['faces'],row['uv_faces'],weights)
        result=bridge.recover(row,[0,1,2],row['vertices'],row['faces'],row['uv_faces'],weights,True)
        self.assertEqual(result['weights'],weights)


if __name__ == '__main__':
    unittest.main()
