# Material and resource decisions

## Channels and color space

| Map | Meaning | Sampling |
| --- | --- | --- |
| Base color | Albedo RGB; existing opacity in alpha when needed | sRGB RGB, linear alpha |
| Normal | DirectX tangent-space XYZ; alpha is not base roughness | Linear |
| RMAOS | R roughness, G metallic, B ambient occlusion, A specular factor | Linear |
| CNR | Coat tangent normal RGB, coat roughness A | Linear |
| Coat color (`_s`) | Coat diffuse RGB and coat strength mask A when enabled | sRGB RGB, linear alpha |

Choose compression for the channels actually used. BC7 is suitable for the RGBA maps above; BC5 cannot store a CNR roughness alpha. Preserve mip chains. Changing an incorrectly tagged BC7 linear base-color header to BC7 sRGB may be lossless to its compressed payload, but only do this when evidence establishes that its RGB bytes were authored in sRGB. Do not automatically retag unknown assets.

Set both the input and output color interpretation during encoding. For an ordinary PNG whose RGB bytes were authored as sRGB, the verified DirectXTex command is `texconv -srgb -f BC7_UNORM_SRGB -m 0 ...`. Selecting only the sRGB output format can apply an unwanted extra linear-to-sRGB conversion and turn brass pale. Data maps use linear input/output. Check decoded DDS pixels against the intended source; a correct DXGI header and hash parity through Manager can both pass with incorrect color.

Use `scripts/audit_colour_roundtrip.py SOURCE.png OUTPUT.dds --report colour-audit.json` for the BC7 sRGB PNG profile. It requires Pillow and compares encoded byte values at mip 0, including alpha. Its default RGB/alpha mean-error limits are 3/.1 on the 0–255 scale; choose tolerances for the actual texture and compression. This check detects unintended conversions, not whether the source palette is artistically correct. Keep separate mip-chain and visual checks.

`RMAOS.A = 1` with dielectric `specular_level = 0.04` is a valid combination. Specular alpha is multiplied by shader parameters; it is not an independent universal constant. Verify the installed shader before changing its convention.

Metallic silver needs a suitable linear albedo, metallic map, roughness, normals and reflections. Setting diffuse to white does not create silver. A flat white BodySlide view does not establish the behavior of TruePBR in-game.

Base roughness, coat roughness, coat strength and metallic should be authored by material region. Use source normals for believable folds and embossing, but normal slope is not a substitute for baked ambient occlusion. Label heuristic AO and replace it with a geometry bake when close review warrants it.

## Clearcoat and opacity

In Open Shaders 2.18's lighting shader, coat roughness is the NIF parameter multiplied by CNR alpha. Manager 0.7's preview reads CNR alpha directly. For that verified combination, using parameter `1` and storing the intended roughness in CNR alpha makes the two interpretations agree. Re-check other versions rather than applying this universally.

Clearcoat is not real refraction. A transparent outfit needs appropriate diffuse alpha, alpha property/blend behavior, an actual fitted underlying body, and correct shape ordering. Do not add skin-tint materials to the PBR conversion just because they are visible through clothing. Preserve opaque trim independently from the translucent shell.

## NIF slots and matching

Raw BSShaderTextureSet indices are zero based:

| Index | TruePBR meaning |
| --- | --- |
| 0 | Base color |
| 1 | Normal |
| 2 | Emissive, when enabled |
| 3 | Height, when enabled |
| 4 | Former cubemap slot; do not keep a Classic cubemap unintentionally |
| 5 | RMAOS |
| 6 | CNR or fuzz, feature dependent |
| 7 | Coat color/subsurface, feature dependent |
| 8 | Normally empty; inspect unusual assets |

These indices differ from PGPatcher JSON's one-based `slot1`…`slot8` commands. A classic Python wrapper may label index 5 `EnvMapMask`; inspect raw strings before concluding that RMAOS is absent.

TruePBR shader selection also needs the expected flags and parameters; texture names alone do not enable it. In the verified PGPatcher implementation, the coat uses `multilayer: true`, the multilayer shader type, and associated flags. Use the target patcher's implementation as the authority for binary layout and flags.

Give materials private match paths when an original diffuse is shared across meshes with different normals or UV layouts. A texture matcher does not distinguish two shapes that share the same matching string. Preserve separate hardware materials in such cases; do not emit a broad alias that converts unrelated original outfits. If the mod ships prepatched NIFs with private paths, state that its configuration targets those NIFs rather than promising automatic conversion of the original mod.

## Verified source anchors

- [TruePBR Manager](https://github.com/jiayev/TruePBR-Manager), installed case: v0.7.0, commit `3e61a8a939d59bc130d8b02d9ebfac69551c2f01`; inspect `src/core/Project.cpp`, `JsonExporter.cpp`, `TextureExporter.cpp`, and preview shaders.
- [PGPatcher mod-author guidance](https://github.com/hakasapl/PGPatcher/wiki/Mod-Authors); inspect the target version's `schema/pbr.schema.json` and `PGLib/src/patchers/PatcherMeshShaderTruePBR.cpp`.
- [Open Shaders](https://github.com/alandtse/open-shaders); local case: 2.18.0. Check installed `Shaders/Lighting.hlsl` and the boot-feature implementation, not just a settings label.
- [DirectXTex texconv](https://github.com/microsoft/DirectXTex/wiki/Texconv), input/output sRGB switches and BC7 encoding. Explicit input color interpretation was verified by a PNG-to-DDS decoded-pixel comparison in this case.

The source pins record a demonstrated compatibility case, not a recommendation to downgrade newer tools.
