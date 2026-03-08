#!/usr/bin/env python3
"""Modify a starship config with work-specific modules.

Reads the personal layer's rendered config from stdin, writes the
modified config to stdout. Idempotent — safe to run multiple times.
"""

import re
import sys

MARKER_BEGIN = "# BEGIN work-layer"
MARKER_END = "# END work-layer"

FORMAT_INJECTION = "${custom.gh_sec_alerts}\\\n"

WORK_MODULES = """\
{begin} modules
[custom.gh_sec_alerts]
require_repo = true
symbol = "🛡️ "
description = "Github Security Alerts"
command = "gh-alerts-status-cached"
when = "git is-doist-repo"
{end} modules
""".format(begin=MARKER_BEGIN, end=MARKER_END)


def clean_previous_injections(config: str) -> str:
    """Remove any previous work-layer injections."""
    # Remove marked sections (including the marker lines)
    config = re.sub(
        rf"^{re.escape(MARKER_BEGIN)}.*?^{re.escape(MARKER_END)}.*\n",
        "",
        config,
        flags=re.MULTILINE | re.DOTALL,
    )

    # Remove old injections from before markers were used
    # Handles both $custom.gh_sec_alerts and ${custom.gh_sec_alerts}
    config = re.sub(r"^.*\$\{?custom\.gh_sec_alerts\}?.*\n", "", config, flags=re.MULTILINE)
    config = re.sub(r"^\[custom\.gh_sec_alerts\]\n(?:(?!\[)[^\n]*\n)*", "", config, flags=re.MULTILINE)

    return config


def has_top_level_format(config: str) -> bool:
    """Check if config has a top-level format = line (before any [section])."""
    for line in config.splitlines():
        if line.startswith("["):
            return False
        if re.match(r"^format\s*=", line):
            return True
    return False


def inject_format(config: str) -> str:
    """Inject the work module into the format string.

    Places the module on the first line (before $line_break) so it appears
    alongside other modules, not on the prompt input line.
    """
    if has_top_level_format(config):
        # Insert before $line_break to keep it on line 1
        if "$line_break" in config:
            config = config.replace("$line_break", FORMAT_INJECTION + "$line_break", 1)
        else:
            # Single-line prompt — insert before $character
            config = config.replace("$character", FORMAT_INJECTION + "$character", 1)
    else:
        # No explicit format — build one that places our module on line 1.
        # By listing $line_break and $character explicitly, they're excluded
        # from $all, letting us control their position.
        config = 'format = "$all${custom.gh_sec_alerts}$line_break$character"\n' + config

    return config


def main() -> None:
    config = sys.stdin.read()
    config = clean_previous_injections(config)
    config = inject_format(config)

    # Append work modules
    if not config.endswith("\n"):
        config += "\n"
    config += WORK_MODULES

    sys.stdout.write(config)


if __name__ == "__main__":
    main()
