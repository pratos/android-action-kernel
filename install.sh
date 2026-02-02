#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/actionstatelabs/android-action-kernel.git"
TARGET_DIR="${1:-android-action-kernel}"

is_repo_root() {
  [[ -f "pyproject.toml" && -f "README.md" ]]
}

if is_repo_root; then
  REPO_DIR="$(pwd)"
else
  if [[ -d "${TARGET_DIR}/.git" ]]; then
    REPO_DIR="$TARGET_DIR"
  else
    echo "Cloning ${REPO_URL} → ${TARGET_DIR}"
    git clone "${REPO_URL}" "${TARGET_DIR}"
    REPO_DIR="$TARGET_DIR"
  fi
  cd "$REPO_DIR"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install it first:"
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

echo "Installing Python dependencies with uv..."
uv sync

if command -v adb >/dev/null 2>&1; then
  echo "Verifying ADB connection..."
  adb devices || true
else
  echo "adb not found. Install it first:"
  case "$(uname -s)" in
    Darwin)
      echo "  brew install android-platform-tools"
      ;;
    Linux)
      echo "  sudo apt-get install adb"
      ;;
    *)
      echo "  Install Android Platform Tools for your OS"
      ;;
  esac
fi

cat <<'EOF'

Next steps:
1) Export your API key (and providers if needed):
   export OPENAI_API_KEY="sk-..."
   export LLM_PROVIDERS="openai,groq,bedrock"  # optional, defaults to openai

2) Run your first agent:
   uv run android-action-kernel
   # or: uv run python src/kernel.py
EOF
