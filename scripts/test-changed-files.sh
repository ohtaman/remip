#!/bin/bash

# 変更されたファイルに関連するテストとlintを実行するスクリプト

set -e

# 色付きの出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# 変更されたファイルを取得
if [ "$1" = "staged" ]; then
    # pre-commit: ステージされたファイルのみ
    CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR)
    print_info "Checking staged files for pre-commit..."
elif [ "$1" = "all" ]; then
    # pre-push: 全ての変更されたファイル
    CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --name-only)
    print_info "Checking all changed files for pre-push..."
else
    # デフォルト: 現在の変更
    CHANGED_FILES=$(git diff --name-only)
    print_info "Checking current changes..."
fi

# テスト関連ファイルのみをフィルタリング
CHANGED_FILES=$(echo "$CHANGED_FILES" | grep -E '\.(py|js|json|yaml|yml|toml|md|sh)$' || true)

if [ -z "$CHANGED_FILES" ]; then
    print_warning "No changed files detected"
    exit 0
fi

print_info "Changed files:"
echo "$CHANGED_FILES" | sed 's/^/  /'

# どのプロジェクトが影響を受けるかを判定
REQUIRE_REMIP_SERVER=false
REQUIRE_REMIP_CLIENT=false
REQUIRE_PYODIDE=false

for file in $CHANGED_FILES; do
    if [[ $file == remip/* ]]; then
        REQUIRE_REMIP_SERVER=true
    fi
    if [[ $file == remip-client/* ]]; then
        REQUIRE_REMIP_CLIENT=true
        if [[ $file == remip-client/tests/node/* ]] || [[ $file == remip-client/src/remip_client/* ]]; then
            REQUIRE_PYODIDE=true
        fi
    fi
    # ルートレベルのファイル（Makefile, scripts等）が変更された場合は全て実行
    if [[ $file == Makefile ]] || [[ $file == scripts/* ]] || [[ $file == .github/workflows/* ]]; then
        REQUIRE_REMIP_SERVER=true
        REQUIRE_REMIP_CLIENT=true
        REQUIRE_PYODIDE=true
    fi
done

print_info "Required tests:"
[ "$REQUIRE_REMIP_SERVER" = true ] && echo "  - remip server"
[ "$REQUIRE_REMIP_CLIENT" = true ] && echo "  - remip-client Python"
[ "$REQUIRE_PYODIDE" = true ] && echo "  - remip-client Pyodide"

# remip server のテストとlint
if [ "$REQUIRE_REMIP_SERVER" = true ]; then
    print_info "Running remip server lint and tests..."

    # Lint
    cd remip
    if uv run ruff check --fix .; then
        print_success "remip server lint passed"
    else
        print_error "remip server lint failed"
        exit 1
    fi

    # Format
    if uv run ruff format .; then
        print_success "remip server format passed"
    else
        print_error "remip server format failed"
        exit 1
    fi

    # Tests
    if uv run pytest tests/ -v; then
        print_success "remip server tests passed"
    else
        print_error "remip server tests failed"
        exit 1
    fi

    cd ..
fi

# remip-client Python のテストとlint
if [ "$REQUIRE_REMIP_CLIENT" = true ]; then
    print_info "Running remip-client Python lint and tests..."

    # Lint
    cd remip-client
    if uv run ruff check --fix .; then
        print_success "remip-client Python lint passed"
    else
        print_error "remip-client Python lint failed"
        exit 1
    fi

    # Format
    if uv run ruff format .; then
        print_success "remip-client Python format passed"
    else
        print_error "remip-client Python format failed"
        exit 1
    fi

    # Tests
    if uv run pytest tests/ -v; then
        print_success "remip-client Python tests passed"
    else
        print_error "remip-client Python tests failed"
        exit 1
    fi

    cd ..
fi

# remip-client Pyodide のテスト
if [ "$REQUIRE_PYODIDE" = true ]; then
    print_info "Running remip-client Pyodide tests..."

    if ./scripts/test-pyodide.sh; then
        print_success "remip-client Pyodide tests passed"
    else
        print_error "remip-client Pyodide tests failed"
        exit 1
    fi
fi

print_success "All required tests and linting passed! 🎉"
