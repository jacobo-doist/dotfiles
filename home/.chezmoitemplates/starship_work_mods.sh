#!/bin/bash
# Modifies a starship config with work-specific modules.
# Reads the personal layer's rendered config from stdin, writes modified config to stdout.

config=$(cat)

# --- Work-specific custom modules ---

read -r -d '' WORK_MODULES << 'MODULES'

[custom.gh_sec_alerts]
require_repo = true
symbol = "🛡️ "
description = "Github Security Alerts"
command = "gh-alerts-status-cached"
when = "git is-doist-repo"
MODULES

# --- Inject into format string if one exists ---

# Check for a top-level format = (before any [section] header)
has_top_level_format=$(echo "$config" | awk '/^\[/{exit} /^format[[:space:]]*=/{print "yes"; exit}')

if [[ "$has_top_level_format" == "yes" ]]; then
    # Has explicit format — inject our module before $character
    config=$(echo "$config" | sed 's|\$character|$custom.gh_sec_alerts\\\n$character|')
else
    # No explicit format — use $all plus our custom module
    config="format = \"\$all\$custom.gh_sec_alerts\"
${config}"
fi

# Append work modules
printf '%s\n%s\n' "$config" "$WORK_MODULES"
