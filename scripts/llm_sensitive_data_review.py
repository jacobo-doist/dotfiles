#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["anthropic"]
# ///
"""LLM-based sensitive data review using Claude Haiku.

Usage:
  # Review specific files:
  uv run --script scripts/llm_sensitive_data_review.py file1.sh file2.tmpl

  # As a pre-push hook (reads push refs from stdin):
  pre-commit run llm-sensitive-data-review --hook-stage pre-push

Fails if sensitive data is detected, ANTHROPIC_API_KEY is not set, or
the API is unreachable.

Bypass (pre-push): SKIP=llm-sensitive-data-review git push
"""

import os
import pathlib
import subprocess
import sys

BYPASS_CMD = "SKIP=llm-sensitive-data-review git push"

SYSTEM_PROMPT = """\
You are a security reviewer for a dotfiles repository that is about to become \
public. Your job is to review git diffs and flag any sensitive data that should \
NOT be committed to a public repo.

Flag the following categories:

1. **Bitwarden UUIDs** — UUIDs (8-4-4-4-12 hex format) that appear to reference \
actual Bitwarden vault entries rather than being placeholders/examples.
2. **Internal service names** — Real hostnames, internal domain names, or service \
identifiers that reveal internal infrastructure (e.g., *.internal.company.com, \
specific service names in URLs).
3. **Workspace/team IDs** — Twist workspace IDs or other platform-specific \
identifiers tied to real accounts.
4. **Credentials and tokens** — API keys, passwords, bearer tokens, SSH private keys, \
or any authentication material.
5. **Internal URLs** — URLs pointing to internal tools, dashboards, wikis, or services \
that are not publicly accessible.
6. **Email addresses and usernames** — Real employee email addresses or internal usernames \
that could be used for social engineering.
7. **IP addresses** — Internal or private IP addresses.

Things that are NOT sensitive (do NOT flag these):
- Public GitHub usernames and public repository URLs
- Bitwarden UUIDs — they are opaque identifiers, not secrets
- chezmoi template invocations like {{ rbw "item-name" }}, {{ template "bw_env" "UUID" }}, \
or {{ (rbw "item-name").data.fields | ... }} — these fetch secrets at apply time
- Template helper definitions in .chezmoitemplates/ — references to "bw:", "rbw", \
"bw_validate", "bw_export" within template logic
- Names of CLI tools and programs (rbw, bw, chezmoi, gh, etc.)
- Configuration keys, option names, and shell aliases
- Public domain names (github.com, doist.com, etc.)

Context about this repo:
- It uses chezmoi for dotfile management with Bitwarden (via rbw) for secrets
- This is a PUBLIC dotfiles repo — the owner's GitHub username and public URLs are fine
- What is NOT safe: hardcoded secret values, internal hostnames/URLs, credentials, \
private IP addresses, real employee emails used in non-public contexts

Respond in EXACTLY one of these two formats:

If the diff is safe:
SAFE

If there are concerns:
CONCERNS
- [file:line_context] Description of the concern
- [file:line_context] Description of another concern
...
"""

MODEL = "claude-haiku-4-5-20251001"
MAX_DIFF_CHARS = 100_000  # Haiku context is large but let's be reasonable


def get_diff_from_push_refs() -> str:
    """Read push refs from stdin and compute the diff."""
    push_info = sys.stdin.read().strip()
    if not push_info:
        return ""

    # stdin format: <local_ref> <local_sha> <remote_ref> <remote_sha>
    # There can be multiple lines (one per ref being pushed)
    diffs = []
    zero_sha = "0" * 40

    for line in push_info.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue

        local_sha = parts[1]
        remote_sha = parts[3]

        if local_sha == zero_sha:
            # Deleting a branch — nothing to review
            continue

        if remote_sha == zero_sha:
            # New branch — diff all commits against the default remote branch
            try:
                result = subprocess.run(
                    ["git", "diff", f"origin/HEAD...{local_sha}"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                diffs.append(result.stdout)
            except subprocess.CalledProcessError:
                # Fallback: show all content in the new branch
                result = subprocess.run(
                    ["git", "diff", "--cached", local_sha],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                diffs.append(result.stdout)
        else:
            # Normal push — diff between remote and local
            result = subprocess.run(
                ["git", "diff", f"{remote_sha}..{local_sha}"],
                capture_output=True,
                text=True,
                check=False,
            )
            diffs.append(result.stdout)

    return "\n".join(diffs)


def get_content_from_files(paths: list[str]) -> str:
    """Read file contents and format them for review."""
    parts = []
    for path in paths:
        content = pathlib.Path(path).read_text()
        parts.append(f"=== {path} ===\n{content}")
    return "\n\n".join(parts)


def review(content: str, *, is_diff: bool) -> tuple[bool, str]:
    """Send content to Claude Haiku for review.

    Returns (is_safe, message).
    """
    import anthropic

    client = anthropic.Anthropic()

    if len(content) > MAX_DIFF_CHARS:
        content = content[:MAX_DIFF_CHARS] + "\n\n[... truncated ...]"

    if is_diff:
        user_msg = (
            f"Review this git diff for sensitive data:\n\n```diff\n{content}\n```"
        )
    else:
        user_msg = f"Review these file contents for sensitive data:\n\n{content}"

    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    response_text = message.content[0].text.strip()

    if response_text.startswith("SAFE"):
        return True, ""

    return False, response_text


def main() -> int:
    files = sys.argv[1:]

    if files:
        content = get_content_from_files(files)
        is_diff = False
    else:
        content = get_diff_from_push_refs()
        is_diff = True

    if not content.strip():
        return 0

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("=" * 60, file=sys.stderr)
        print("ERROR: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        print("The LLM sensitive data review cannot run.", file=sys.stderr)
        print(file=sys.stderr)
        print(f"To bypass: {BYPASS_CMD}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return 1

    try:
        is_safe, message = review(content, is_diff=is_diff)
    except Exception as exc:
        print("=" * 60, file=sys.stderr)
        print(f"ERROR: LLM review failed: {exc}", file=sys.stderr)
        print(file=sys.stderr)
        print(f"To bypass: {BYPASS_CMD}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return 1

    if is_safe:
        print("LLM review: no sensitive data detected.", file=sys.stderr)
        return 0

    print("=" * 60, file=sys.stderr)
    print("SENSITIVE DATA DETECTED by LLM review:", file=sys.stderr)
    print(file=sys.stderr)
    print(message, file=sys.stderr)
    print(file=sys.stderr)
    print(f"To bypass: {BYPASS_CMD}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
