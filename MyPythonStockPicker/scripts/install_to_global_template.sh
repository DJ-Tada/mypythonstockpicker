#!/usr/bin/env zsh
# Install this repo's .github/copilot-instruction.md into the user's global git template

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$REPO_ROOT/scripts/common_env.sh" || true
SRC="$REPO_ROOT/.github/copilot-instruction.md"
TEMPLATE_DIR="$HOME/.git-templates"
DEST="$TEMPLATE_DIR/.github/copilot-instruction.md"

AUTO_YES=0
if [[ "${1:-}" == "--yes" || "${1:-}" == "-y" || "$AUTO_APPROVE" == "1" ]]; then
  AUTO_YES=1
fi

if [[ ! -f "$SRC" ]]; then
  echo "Source file not found: $SRC"
  exit 1
fi

echo "About to copy: $SRC -> $DEST"
if [[ $AUTO_YES -eq 0 ]]; then
  read -q "REPLY?Proceed? (y/N): "
  echo
  if [[ "$REPLY" != [Yy] ]]; then
    echo "Aborted by user."
    exit 0
  fi
else
  echo "AUTO_APPROVE set: proceeding without prompting"
  REPLY=Y
fi

mkdir -p "$(dirname "$DEST")"

# Copy with a simple spinner while the copy runs (useful if the file is on slow disk)
start_ts=$(date +%s)
cp "$SRC" "$DEST" &
cp_pid=$!
spinner_chars=( '|' '/' '-' '\\' )
i=0
while kill -0 $cp_pid 2>/dev/null; do
  idx=$(( i % ${#spinner_chars[@]} ))
  idx=$(( idx + 1 ))
  printf "\r%s Copying..." "${spinner_chars[$idx]}"
  sleep 0.08
  i=$((i+1))
done
wait $cp_pid
end_ts=$(date +%s)
elapsed=$((end_ts - start_ts))
printf "\rCopied to %s (%.2fs)\n" "$DEST" "$elapsed"

echo "Setting git global template dir to $TEMPLATE_DIR"
git config --global init.templateDir "$TEMPLATE_DIR"
echo "git config set to: $(git config --global --get init.templateDir)"

echo "Done. New repositories created with 'git init' will now include the .github/copilot-instruction.md file by default."
