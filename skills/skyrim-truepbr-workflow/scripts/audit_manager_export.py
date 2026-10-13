"""Audit prepared BC7 .tpbr inputs/native exports; derive coat-compatible JSON.

Python 3.10+, standard library for audits; jsonschema for deployment JSON.
No live-mod writes, NIF mutation, source overwrite, or native-export simulation.
"""
import argparse
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path, PurePosixPath

SUFFIX = {"diffuse": ".dds", "normal": "_n.dds", "rmaos": "_rmaos.dds",
          "coat_normal_roughness": "_cnr.dds", "coat_color": "_s.dds"}
COLOR = {"diffuse", "coat_color"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def match_key(value):
    value = value.replace("\\", "/").lower().removesuffix(".dds")
    if value.startswith("textures/"):
        value = value[9:]
    return value


def safe_match(value):
    value = value.replace("\\", "/")
    p = PurePosixPath(value)
    require(bool(value) and not p.is_absolute() and ".." not in p.parts
            and ":" not in value, f"Unsafe match path: {value!r}")
    require(not value.lower().startswith(("textures/", "pbr/")),
            f"Project match must omit textures/pbr prefix: {value}")
    return p


def bc7_info(path, slot):
    path = Path(path)
    with path.open("rb") as f:
        b = f.read(148)
    require(len(b) == 148 and b[:4] == b"DDS " and b[84:88] == b"DX10",
            f"Expected DX10 DDS: {path}")
    require(struct.unpack_from("<I", b, 4)[0] == 124, f"Invalid DDS header: {path}")
    height, width = struct.unpack_from("<II", b, 12)
    mips = struct.unpack_from("<I", b, 28)[0]
    fmt, dimension, misc, array_size = struct.unpack_from("<4I", b, 128)
    require(width > 0 and height > 0 and dimension == 3 and array_size == 1
            and not (misc & 4), f"Expected single 2D texture: {path}")
    require(fmt == (99 if slot in COLOR else 98),
            f"Wrong BC7 color space for {slot}: DXGI={fmt}, {path}")
    require(mips == math.floor(math.log2(max(width, height))) + 1,
            f"Incomplete mip chain ({mips}): {path}")
    expected = 148 + sum(max(1, (max(1, width >> i) + 3) // 4)
                         * max(1, (max(1, height >> i) + 3) // 4) * 16
                         for i in range(mips))
    require(path.stat().st_size == expected,
            f"DDS size differs from declared mip payload: {path}")
    return {"width": width, "height": height, "mips": mips,
            "dxgi": fmt, "bytes": expected, "sha256": sha(path)}


def audit_project(project_path, export_root=None):
    p = read_json(project_path)
    require(p.get("version") == "1.0", "Unsupported .tpbr version")
    sets = p.get("texture_sets", [])
    require(bool(sets), "Project has no texture sets")
    seen, destinations, results = set(), set(), []
    for ts in sets:
        match = safe_match(ts["match_texture"])
        mode = ts.get("match_texture_mode", "auto")
        if mode == "auto":
            mode = "normal" if match.stem.lower().endswith(("_n", "_msn")) else "diffuse"
        require(mode in ("diffuse", "normal"), f"Unsupported matcher: {mode}")
        key = (mode, match_key(str(match)))
        require(key not in seen, f"Duplicate material matcher: {key}")
        seen.add(key)
        require(not ts.get("match_aliases"), "Audit aliases separately; this profile requires one-to-one matches")
        require(not ts.get("channel_maps") and ts.get("rmaos_source_mode") == "packed",
                "This audit profile requires an already packed RMAOS")
        require(not ts.get("slot_path_overrides"), "Audit explicit path overrides separately")
        f = ts.get("features", {})
        require(all(isinstance(v, bool) for v in f.values()), "Feature switches must be booleans")
        coat = f.get("multilayer", False)
        require(coat or not f.get("coat_normal"),
                "coat_normal conflicts with an absent or false multilayer switch")
        require(coat or not f.get("coat_diffuse"), "coat_diffuse requires multilayer")
        require(not any(v for k, v in f.items() if k not in
                        ("multilayer", "coat_normal", "coat_diffuse")),
                "This profile supports the base shader and clearcoat; audit other features separately")
        name = re.sub(r'[<>:"/\\|?*]', "_", ts.get("name") or match.stem) or "texture_set"
        textures = ts.get("textures", [])
        slots = [t["slot"] for t in textures]
        require(len(set(slots)) == len(slots), f"Duplicate slots: {ts['name']}")
        required = {"diffuse", "normal", "rmaos"}
        if f.get("coat_normal"):
            required.add("coat_normal_roughness")
        if f.get("coat_diffuse"):
            required.add("coat_color")
        require(required <= set(slots), f"Missing required slots: {required - set(slots)}")
        items = []
        for tex in textures:
            slot = tex["slot"]
            require(slot in SUFFIX, f"Unsupported slot in packed-BC7 profile: {slot}")
            src = Path(tex["path"])
            if not src.is_absolute():
                src = Path(project_path).resolve().parent / src
            info = bc7_info(src, slot)
            expected_compression = "bc7_srgb" if slot in COLOR else "bc7_linear"
            require(ts.get("export_compression", {}).get(slot) == expected_compression,
                    f"Export compression must be explicit for {ts['name']}/{slot}")
            for dim in ("width", "height"):
                require(dim not in tex or tex[dim] == info[dim], f"Stale {dim}: {src}")
            relative = PurePosixPath("textures/pbr") / match.parent / (name + SUFFIX[slot])
            require(str(relative).lower() not in destinations, f"Export collision: {relative}")
            destinations.add(str(relative).lower())
            item = {"slot": slot, "source": str(src), "relative": str(relative), **info}
            if export_root is not None:
                target = Path(export_root) / str(relative)
                out = bc7_info(target, slot)
                require(out["sha256"] == info["sha256"],
                        f"Native export re-encoded or changed DDS; decoded QA required: {target}")
                item["export_sha256"] = out["sha256"]
            items.append(item)
        sizes = {(x["width"], x["height"]) for x in items}
        require(len(sizes) == 1, f"Mismatched map dimensions: {ts['name']}")
        results.append({"name": ts["name"], "mode": mode, "match": key[1],
                        "coat": coat, "textures": items})
    if export_root is not None:
        actual = {x.relative_to(export_root).as_posix().lower()
                  for x in Path(export_root).rglob("*.dds")}
        require(actual == destinations,
                f"Export DDS inventory differs: extra={sorted(actual - destinations)}, "
                f"missing={sorted(destinations - actual)}")
    return p, results


def compatible_json(project, materials, raw_path):
    raw = read_json(raw_path)
    require(isinstance(raw, list) and len(raw) == len(materials),
            "Native JSON must contain exactly one entry per project material")
    expected = {(x["mode"], x["match"]): (x, ts)
                for x, ts in zip(materials, project["texture_sets"])}
    changes, seen = [], set()
    for index, entry in enumerate(raw):
        fields = [k for k in ("texture", "match_diffuse", "match_normal") if k in entry]
        require(len(fields) == 1, f"Ambiguous native matcher at entry {index}")
        field = fields[0]
        key = ("normal" if field == "match_normal" else "diffuse", match_key(entry[field]))
        require(key in expected and key not in seen, f"Unexpected/duplicate native match: {key}")
        seen.add(key)
        material, ts = expected[key]
        coat = material["coat"]
        for flag in ("emissive", "parallax", "subsurface", "subsurface_foliage", "hair"):
            require(entry.get(flag, False) is False, f"Unexpected enabled feature {flag}: {key}")
        require(not entry.get("fuzz") and not entry.get("glint"), f"Unexpected layer: {key}")
        require(not any(k.startswith("slot") for k in entry),
                f"Audit explicit native slot overrides separately: {key}")
        require("rename" not in entry or entry["rename"] == ts["name"],
                f"Unexpected native rename: {key}")
        if coat and "multilayer" not in entry:
            entry["multilayer"] = True
            changes.append({"index": index, "match": key[1], "added": {"multilayer": True}})
        require(entry.get("multilayer", False) is coat,
                f"Project/native multilayer conflict: {key}")
        for flag in ("coat_normal", "coat_diffuse", "coat_parallax"):
            if coat:
                require(entry.get(flag, False) is bool(ts.get("features", {}).get(flag)),
                        f"Project/native {flag} differs: {key}")
        params = ts.get("params", {})
        for name in ("specular_level", "roughness_scale", "displacement_scale",
                     "subsurface_opacity", "subsurface_color", "coat_strength",
                     "coat_roughness", "coat_specular_level"):
            if name in params and (coat or not name.startswith("coat_")):
                value = params[name]
                value = [round(v, 3) for v in value] if isinstance(value, list) else round(value, 3)
                require(entry.get(name) == value, f"Project/native {name} differs: {key}")
    return raw, changes


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project", type=Path)
    ap.add_argument("--export-root", type=Path)
    ap.add_argument("--raw-json", type=Path)
    ap.add_argument("--patched-json", type=Path)
    ap.add_argument("--schema", type=Path)
    ap.add_argument("--report", required=True, type=Path)
    a = ap.parse_args()
    for path in (a.report, a.patched_json):
        require(path is None or not path.exists(), f"Refusing to overwrite {path}")
    require(not a.patched_json or (a.raw_json and a.schema and a.export_root),
            "Deployment JSON requires actual export root, raw JSON and target schema")
    report = {"project": str(a.project), "project_sha256": sha(a.project),
              "acceptance": "static packed-BC7 audit; no game or patcher execution claim"}
    try:
        project, materials = audit_project(a.project, a.export_root)
        report.update(material_count=len(materials), materials=materials,
                      native_export_dds_byte_exact=a.export_root is not None)
        if a.raw_json:
            fixed, changes = compatible_json(project, materials, a.raw_json)
            report.update(raw_json_sha256=sha(a.raw_json), changes=changes)
            if a.schema:
                import jsonschema
                schema = read_json(a.schema)
                jsonschema.validators.validator_for(schema)(schema).validate(fixed)
                report["schema_sha256"] = sha(a.schema)
                report["schema_valid"] = True
            if a.patched_json:
                write_new(a.patched_json, fixed)
                report["deployment_json_sha256"] = sha(a.patched_json)
        report["passed"] = True
    except (ValueError, OSError, KeyError, ImportError) as exc:
        report.update(passed=False, error=str(exc))
    except Exception as exc:
        report.update(passed=False, error=f"{type(exc).__name__}: {exc}")
    write_new(a.report, report)
    print(json.dumps({k: v for k, v in report.items() if k not in ("materials",)}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
