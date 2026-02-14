# Multi-Layer Dotfiles Setup

## Overview

This repo implements a **two-layer dotfiles architecture**: a personal layer
(`jdevera/dotfiles`) managed by the default chezmoi instance, and this work
layer (`jacobo-doist/dotfiles`) managed by a second chezmoi instance with
separate source and config paths.

Both layers target the same `$HOME` directory. The personal layer is applied
first, then the work layer on top. The personal layer remains fully standalone
and functional without the work layer present.

## How It Works

Each layer has its own chezmoi instance:

| | Personal | Work |
|---|---|---|
| **Source** | `~/.local/share/chezmoi` | `~/.local/share/chezmoi-work` |
| **Config** | `~/.config/chezmoi/chezmoi.toml` | `~/.config/chezmoi-work/chezmoi.toml` |
| **Repo** | `jdevera/dotfiles` | `jacobo-doist/dotfiles` |
| **Apply order** | First | Second |

### CLI Tools

All tools live in `~/.local/bin/` as scripts, so they work in any context
(interactive shells, editor terminals, CI, Claude Code sessions).

**`chezmoi-work`** — wrapper that invokes chezmoi with the work layer config:

```bash
chezmoi-work diff      # diff work layer only
chezmoi-work apply     # apply work layer only
```

**`cheznous`** — runs a chezmoi command across both layers sequentially
(personal first, then work):

```bash
cheznous diff          # diff both layers
cheznous apply         # apply both layers in order
cheznous update        # pull + apply both layers
```

**`cheznous-rev`** — symlink to `cheznous` that reverses the order (work
first, then personal). It detects the invocation name via `$0`, so aliasing
the symlink preserves the reverse behavior:

```bash
cheznous-rev status    # status work first, then personal
alias foo=cheznous-rev # foo also runs in reverse
```

Reversal can also be triggered via environment variable:

```bash
CHEZNOUS_REVERSE=1 cheznous diff
```

**`dotfiles-update`** — shell function that wraps `cheznous update` for
convenience in interactive shells.

## Work Detection

The personal layer detects that it's on a work machine through a **marker
file** at `~/.config/chezmoi-work/.is-work`. If the marker exists, `is_work`
is set to `true` unconditionally. If absent, it falls back to matching against
a list of known work hostnames.

The install script creates this marker **before** the personal layer's first
`chezmoi init`, so templates and `run_once` scripts see the correct
`is_work=true` context from the very first apply.

## Avoiding Conflicts

Since both layers target `$HOME`, the work layer must not interfere with
personal files. The work `.chezmoiignore` uses a **deny-all, allow-specific**
strategy:

```
# Ignore everything
*

# Un-ignore directory paths to allow traversal, then specific files/patterns
!.bash.d/
!.bash.d/local/
!.bash.d/local/before/
!.bash.d/local/before/doist_*
!.bash.d/local/after/
!.bash.d/local/after/doist_*

# Re-ignore machine-specific work files (not tracked by either repo)
.bash.d/local/before/doist_local_*
.bash.d/local/after/doist_local_*

!.config/
!.config/git/
!.config/git/config.work
# ... etc
```

Each parent directory in the path must be explicitly un-ignored — ignoring `*`
blocks all directory traversal, so without those lines chezmoi would never
see the files inside. This is the same behavior as `.gitignore`.

The deny-all approach is maintenance-free: new files added to the personal
repo don't require updates to the work ignore list.

**Important:** The work layer deliberately does **not** use the `exact_`
prefix on any directories. The personal layer uses `exact_` on `.bash.d/` to
keep it clean — the work layer only needs to add files, not enforce directory
contents. Using `exact_` in the work layer would cause it to delete any
`doist_*.sh` files that exist on disk but haven't been added to the work
source yet, which is a problem during transition.

## Extension Points

The layers avoid file conflicts entirely through include-based splitting. Each
config format's native include mechanism lets both layers contribute without
touching each other's files.

### Bash — `~/.bash.d/local/`

The personal layer's `bootstrap.sh` sources files in this order:
1. `~/.bash.d/local/before/*` — machine-specific, before main config
2. `~/.bash.d/*` — main config files (personal layer)
3. `~/.bash.d/local/after/*` — machine-specific, after main config

Personal's `.chezmoiignore` has `.bash.d/local/*`, so files placed here by
the work layer survive personal re-apply.

The work layer uses a **`doist_` prefix convention** for files in both
`local/before/` and `local/after/`:

| Pattern | Tracked by | Purpose |
|---------|-----------|---------|
| `doist_*.sh` | This repo | Work config, managed by chezmoi-work |
| `doist_local_*.sh` | Nothing | Machine-specific work config, untracked |

This keeps work config cleanly separated from personal config. To bring an
existing file into the work repo: `chezmoi-work add ~/.bash.d/local/after/doist_env.sh`.

### Git — `~/.config/git/config.work`

Personal's git config includes files in this order:
1. `config.user` — identity (name, email, driven by `is_work` flag)
2. `config.work` — work-specific settings (managed by this repo)
3. `config.local` — untracked machine-specific overrides (always last)

Git silently skips missing includes, so `config.work` is a no-op on
personal-only machines.

### SSH — `~/.ssh/config.d/`

Personal manages `~/.ssh/config` with `Include ~/.ssh/config.d/*` at the top.
The work layer places `~/.ssh/config.d/work` with work-specific host entries.
A `~/.ssh/config.d/local` file is seeded empty (via chezmoi's `create_`
prefix) for untracked machine-specific SSH config.

## Secrets

**Identity** (email, name, GitHub user) stays in **1Password**. The personal
layer's config template selects the right 1Password entry based on the
`is_work` flag.

**Work secrets** (SSH keys, API tokens, etc.) use **Bitwarden** via chezmoi's
native `bw` CLI support, configured with auto-unlock in the work layer's
chezmoi config.

## Inspiration

This approach implements "Option 1" from the chezmoi FAQ on [multiple source
states][faq]: run chezmoi multiple times with different `--config` and
`--source` flags, wrapped in a shell function.

The practical patterns (wrapper functions, sequential apply, separate
source/config paths) are similar to those described in [GitHub Discussion
#2574][discussion], which applies the same two-instance technique to a
team-base/individual-user split rather than a personal/work split.

[faq]: https://www.chezmoi.io/user-guide/frequently-asked-questions/design/#can-chezmoi-support-multiple-sources-or-multiple-source-states
[discussion]: https://github.com/twpayne/chezmoi/discussions/2574
