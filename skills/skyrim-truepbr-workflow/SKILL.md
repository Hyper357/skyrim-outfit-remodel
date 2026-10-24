---
name: skyrim-truepbr-workflow
description: Author, export, validate, and deploy Skyrim SE/AE TruePBR outfit materials with TruePBR Manager and PGPatcher. Use for PBR conversion of fitted clothing, armor, gloves, boots, and head coverings while preserving BodySlide compatibility and approved appearance.
---

# Skyrim TruePBR workflow

Produce an editable material project, a resource-complete mod, and evidence that distinguishes file validation, material preview, BodySlide building, and game acceptance.

For a complete ordered delivery checklist, read [references/end-to-end.md](references/end-to-end.md). Load the channel/compatibility details only for the current step.

## Establish the actual target

- Inspect the active MO2 profile, resource winners (including overwrite and PGPatcher output), renderer version, and shader configuration before editing. Work on staged copies and preserve a rollback manifest. Keep equipment records and identifiers unchanged unless the user requests record changes.
- Inventory runtime NIFs **and** BodySlide ShapeData/OSP/TRI inputs. A runtime-only material edit can disappear after a rebuild. Do not replace geometry, morphs, weights, UVs, alpha behavior, or approved colors during material conversion unless that work is within scope.
- Split the outfit into material zones (metal, latex, stockings, leather, cloth, skin, transparent) before authoring anything; a shared black albedo does not make every part latex. The source environment/matcap slot often carries the only zone evidence and is replaced during conversion, so record the per-shape evidence first. Zone rules and starting parameters are in [references/materials.md](references/materials.md).
- When the user requires multiple outfit variants to coexist, give each variant unique BodySlide `OutputFile`, model, and TRI paths, and create independent ARMO/ARMA equipment records. Multiple projects that still share output paths do not provide independent variants.
- Verify source versions instead of assuming the newest upstream code matches the installed tool. In a `Disable at Boot` configuration, `false` means the feature is not disabled; it does not mean the feature is off. Actual shader loading still needs runtime evidence.
- Read [references/materials.md](references/materials.md) for channel packing and shader details. Read [references/manager-compatibility.md](references/manager-compatibility.md) when using TruePBR Manager or diagnosing a coat that disappears after patching.

## Author and export

Use albedo, tangent normals, and physical maps with the existing UVs. Keep dielectric and metal regions distinct. Retain useful source folds and panel detail; do not bake studio highlights into base color. Treat actual transparency separately from a glossy resin appearance.

When parts of one black material class look grey beside an approved black part, compare both shapes in the same NIF where possible. Resolve MO2 texture winners and decode the base-color RGB/alpha before changing coat or specular values. A shared shader parameter set does not imply a shared perceived color. Follow the diagnostic order in [references/materials.md](references/materials.md).

For silver latex, state the intended flexible coating, reflections, and natural folds explicitly; do not assume the target is pure metallic chrome. When matching brass across different parts, compare the actual albedo, RMAOS, and normal maps against representative parts. A generic brightness multiplication alone is not sufficient evidence of a match.

For newly encoded color maps, compare decoded DDS pixels against the intended PNG using `scripts/audit_colour_roundtrip.py`; the input and output color spaces both matter. The material reference documents the verified texconv switches. Header validation alone cannot detect double gamma conversion.

TruePBR Manager projects are JSON `.tpbr` files, so bulk assignments can be authored with a script. Generate projects from an explicit material manifest, with unique match paths and slot assignments; do not invent an HTTP API or command-line export flag. Check the installed version before deciding whether native export requires the GUI.

For the packed BC7 DDS staging profile, run the helper before export:

```powershell
py -3.10 scripts/audit_manager_export.py PROJECT.tpbr --report project-audit.json
```

Open the project in Manager, inspect representative materials, and export to a new staging directory. Preserve the raw native export. With the matching PGPatcher schema, derive a checked deployment configuration:

```powershell
py -3.10 scripts/audit_manager_export.py PROJECT.tpbr --export-root EXPORT_DIR --raw-json RAW.json --patched-json DEPLOY.json --schema pbr.schema.json --report export-audit.json
```

Resolve script paths relative to this skill. The helper checks packed BC7 input/export parity, complete mip chains, color space, unique matches, and clearcoat flags. It only repairs a missing `multilayer: true` when the project explicitly requests a coat. Conflicting settings fail. It refuses to overwrite files and does not deploy or mutate NIFs. Other compression profiles and generated channel maps require appropriate validation outside this helper.

`audit_manager_export.py` supports Python 3.10+ with the standard library; schema validation additionally needs `jsonschema`. `audit_colour_roundtrip.py` needs Pillow. These helpers validate the documented packed-BC7 workflows, not arbitrary Manager projects.

## Integrate and verify

- Keep raw and corrected JSON distinct. Validate against the schema used by the intended PGPatcher version; schema success alone does not prove patcher execution or shader behavior.
- Either run a bounded PGPatcher conversion or use a verified NIF authoring route. Inspect the resulting shader type, flags, material parameters, and all raw texture slots. Do not rely on a library's classic slot labels for PBR meanings.
- If using binary NIF edits, require byte equality for every non-material block and independently parse the result. Some NIF serializers reconstruct or lose unrelated data; a successful save is insufficient.
- For direct NIF authoring or preview CTDs, read [NIF field and sampler safety](references/nif-sampler-safety.md). Validate storage types and legal values inside material blocks, use a field-level byte allowlist, and check every source/runtime winner. Parsing and BodySlide success do not validate sampler enums.
- Resolve every referenced resource through the staged mod and active MO2 winners. Check that texture-only conversions preserve the geometry/morph payloads. Rebuild affected BodySlide projects when their geometry or morph data changed, and synchronize source and runtime materials.
- Before deployment, show the concrete material changes and confidence level, back up affected winners, then apply within the user's authorized scope. Preserve global renderer settings, load order, and unrelated mods unless changing them is necessary and authorized.
- Validate final archive contents and hashes, and verify the installed winners. Keep Classic and PBR alternatives clearly selectable when a fallback is part of the request.

## Acceptance

Material spheres and Blender renders support visual review; neither reproduces Skyrim lighting, alpha sorting, animation, or physics. Test silver, black latex, amber, skin overlap, seams, and head/neck junctions in the actual game before claiming final appearance acceptance. Report remaining checks explicitly instead of treating static success as visual or runtime success.

For handing this workflow to another agent or machine, read [references/agent-handoff.md](references/agent-handoff.md). Never describe static checks as in-game acceptance.
