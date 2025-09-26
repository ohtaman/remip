#!/bin/bash

# 全テスト実行スクリプト
# このスクリプトは全てのテストを順次実行します

set -e  # エラー時に停止

echo "🚀 Starting comprehensive test suite..."

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# 色付きの出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Test remip server
echo "📦 Testing remip server..."
cd remip
if uv run pytest tests/ -v; then
    print_status "remip server tests passed"
else
    print_error "remip server tests failed"
    exit 1
fi

# 2. Test remip-client Python
echo "📦 Testing remip-client (Python)..."
cd ../remip-client
if uv run pytest tests/ -v; then
    print_status "remip-client Python tests passed"
else
    print_error "remip-client Python tests failed"
    exit 1
fi

# 3. Test remip-client Pyodide/Node.js
echo "🌐 Testing remip-client (Pyodide/Node.js)..."
cd tests/node
if npm run build-and-test; then
    print_status "remip-client Pyodide tests passed"
else
    print_error "remip-client Pyodide tests failed"
    exit 1
fi

# 4. Integration test with running server
echo "🔄 Running integration tests with live server..."
cd ../../../
cd remip

# Start server in background
print_warning "Starting server in background..."
uv run python -m remip.main &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Check if server is running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "Server is running"

    # Run integration tests
    cd ../remip-client
    if uv run pytest tests/ -v; then
        print_status "Integration tests passed"
    else
        print_error "Integration tests failed"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
else
    print_error "Server failed to start"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Clean up
kill $SERVER_PID 2>/dev/null || true
print_status "Server stopped"

print_status "All tests completed successfully! 🎉"
