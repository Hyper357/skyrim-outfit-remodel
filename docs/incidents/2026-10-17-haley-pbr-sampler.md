# Haley PBR preview CTD: float written to a sampler enum

## Observed failure

Two local crashes on 2026-10-17, Skyrim AE 1.6.1170, occurred at `d3d11.dll+0x159D40`, called from `SkyrimSE.exe+0xE4BB82`, while Modex rendered an inventory preview. One log referenced arm stocking shape `038`; the second referenced thigh hardware `EB_leg.001_Shinano_body_base.061`. The second occurred after the recent sleeve connection edits were removed. This did not support attributing both crashes to the sleeve edits.

Installed rendering context included Open Shaders 2.18, PGLite 2.2.1 and Better Body Deformation 1.0.3. Their presence in the process or stack does not establish a plugin defect.

## Confirmed asset defect and causal evidence

The custom PBR authoring script wrote float32 `1.0` at byte offset 60 of the SSE BS100 `BSLightingShaderProperty`. That location is the uint32 `textureClampMode`, not a floating-point material parameter. Independent PyNifly reads returned **1065353216**, matching the raw bytes `0x3F800000`; valid values are 0–3. The corresponding original shader used 3.

Local disassembly at the Skyrim caller shows indexed sampler-state lookup followed by the context call at vtable offset `0x50` (`PSSetSamplers`). Invalid sampler addressing is consistent with the observed crash path. The asset defect is confirmed; disappearance of the CTD after repair has **not yet been verified in game**.

## Repair and bounded evidence

- Corrected 148 shader blocks in 20 winning runtime/BodySlide source NIFs, restoring each original shader's valid addressing mode.
- Restored the approved sleeve connection source/runtime assets while applying the sampler fix to their NIFs; retained 1K PBR, metal refinement and corset/latex contrast.
- Deployed 24 unique files with backups, including the actual winning glove TRI in BodySlide Output.
- Verified types, strings, tail and bytes outside shader offsets 60–63 against the selected intended source; decoded corrected modes independently. Confirmed deployed winner hashes and unchanged profile files.
- Corrected the authoring script and marked older staged NIFs as unsafe to redeploy.

No third-party assets, full crash logs, machine paths or game binaries are included here. Local evidence consists of the two logs, before/after NIF field reads, staged validation and deployment manifests.

## Process correction

Earlier checks established non-material byte equality, successful parsing, and native BodySlide builds. They did not check legal values inside material blocks, so the bad enum survived them. The initial sleeve rollback was an isolation attempt, not a completed fix; communication overstated the sleeve hypothesis and stopped diagnosis too early.

The workflow now requires typed field definitions, semantic validation, a field-level material byte allowlist, independent readback, source/runtime winner checks and correction of the generating code. See [NIF sampler safety](../../skills/skyrim-truepbr-workflow/references/nif-sampler-safety.md).

## Acceptance status

File defect corrected and deployed. Same-item Modex preview, equipped suit/gloves, and animation acceptance remain pending. Do not label this incident runtime-resolved until those checks are reported.
