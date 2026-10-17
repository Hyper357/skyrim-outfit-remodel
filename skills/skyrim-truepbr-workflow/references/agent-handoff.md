# Agent handoff

## Same machine

Read the complete `SKILL.md` and only the relative references or scripts needed for the task. Invoke the workflow with `$skyrim-truepbr-workflow`. Resolve script paths relative to this skill folder.

## Different machine

Copy the complete `skyrim-truepbr-workflow` folder, including `SKILL.md`, `references/`, `scripts/`, and `agents/`. Prepare the local MO2 instance, TruePBR Manager, Blender, `texconv`, and Nifly tools as needed. Verify every absolute path against that machine before running commands; this package does not transfer those applications or validate their configuration.

## Evidence boundary

Report file/static checks, material previews, BodySlide builds, and in-game behavior as separate evidence. Never describe static checks as game acceptance. Claim in-game acceptance only after observing the relevant result in Skyrim.

## Material zone record in the handoff

Record the zone split before conversion, because the source evidence disappears from the files:

```text
Zones: <metal-steel | metal-gold | latex-glossy | latex-matte | stockings | leather | cloth | transparent>
Per zone: shapes <names/count>, evidence <env/matcap slot, separate albedo/normal, user statement>, albedo <path/value>,
          roughness <value>, metallic <0/1>, coat <strength/roughness>, match path <private>, NIFs <list>
Excluded: <skin/body shapes left classic>, <zones not converted and why>
```

The source environment/matcap slot is usually the only split evidence for a shared-black outfit and is replaced by RMAOS during conversion. Grouping only by `(diffuse, normal)` merges metal and latex zones; a handoff without per-shape zone evidence cannot be reviewed or reproduced.

## BodySlide handoff lessons

- A Windows BodySlide case showed a Unicode `ProjectPath` falling back to another project directory. If this behavior is reproduced in the target version, use a physical ASCII-only project path; always verify which source geometry and OSD data the build consumed. This is a version-specific recovery route, not evidence that all Unicode paths fail.
- When the user will run the final BodySlide build, hand off the independent output and First Person projects for review; do not trigger the build yourself.
