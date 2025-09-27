#!/bin/bash

# Pyodide統合テストスクリプト
# このスクリプトは remip-client をビルドしてからPyodideテストを実行します

set -e  # エラー時に停止

echo "🚀 Starting Pyodide integration test..."

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# remip-clientディレクトリに移動
cd remip-client

echo "📦 Building remip-client wheel..."
# uv buildでwheelをビルド
uv build

echo "✅ Build completed successfully"

# tests/nodeディレクトリに移動
cd tests/node

echo "🧪 Running Pyodide tests..."
# npm testを実行
npm test

echo "✅ All tests completed successfully!"
