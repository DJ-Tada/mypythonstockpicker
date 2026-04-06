#!/usr/bin/env zsh
# Install ~/Downloads/copilot-instruction.md into this repo's .github/ directory.

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$REPO_ROOT/scripts/common_env.sh" || true
SRC="$HOME/Downloads/copilot-instruction.md"
DEST="$REPO_ROOT/.github/copilot-instruction.md"

AUTO_YES=0
if [[ "${1:-}" == "--yes" || "${1:-}" == "-y" || "$AUTO_APPROVE" == "1" ]]; then
  AUTO_YES=1
fi

if [[ ! -f "$SRC" ]]; then
  echo "No file found at $SRC"
  exit 1
fi

echo "Found $SRC. Showing first 40 lines:" 
sed -n '1,40p' "$SRC" || true

if [[ $AUTO_YES -eq 0 ]]; then
  echo
  read -q "REPLY?Do you want to copy $SRC to $DEST and commit it to this repo? (y/N): "
  echo
  if [[ "$REPLY" != [Yy] ]]; then
    echo "Aborted by user."
    exit 0
  fi
else
  echo "AUTO_YES set: proceeding without prompting"
  REPLY=Y
fi

start_ts=$(date +%s)
cp "$SRC" "$DEST" &
cp_pid=$!
spinner_chars=( '|' '/' '-' '\\' )
 i=0
while kill -0 $cp_pid 2>/dev/null; do
  printf "\r%s Copying..." "${spinner_chars[i % ${#spinner_chars[@]}]}"
  sleep 0.08
  i=$((i+1))
done
wait $cp_pid
end_ts=$(date +%s)
elapsed=$((end_ts - start_ts))
printf "\rCopied to %s (%.2fs)\n" "$DEST" "$elapsed"

if [[ $AUTO_YES -eq 1 || "$AUTO_APPROVE" == "1" ]]; then
  COMMIT=Y
else
  read -q "COMMIT?Do you also want to git add and commit the file? (y/N): "
  echo
fi

if [[ "${COMMIT:-}" == [Yy] ]]; then
  cd "$REPO_ROOT"
  git add ".github/copilot-instruction.md"
  git commit -m "Add copilot-instruction.md from Downloads"
  echo "Committed."
else
  echo "File copied but not committed."
fi
