# Working on this repository

This repository distributes a reusable agent skill, not a mod asset package.

- Read `skills/skyrim-outfit-remodel/SKILL.md`, then only the references needed for the current phase.
- Preserve the separation between indexed edits and retopology, and between source projects and game outputs.
- Keep script coverage honest: numeric, reference and build checks do not imply pose or game acceptance. Warnings require review.
- Scripts must not rewrite their source NIF/blend/OSP, change live MO2 configuration, deploy mods, or delete historical assets implicitly.
- Record unknown version behavior using primary documentation and a minimal experiment. Community posts are leads, not universal rules.
- Use UTF-8. Run `python -m unittest discover -s tests -v` after functional changes. Validate local Markdown links and skill metadata.
- Add tests for meaningful failure conditions. Use synthetic fixtures; never commit third-party geometry, textures, tool binaries, credentials, personal paths or full crash logs.
- Real-resource smoke evidence belongs in ignored `.local-validation/`; publish only sanitized aggregate results in `docs/VALIDATION.md`.
- Do not add mandatory approvals beyond the user's actual authorization. Do not claim an unperformed GUI, game or upload test passed.
