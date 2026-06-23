#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="excel-to-html-slides"

install_skill() {
  local dest_root="$1"
  local dest="$dest_root/$SKILL_NAME"
  mkdir -p "$dest_root"
  rm -rf "$dest"
  mkdir -p "$dest"
  cp "$ROOT_DIR/SKILL.md" "$dest/SKILL.md"
  if [ -f "$ROOT_DIR/requirements.txt" ]; then
    cp "$ROOT_DIR/requirements.txt" "$dest/requirements.txt"
  fi
  cp -R "$ROOT_DIR/scripts" "$dest/scripts"
  cp -R "$ROOT_DIR/references" "$dest/references"
  cp -R "$ROOT_DIR/assets" "$dest/assets"
  cp -R "$ROOT_DIR/report-template-pack" "$dest/report-template-pack"
  if [ -d "$ROOT_DIR/agents" ]; then
    cp -R "$ROOT_DIR/agents" "$dest/agents"
  fi
  echo "Installed $SKILL_NAME to $dest"
  echo "If pandas/openpyxl are missing, run: pip install -r \"$dest/requirements.txt\""
}

case "${1:-all}" in
  workbuddy)
    install_skill "$HOME/.workbuddy/skills"
    ;;
  codex)
    install_skill "${CODEX_HOME:-$HOME/.codex}/skills"
    ;;
  claude)
    install_skill "$HOME/.claude/skills"
    ;;
  all)
    install_skill "$HOME/.workbuddy/skills"
    install_skill "${CODEX_HOME:-$HOME/.codex}/skills"
    install_skill "$HOME/.claude/skills"
    ;;
  *)
    echo "Usage: ./install.sh [all|workbuddy|codex|claude]" >&2
    exit 1
    ;;
esac
