"""Synthetic failure tests for the TruePBR export audit helpers."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TRUEPBR = ROOT / "skills" / "skyrim-truepbr-workflow"
sys.path.insert(0, str(TRUEPBR / "scripts"))
import audit_manager_export as manager


def dds_bc7(width=4, height=4, dxgi=99, mip_count=3):
    """Build the small DX10 BC7 DDS fixture expected by the audit helper."""
    header = bytearray(148)
    header[:4] = b"DDS "
    struct.pack_into("<I", header, 4, 124)
    struct.pack_into("<II", header, 12, height, width)
    struct.pack_into("<I", header, 28, mip_count)
    header[84:88] = b"DX10"
    struct.pack_into("<4I", header, 128, dxgi, 3, 0, 1)
    payload_size = sum(
        max(1, (max(1, width >> level) + 3) // 4)
        * max(1, (max(1, height >> level) + 3) // 4) * 16
        for level in range(mip_count)
    )
    return bytes(header) + bytes(payload_size)


def packed_project(folder, match="outfit/latex", duplicate=False):
    maps = []
    for slot, filename in (("diffuse", "base.dds"),
                           ("normal", "normal.dds"),
                           ("rmaos", "rmaos.dds")):
        (folder / filename).write_bytes(dds_bc7(dxgi=99 if slot == "diffuse" else 98))
        maps.append({"slot": slot, "path": filename})
    texture_set = {
        "name": "latex", "match_texture": match,
        "match_texture_mode": "diffuse", "features": {},
        "rmaos_source_mode": "packed", "channel_maps": {},
        "textures": maps,
        "export_compression": {
            "diffuse": "bc7_srgb", "normal": "bc7_linear",
            "rmaos": "bc7_linear",
        },
    }
    sets = [texture_set]
    if duplicate:
        sets.append({**texture_set, "name": "duplicate"})
    project = {"version": "1.0", "texture_sets": sets}
    path = folder / "project.tpbr"
    path.write_text(json.dumps(project), encoding="utf-8")
    return path


class TruePbrAuditTests(unittest.TestCase):
    def test_dds_header_mip_chain_and_slot_colorspace_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "synthetic.dds"
            path.write_bytes(b"NOPE" + dds_bc7()[4:])
            with self.assertRaisesRegex(ValueError, "Expected DX10 DDS"):
                manager.bc7_info(path, "diffuse")

            path.write_bytes(dds_bc7(mip_count=2))
            with self.assertRaisesRegex(ValueError, "Incomplete mip chain"):
                manager.bc7_info(path, "diffuse")

            path.write_bytes(dds_bc7(dxgi=98))
            with self.assertRaisesRegex(ValueError, "Wrong BC7 color space"):
                manager.bc7_info(path, "diffuse")

    def test_duplicate_material_matcher_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            project = packed_project(Path(temp), duplicate=True)
            with self.assertRaisesRegex(ValueError, "Duplicate material matcher"):
                manager.audit_project(project)

    def test_missing_multilayer_flag_is_added_only_for_explicit_coat(self):
        project = {"texture_sets": [{
            "name": "coat", "match_texture": "outfit/latex",
            "features": {"multilayer": True, "coat_normal": True}, "params": {},
        }]}
        materials = [{"mode": "diffuse", "match": "outfit/latex", "coat": True}]
        # The helper consumes JSON from disk; keep this fixture isolated and synthetic.
        with tempfile.TemporaryDirectory() as temp:
            raw_path = Path(temp) / "raw.json"
            raw_path.write_text(json.dumps([{"texture": "outfit/latex", "coat_normal": True}]),
                                encoding="utf-8")
            raw, changes = manager.compatible_json(project, materials, raw_path)
        self.assertIs(raw[0]["multilayer"], True)
        self.assertEqual(changes, [{"index": 0, "match": "outfit/latex",
                                    "added": {"multilayer": True}}])

    def test_conflicting_false_multilayer_is_not_silently_repaired(self):
        project = {"texture_sets": [{
            "name": "coat", "match_texture": "outfit/latex",
            "features": {"multilayer": True, "coat_normal": True}, "params": {},
        }]}
        materials = [{"mode": "diffuse", "match": "outfit/latex", "coat": True}]
        with tempfile.TemporaryDirectory() as temp:
            raw_path = Path(temp) / "raw.json"
            raw_path.write_text(json.dumps([{
                "texture": "outfit/latex", "multilayer": False, "coat_normal": True,
            }]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Project/native multilayer conflict"):
                manager.compatible_json(project, materials, raw_path)

    def test_report_and_patched_json_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report.json"
            output.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                manager.write_new(output, {"replace": True})
            with patch.object(sys, "argv", ["audit_manager_export.py", "missing.tpbr",
                                             "--report", str(output)]):
                with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                    manager.main()
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
