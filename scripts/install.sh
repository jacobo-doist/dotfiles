#!/usr/bin/env bash
# Work dotfiles installer
# One command: curl -fsLS https://raw.githubusercontent.com/jacobo-doist/dotfiles/main/scripts/install.sh | bash
#
# Flow:
#   1. Create work marker BEFORE personal init (so personal sees is_work=true from the start)
#   2. Install chezmoi if needed
#   3. Init + apply personal dotfiles (reads marker → is_work=true)
#   4. Init + apply work dotfiles

set -euo pipefail

WORK_CONFIG_DIR="${HOME}/.config/chezmoi-work"
WORK_MARKER="${WORK_CONFIG_DIR}/.is-work"
WORK_SOURCE_DIR="${HOME}/.local/share/chezmoi-work"
WORK_CONFIG_FILE="${WORK_CONFIG_DIR}/chezmoi.toml"

PERSONAL_REPO="jdevera/dotfiles"
WORK_REPO="jacobo-doist/dotfiles"

# --- Helpers ---

info() { printf '\033[1;34m[info]\033[0m %s\n' "$*"; }
error() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; }
die() { error "$@"; exit 1; }

# --- Step 1: Create work marker ---

info "Creating work marker at ${WORK_MARKER}..."
mkdir -p "${WORK_CONFIG_DIR}"
touch "${WORK_MARKER}"

# --- Step 2: Install chezmoi ---

if command -v chezmoi >/dev/null 2>&1; then
    info "chezmoi already installed: $(command -v chezmoi)"
else
    info "Installing chezmoi..."
    sh -c "$(curl -fsLS get.chezmoi.io)" || die "Failed to install chezmoi"
fi

# Ensure chezmoi is on PATH (get.chezmoi.io installs to ~/bin by default)
if ! command -v chezmoi >/dev/null 2>&1; then
    export PATH="${HOME}/bin:${PATH}"
    command -v chezmoi >/dev/null 2>&1 || die "chezmoi not found on PATH after install"
fi

# --- Step 3: Init + apply personal dotfiles ---

info "Initializing personal dotfiles from ${PERSONAL_REPO}..."
chezmoi init --apply "${PERSONAL_REPO}" || die "Failed to init/apply personal dotfiles"
info "Personal dotfiles applied."

# --- Step 4: Init + apply work dotfiles ---

info "Initializing work dotfiles from ${WORK_REPO}..."
chezmoi init --apply \
    --source "${WORK_SOURCE_DIR}" \
    --config "${WORK_CONFIG_FILE}" \
    "${WORK_REPO}" || die "Failed to init/apply work dotfiles"
info "Work dotfiles applied."

# --- Done ---

info "Work dotfiles installation complete!"
info "Use 'chezmoi-work' to manage work dotfiles."
info "Use 'dotfiles-update' to update both layers."
