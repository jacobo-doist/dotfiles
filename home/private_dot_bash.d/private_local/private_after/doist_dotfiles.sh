#!/usr/bin/env bash
# Dotfiles management helpers
# Managed by chezmoi-work — do not edit manually

# shellcheck disable=SC2120
dotfiles-update() {
    cheznous update "$@"
}
