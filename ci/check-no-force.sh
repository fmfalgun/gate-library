#!/usr/bin/env bash
# Fails when a script uses a force-based command (global no-force rule,
# and the repo hygiene baseline). Scans shell scripts, hooks, Makefiles, Dockerfiles and
# everything else under ci/ and .github/, except markdown and Go sources
# (documentation may name the forbidden commands).
# Usage: ci/check-no-force.sh [FILE...]   (no arguments: scan the whole repo)
# Output: "file:line: reason: text" per finding. Exit 1 on any finding.
#
# Full-line comments are skipped. File tests such as [[ -f x ]] are not
# flagged: each pattern needs a command word (git, rm, curl, ...) before the
# flag. The pattern list below is written with bracket tricks (for example
# a letter in its own brackets) so that this file does not match itself.

set -euo pipefail

# Each entry is "reason@@extended-regex". Reasons avoid the forbidden text.
readonly FORBIDDEN=(
  "long force flag@@--forc[e]"
  "hard reset flag@@--har[d]([^a-zA-Z-]|$)"
  "hook bypass flag@@--no-verif[y]"
  "recursive or forced remove@@(^|[^[:alnum:]_-])rm[[:space:]]+-[a-zA-Z]*[rf]"
  "combined recursive-force flag@@[[:space:]]-[a-zA-Z]*(rf|fr)[a-zA-Z]*([[:space:]]|$)"
  "short force flag on git@@(^|[^[:alnum:]_-])git[[:space:]]([^|;&#]*[[:space:]])?-[a-zA-Z]*f[a-zA-Z]*([[:space:]]|$)"
  "branch delete without merge check@@git[[:space:]]+branch[[:space:]]+-[a-zA-Z]*D"
  "history rewrite@@git[[:space:]]+(filter-branch|filter-repo|rebase)|git[[:space:]]+commit[[:space:]].*--amen[d]"
  "hard kill@@(^|[^[:alnum:]_-])(p?kill|killall)[[:space:]]+(-9|-KILL|-SIGKILL|-s[[:space:]]+(9|KILL))"
  "forced symlink@@(^|[^[:alnum:]_-])ln[[:space:]]+-[a-zA-Z]*f"
  "forced copy or move@@(^|[^[:alnum:]_-])(cp|mv)[[:space:]]+-[a-zA-Z]*f"
  "short fail flag on curl@@(^|[^[:alnum:]_-])curl[[:space:]]([^|;&#]*[[:space:]])?-[a-zA-Z]*f[a-zA-Z]*([[:space:]]|$)"
  "forced docker remove or prune@@docker[[:space:]]+([a-z]+[[:space:]]+)?(rm|rmi|prune)[[:space:]]([^|;&#]*[[:space:]])?-[a-zA-Z]*f"
  "sudo@@(^|[[:space:];&|(])sudo([[:space:]]|$)"
)

# project_root prints the repository root, found relative to this script.
project_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

# list_targets prints the files to scan, one per line, when none were given.
list_targets() {
  local root
  root="$(project_root)"
  find "$root" \( -name .git -o -name .tools -o -name .cache -o -name .venv -o -name node_modules -o -name vendor \) -prune -o \
    -type f \( -name '*.sh' -o -name '*.fish' -o -name '*.mk' -o -name 'Makefile' -o -name 'Dockerfile*' \
    -o -path "$root/ci/*" -o -path "$root/.github/*" \) \
    ! -name '*.md' ! -name '*.go' -print | sort
}

# scan_line checks one line ($3, from line number $2 of file $1) against every
# pattern, prints a finding for each match and returns 0 if any matched.
scan_line() {
  local file="$1" number="$2" line="$3" entry reason regex hit=1
  for entry in "${FORBIDDEN[@]}"; do
    reason="${entry%%@@*}"
    regex="${entry#*@@}"
    if [[ "$line" =~ $regex ]]; then
      echo "$file:$number: $reason: ${line#"${line%%[![:space:]]*}"}"
      hit=0
    fi
  done
  return "$hit"
}

# scan_file scans every non-comment line of file $1 and returns 0 if it found
# anything. An unreadable file stops the script (set -e) rather than passing.
scan_file() {
  local file="$1" line number=0 found=1
  # shellcheck disable=SC2094  # scan_line only prints the file name, it never writes the file
  while IFS= read -r line || [[ -n "$line" ]]; do
    number=$((number + 1))
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    if scan_line "$file" "$number" "$line"; then found=0; fi
  done < "$file"
  return "$found"
}

# main scans the given files (or the repo) and exits 1 if any had findings.
main() {
  local file failed=0
  local -a targets=()
  if (( $# > 0 )); then
    targets=("$@")
  else
    mapfile -t targets < <(list_targets)
  fi
  for file in "${targets[@]}"; do
    [[ "$file" == *.md || "$file" == *.go ]] && continue
    if scan_file "$file"; then failed=1; fi
  done
  if (( failed )); then
    echo "check-no-force: force-based commands found" >&2
  fi
  return "$failed"
}

main "$@"
