# NIF material field safety and preview crash diagnosis

## Before writing a binary material

Prefer named fields in a format-aware authoring API when that API preserves the required mesh data. If byte edits are necessary, establish the exact NIF version, user version, Bethesda stream version and block layout first. Record each field's offset, storage type, allowed values and intended change. Reject unsupported layouts rather than reusing offsets from another format.

For the verified Skyrim SSE layout (`20.2.0.7`, user version `12`, BS stream `100`), the following offsets are relative to the beginning of a `BSLightingShaderProperty` block:

| Offset | Field | Storage | Validation |
| --- | --- | --- | --- |
| 60 | `textureClampMode` | little-endian uint32 | 0 through 3; normally preserve source value |
| 64 | alpha | little-endian float32 | finite, 0 through 1; preserve intended transparency |

Value 3 is wrap on both axes. Preserve the source's valid mode rather than guessing an axis mapping from a wrapper's labels. These offsets are **not** a general layout for other NIF versions or shader block types. Verify against the target format schema and independent parser.

Writing `struct.pack_into('<f', block, 60, 1.0)` stores `0x3F800000`, which parses successfully as uint32 **1065353216**. It is an invalid addressing mode. A parser accepting the file does not establish field validity. Do not replace it with uint32 1 automatically either: restore the corresponding source's valid mode so UV wrapping is preserved.

## Required checks for the chosen authoring route

1. Check all changed shader fields semantically, including enum ranges, finite floats, transparency, shader type/flag combinations and raw texture slots. A JSON schema only validates the configuration, not the generated NIF.
2. Independently parse the written NIF and compare the decoded values with the intended values. For byte edits, also verify the raw storage type and offset. Check **every** affected shader, including shared blocks, across source and runtime assets.
3. Use a field-level byte allowlist inside material blocks. Unchanged non-material blocks alone cannot catch corruption of an unrelated material field. Preserve all bytes outside the intended fields; separately account for authorized geometry changes.
4. Audit both staged and actual winning files. Synchronize BodySlide ShapeData and runtime NIFs; a subsequent build must not reintroduce the defect. Fix the generator and identify older staged artifacts that are no longer safe to deploy.
5. Report separately: parsing, semantic checks, byte preservation, BodySlide building, renderer loading, item preview, equipped appearance and animation. None substitutes for the next.

## When a PBR item preview crashes

- Preserve the log and resolve the item/shape to its actual winning NIF and materials. Compare successive logs: a different shape at the same rendering call can indicate a shared material-writing or rendering defect.
- Inspect sampler addressing, shader flags, slot closure and version-specific material layout alongside skin partitions and morphs. An implicated skinned shape is not proof that geometry or a sleeve seam caused the crash.
- A rollback can provide a controlled baseline, but it does not establish a cause or finish the repair. Continue inspecting the original and generated data; correct the identified defect and preserve approved changes where supported.
- Do not disable global renderers, deformation plugins or change drivers solely because their names appear in a stack. Establish evidence for a targeted change.
- After repair, reproduce the original preview and equip the affected items in game. Until then, state that the file defect is corrected and runtime resolution is pending.

Case evidence: [Haley invalid sampler incident](../../../docs/incidents/2026-10-17-haley-pbr-sampler.md).
