# TruePBR Manager integration

## Editable project

For Manager 0.7.0, the relevant `.tpbr` keys are. Replace `<PROJECT_ROOT>` placeholders with paths on the current machine before loading the example:

```json
{
  "version": "1.0",
  "name": "Example",
  "output_mod_folder": "<PROJECT_ROOT>/exports/Example",
  "texture_sets": [{
    "name": "latex",
    "match_texture": "MyOutfit\\latex",
    "match_texture_mode": "diffuse",
    "features": {"multilayer": true, "coat_normal": true},
    "params": {"specular_level": 0.04, "roughness_scale": 1,
               "coat_strength": 0.6, "coat_roughness": 1,
               "coat_specular_level": 0.04},
    "rmaos_source_mode": "packed",
    "textures": [
      {"slot": "diffuse", "path": "<PROJECT_ROOT>/latex.dds"},
      {"slot": "normal", "path": "<PROJECT_ROOT>/latex_n.dds"},
      {"slot": "rmaos", "path": "<PROJECT_ROOT>/latex_rmaos.dds"},
      {"slot": "coat_normal_roughness", "path": "<PROJECT_ROOT>/latex_cnr.dds"}
    ],
    "export_compression": {"diffuse": "bc7_srgb", "normal": "bc7_linear",
                           "rmaos": "bc7_linear", "coat_normal_roughness": "bc7_linear"},
    "channel_maps": {}
  }]
}
```

Include dimensions and alpha metadata when known. Use Manager's current project loader as the schema authority. Paths must point to the actual local inputs. Keep project assets together; a `.tpbr` file does not embed them. The case above uses ASCII project/export directories because 0.7 uses narrow `std::filesystem` strings in parts of its export code; do not assume all Unicode paths fail.

Native 0.7 command-line handling opens a project passed as the first argument. No headless export flag or public server API was found in that version. Batch project creation and validation are scriptable; native export and material preview can be done through the GUI. Re-evaluate this limitation for future versions.

## Missing multilayer field in 0.7

At commit `3e61a8a`, `JsonExporter.cpp` emits `coat_normal`, `coat_strength`, `coat_roughness`, `coat_specular_level`, `coat_diffuse`, and `coat_parallax`, but omits `multilayer: true`. PGPatcher 2.1.2 and commit `4d8973399933b9d33e7d48da90539235f6a035ef` require that switch; otherwise they revert the coat shader and clear associated flags.

Preserve the actual native JSON, then use the helper to produce a separate deployment JSON. It derives the missing switch from explicit project features, checks one-to-one material matches and schema validity, and records input/output hashes and the changed entries. It fails on conflicting `multilayer: false` instead of silently overriding it. Do not put both raw and corrected JSON in a deployed `PBRNIFPatcher` folder.

## Preview and export checks

Manager previews material primitives, not the fitted Skyrim outfit. Compare the source and exported DDS hashes if the export should be a direct copy. A re-encoded file needs decoded-image/channel comparison instead of a false claim of byte preservation. The helper intentionally requires exact copying for its prepared-BC7 profile.

GUI modal dialogs can have their own screenshot origin. If accessibility indexes land on the wrong control, refresh the actual dialog screenshot and use its screenshot ID for coordinates. Do not keep trying stale parent-window coordinates. A locked desktop requires user unlock; continue independent file work while waiting.

Run a bounded PGPatcher test if an actual conversion claim is needed, using an isolated input/output and the same target configuration. A schema audit or direct prepatched NIF derivation must be reported with its own evidence; neither proves that a full load-order PGPatcher run completed.
