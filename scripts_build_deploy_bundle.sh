#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d deploy_bundle ]; then
  echo "deploy_bundle 目录不存在" >&2
  exit 1
fi

zip -r deploy_bundle.zip deploy_bundle

echo "已生成: $ROOT_DIR/deploy_bundle.zip"
