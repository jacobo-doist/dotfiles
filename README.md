# 💼 Jacobo's Work Dotfiles

> The work layer — because one set of dotfiles wasn't enough trouble

This is the **work half** of a two-layer dotfiles setup. My
[personal dotfiles](https://github.com/jdevera/dotfiles) handle the
foundation: shell, editor, prompt, tools. This repo layers work-specific
config on top — extra git settings, SSH hosts, shell aliases — without
touching or duplicating anything from the personal layer.

Both layers are managed with [chezmoi](https://www.chezmoi.io/), each running
as its own instance with separate source and config paths, both targeting
`$HOME`. Personal is applied first, work second. They don't conflict because
each layer uses native include mechanisms (git includes, SSH `Include`,
bash.d sourcing) to extend rather than override.

Curious how this actually works? See
[docs/multi-layer-setup.md](docs/multi-layer-setup.md) for the full
architecture, or keep reading for the short version.

## ⚡ Installation

For me (hi, work me!):

```bash
curl -fsLS https://raw.githubusercontent.com/jacobo-doist/dotfiles/main/scripts/install.sh | bash
```

This creates a work marker file, installs chezmoi, applies personal dotfiles
(which detect the marker and adjust identity accordingly), then applies this
work layer on top.

## ⚠️ For Everyone Else

This is my work config. It extends my personal dotfiles, which are already
[not recommended for direct use](https://github.com/jdevera/dotfiles#%EF%B8%8F-for-everyone-else).
But if you're looking to set up a similar two-layer system with chezmoi,
the [architecture docs](docs/multi-layer-setup.md) might be useful.

## 🛠️ Daily Use

| Command | What it does |
|---------|--------------|
| `cheznous diff` | Diff both layers (personal first, then work) |
| `cheznous apply` | Apply both layers in order |
| `cheznous-rev status` | Status both layers (work first, then personal) |
| `chezmoi-work` | Manage work dotfiles directly (e.g. `chezmoi-work edit`) |
All commands are scripts in `~/.local/bin/`, available outside interactive
shells (e.g. in editor terminals, CI, Claude Code sessions). `cheznous-rev`
is a symlink to `cheznous` — it detects the invocation name to reverse the
layer order.

## 🐚 Shell

The personal layer loads bash config from `.bash.d/` in this order:
1. `.bash.d/local/before/*` — machine-specific, before main config
2. `.bash.d/*` — main config files (personal layer)
3. `.bash.d/local/after/*` — machine-specific overrides

This repo places work shell config in `local/before/` and `local/after/`
using the `doist_` prefix convention:

| Pattern | Tracked by | Example |
|---------|-----------|---------|
| `doist_*.sh` | This repo | `doist_env.sh`, `doist_aliases.sh` |
| `doist_local_*.sh` | Nothing (machine-specific) | `doist_local_vpn.sh` |

This keeps work config cleanly separated from personal config and from
untracked machine-specific files, all within the same directory structure.

## 🔐 Secrets

Work secrets are stored in **Bitwarden** and fetched at `chezmoi apply`
time using [rbw](https://github.com/doy/rbw) (an unofficial Bitwarden
CLI with a background agent — no manual unlock per command).

Shell environment secrets are defined via Bitwarden entries whose custom
fields use the `env.` prefix convention. A single "index" entry maps
variable names to other Bitwarden entries, so template files contain only
one UUID each — no variable names or service details in the repo.

### How it works

Each `env.`-prefixed field in a Bitwarden entry defines a shell export:

| Field value format | Meaning |
|--------------------|---------|
| `bw:<UUID>` | Fetch the password from another entry |
| `bw:<UUID>:username` | Fetch the username |
| `bw:<UUID>:<fieldname>` | Fetch a custom field |
| anything else | Export the value verbatim |

Optional `env.VARNAME.comment` companion fields add `# comment` lines.
An entry-level `dotfiles_comment` field adds a header comment.

### Safety guard: `dotfiles_enabled`

Every Bitwarden item referenced by dotfiles **must** have a custom field:

| Field name | Type | Value |
|-----------|------|-------|
| `dotfiles_enabled` | Boolean | `true` |

If this field is missing or set to `false`, `chezmoi apply` will **fail**
with an error naming the item UUID. This prevents accidentally writing
secrets from items not explicitly opted in.

### Adding a new secret

1. Store the secret in Bitwarden with `dotfiles_enabled` set to `true`
2. Add an `env.VARNAME` field to the index entry pointing to it
3. Run `chezmoi-work apply` (or `cheznous apply`)
