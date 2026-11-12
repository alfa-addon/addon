# Repository Guidelines

## Project Structure & Module Organization

`plugin.video.alfa/` contains the Kodi add-on. Put website integrations in `channels/` (usually paired `.py` and `.json` files), hosting-service resolvers in `servers/`, shared application logic in `core/`, user-facing features in `modules/`, and Kodi integration in `platformcode/`. Assets, translations, skins, and settings live in `resources/`; add-on metadata and dependencies are declared in `addon.xml`.

`lib/` contains bundled libraries. Prefer inward dependencies: Alfa may import libraries, but libraries should remain self-contained rather than importing Alfa's `core` or `platformcode`. Keep application helpers outside vendored packages such as `lib/pywasm/`.

`mediaserver/` provides the standalone overlay. `scripts/` and `.github/workflows/release.yml` handle packaging and releases.

## Development & Packaging Commands

- Run the add-on inside Kodi with its declared dependencies installed; ordinary Python cannot supply Kodi's `xbmc` APIs.
- `bash scripts/release.sh -h` lists release options.
- `bash scripts/release.sh -nv` previews the version without writing release files.
- `bash scripts/release.sh -z` creates an installable ZIP. Use Bash and install the script's required tools; CI installs `xmlstarlet`, `jq`, and `python -m pip install -r requirements-ci.txt`.

Release flags can change versions, generate assets, and commit changes. Reserve those operations for release work. For standalone setup, follow `mediaserver/README.md`.

## Coding Style & Compatibility

Follow the README's PEP 8 guidance: four-space indentation and English identifiers for new classes, functions, and variables. Use `snake_case` for functions and modules, and `PascalCase` for classes. Match surrounding line endings and avoid unrelated reformatting; no repository-wide formatter is configured.

Preserve Python 3.6 syntax and existing Python 2 compatibility in shared code. Reuse existing helpers instead of introducing parallel implementations. Keep temporary files in an add-on-specific directory and preserve explicitly configured user paths.

## Commits & Pull Requests

History mixes Spanish descriptive messages with terse legacy summaries; prefer concise, descriptive messages stating the actual change. Keep commits focused. PR descriptions should explain the problem, resulting behavior, affected channels or servers, and manual verification in Kodi. Link related issues or PRs and include screenshots when changing visible UI. Do not commit credentials, local settings, caches, or generated release artifacts.
