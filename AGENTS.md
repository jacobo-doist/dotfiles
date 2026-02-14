# Agents Guide

## Project

Two-layer dotfiles: personal (`jdevera/dotfiles`) + work (this repo). Both use chezmoi targeting `$HOME`. See [docs/multi-layer-setup.md](docs/multi-layer-setup.md) for architecture.

## Structure

- `.chezmoiroot` points to `home/` as chezmoi source root
- `home/` contains chezmoi source files with standard naming (`dot_`, `private_`, `executable_`, `symlink_`, etc.)
- `scripts/install.sh` bootstraps both layers

## Conventions

- **Commits**: `Area: Description` (e.g., `Chezmoi:`, `Bash:`, `Git:`, `SSH:`, `Scripts:`, `Docs:`, `Install:`)
- **Co-authorship**: include `Co-authored-by: Claude (<model-id>) <noreply@anthropic.com>`
- **Bash files**: `doist_*.sh` in `local/before/` and `local/after/` — tracked by this repo. `doist_local_*` — untracked, machine-specific
- **chezmoiignore**: deny-all (`*`) then un-ignore specific files. Each parent dir must be un-ignored for traversal
- **No `exact_`**: work layer never uses `exact_` prefix — personal layer handles directory enforcement

## Commands

Work layer commands (all available outside interactive shells):

```bash
chezmoi-work add ~/.bash.d/local/after/doist_foo.sh   # bring a file into the work repo
chezmoi-work apply                                     # apply work layer only
chezmoi-work diff                                      # preview work layer changes
chezmoi-work cd                                        # cd to work source dir
chezmoi-work edit ~/.config/git/config.work            # edit a managed file in source

cheznous apply       # apply both layers (personal first, then work)
cheznous diff        # diff both layers
cheznous update      # pull + apply both layers
cheznous-rev diff    # diff both layers (work first, then personal)
```

When adding a new file with `chezmoi-work add`, also un-ignore it in `home/.chezmoiignore` (with parent directories).

## Secrets

Work secrets come from Bitwarden via `rbw` at chezmoi apply time. Templates in `home/.chezmoitemplates/` handle fetching and validation. Every referenced Bitwarden item must have a `dotfiles_enabled=true` custom field as a safety guard.

The main template is `bw_env`, which takes a single UUID for a Bitwarden entry whose `env.`-prefixed fields define shell exports. Values starting with `bw:` reference other entries (`bw:UUID` for password, `bw:UUID:username`, `bw:UUID:fieldname`); all other values are exported verbatim. Optional `.comment` companion fields add `#` comments. Lower-level templates `bw_validate` and `bw_export` are also available for direct use.

## Extending personal layer configs

The work layer can interact with personal layer files in two ways:
- **Include**: the personal layer's config includes a work-specific file (e.g., git's `config.work`). The work layer just manages that file.
- **Modify**: chezmoi `modify_` scripts patch the personal layer's rendered output (e.g., starship). Use this when the config format doesn't support includes.
