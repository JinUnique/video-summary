#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILL_NAME="video-summary"
CATEGORY="media"
SOURCE_DIR="${REPO_ROOT}/skills/${CATEGORY}/${SKILL_NAME}"
HERMES_HOME_DIR="${HERMES_HOME:-${HOME}/.hermes}"
TARGET_DIR="${HERMES_HOME_DIR}/skills/${CATEGORY}/${SKILL_NAME}"

if [[ ! -f "${SOURCE_DIR}/SKILL.md" ]]; then
  echo "missing source skill: ${SOURCE_DIR}/SKILL.md" >&2
  exit 1
fi

python3 - <<'PY' "${SOURCE_DIR}/SKILL.md"
from pathlib import Path
import re
import sys
import yaml
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if not text.startswith("---"):
    raise SystemExit("SKILL.md must start with frontmatter")
match = re.search(r"\n---\s*\n", text[3:])
if not match:
    raise SystemExit("SKILL.md frontmatter is not closed")
frontmatter = yaml.safe_load(text[3:match.start()+3])
if frontmatter.get("name") != "video-summary":
    raise SystemExit("unexpected skill name")
if len(frontmatter.get("description", "")) > 1024:
    raise SystemExit("description exceeds 1024 chars")
for token in ["bilibili.com", "b23.tv", "BV/av", "总结视频", "视频总结", "智能总结", "分析这个视频"]:
    if token not in frontmatter.get("description", ""):
        raise SystemExit(f"missing trigger token in description: {token}")
PY

mkdir -p "$(dirname "${TARGET_DIR}")"
TMP_DIR="$(mktemp -d "$(dirname "${TARGET_DIR}")/${SKILL_NAME}.tmp.XXXXXX")"
cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

cp -a "${SOURCE_DIR}/." "${TMP_DIR}/"
rm -rf "${TARGET_DIR}"
mv "${TMP_DIR}" "${TARGET_DIR}"
trap - EXIT
echo "installed ${SKILL_NAME} to ${TARGET_DIR}"
echo "verify with: hermes skills list | grep ${SKILL_NAME}"
