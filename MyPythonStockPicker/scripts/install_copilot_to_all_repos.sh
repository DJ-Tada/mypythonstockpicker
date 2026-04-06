#!/usr/bin/env zsh
# Copy a local copilot-instruction.md into multiple repositories under a given root path.
# Usage: ./install_copilot_to_all_repos.sh /path/to/repos [--yes]

set -euo pipefail
COPILOT_SRC="$HOME/Downloads/copilot-instruction.md"
ROOT_DIR="${1:-$HOME/Projects}"
source "$(cd "$(dirname "$0")/.." && pwd)/scripts/common_env.sh" || true
AUTO_YES=0
if [[ "${2:-}" == "--yes" || "${2:-}" == "-y" || "${1:-}" == "--yes" || "$AUTO_APPROVE" == "1" ]]; then
  AUTO_YES=1
fi

if [[ ! -f "$COPILOT_SRC" ]]; then
  echo "No $COPILOT_SRC found"
  exit 1
fi

echo "Scanning for git repositories under $ROOT_DIR"

if [[ $AUTO_YES -eq 0 ]]; then
  echo
  read -q "PROCEED?This will copy $COPILOT_SRC into many repositories under $ROOT_DIR. Proceed? (y/N): "
  echo
  if [[ "$PROCEED" != [Yy] ]]; then
    echo "Aborted by user."
    exit 0
  fi
else
  echo "AUTO_APPROVE set: proceeding without prompting"
fi

total=0
copied=0
start_all=$(date +%s)
while IFS= read -r -d '' gitdir; do
  repo=$(dirname "$gitdir")
  total=$((total+1))
  echo
  echo "Repo: $repo"
  dest="$repo/.github/copilot-instruction.md"
  mkdir -p "$repo/.github"
  start_ts=$(date +%s)
  cp "$COPILOT_SRC" "$dest"
  end_ts=$(date +%s)
  elapsed=$((end_ts-start_ts))
  echo "Copied to $dest ("$elapsed"s)"
  copied=$((copied+1))
done < <(find "$ROOT_DIR" -maxdepth 3 -type d -name .git -print0)
end_all=$(date +%s)
all_elapsed=$((end_all-start_all))

echo
printf "Completed: %d repos scanned, %d files copied in %d seconds\n" "$total" "$copied" "$all_elapsed"

echo "Done. Remember to review and commit changes in repositories where you want to keep the file."
