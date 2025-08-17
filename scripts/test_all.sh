#!/bin/bash
# test_all.sh - 运行所有测试并生成报告
# MCPSecTrace 重构后综合测试脚本

set -e  # 遇到错误时停止执行

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️ $message${NC}"
            ;;
        *)
            echo "$message"
            ;;
    esac
}

# 检查命令是否存在
check_command() {
    if command -v $1 >/dev/null 2>&1; then
        print_status "SUCCESS" "$1 可用"
        return 0
    else
        print_status "ERROR" "$1 不可用"
        return 1
    fi
}

# 运行测试并捕获结果
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo ""
    echo "🔍 执行: $test_name"
    echo "----------------------------------------"
    
    if eval $test_command; then
        print_status "SUCCESS" "$test_name 通过"
        return 0
    else
        print_status "ERROR" "$test_name 失败"
        return 1
    fi
}

# 主函数
main() {
    echo "🚀 MCPSecTrace 重构后测试报告"
    echo "========================================"
    echo "测试时间: $(date)"
    echo "操作系统: $(uname -s)"
    echo "Python版本: $(python --version 2>&1)"
    echo "当前目录: $(pwd)"
    echo ""

    local total_tests=0
    local passed_tests=0

    # 1. 环境检查
    echo "🔧 环境检查"
    echo "----------------------------------------"
    
    if check_command python; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    if check_command uv; then
        ((passed_tests++))
    fi
    ((total_tests++))

    # 2. 依赖安装测试
    if run_test "依赖安装" "uv sync"; then
        ((passed_tests++))
    fi
    ((total_tests++))

    # 3. 项目结构检查
    if run_test "项目结构检查" "python -c 'import src.mcpsectrace; print(\"项目包导入成功\")'"; then
        ((passed_tests++))
    fi
    ((total_tests++))

    # 4. 模块导入测试
    if run_test "模块导入测试" "python tests/integration/test_imports.py"; then
        ((passed_tests++))
    fi
    ((total_tests++))

    # 5. 工具功能测试
    if run_test "工具功能测试" "python tests/unit/test_utils.py"; then
        ((passed_tests++))
    fi
    ((total_tests++))

    # 6. 代码质量检查
    echo ""
    echo "✨ 代码质量检查"
    echo "----------------------------------------"
    
    # 代码格式检查
    if uv run black --check src/ >/dev/null 2>&1; then
        print_status "SUCCESS" "代码格式正确"
        ((passed_tests++))
    else
        print_status "WARNING" "代码格式需要修复"
    fi
    ((total_tests++))

    # 导入排序检查
    if uv run isort --check-only src/ >/dev/null 2>&1; then
        print_status "SUCCESS" "导入排序正确"
        ((passed_tests++))
    else
        print_status "WARNING" "导入排序需要修复"
    fi
    ((total_tests++))

    # 7. 脚本文件检查
    if run_test "启动脚本检查" "python scripts/run_browser_forensics.py --help >/dev/null 2>&1"; then
        ((passed_tests++))
    fi
    ((total_tests++))

    # 8. 文档完整性检查
    echo ""
    echo "📚 文档完整性检查"
    echo "----------------------------------------"
    
    docs=(
        "README.md"
        "CLAUDE.md" 
        "docs/development/github-collaboration-guide.md"
        "docs/development/post-refactor-testing-guide.md"
    )
    
    doc_score=0
    for doc in "${docs[@]}"; do
        if [[ -f "$doc" ]]; then
            print_status "SUCCESS" "$doc"
            ((doc_score++))
        else
            print_status "ERROR" "缺少: $doc"
        fi
    done
    
    if [[ $doc_score -eq ${#docs[@]} ]]; then
        ((passed_tests++))
    fi
    ((total_tests++))

    # 9. 外部MCP服务器检查
    echo ""
    echo "🔗 外部MCP服务器检查"
    echo "----------------------------------------"
    
    external_mcp=(
        "external_mcp/ThreatMCP"
        "external_mcp/winlog-mcp"
        "external_mcp/fdp-mcp-server"
        "external_mcp/mcp-everything-search"
    )
    
    mcp_score=0
    for server in "${external_mcp[@]}"; do
        if [[ -d "$server" ]]; then
            print_status "SUCCESS" "$server"
            ((mcp_score++))
        else
            print_status "ERROR" "缺少: $server"
        fi
    done
    
    if [[ $mcp_score -eq ${#external_mcp[@]} ]]; then
        ((passed_tests++))
    fi
    ((total_tests++))

    # 生成最终报告
    echo ""
    echo "📊 测试总结"
    echo "========================================"
    echo "总测试项: $total_tests"
    echo "通过数量: $passed_tests"
    echo "失败数量: $((total_tests - passed_tests))"
    echo "通过率: $(( passed_tests * 100 / total_tests ))%"
    echo ""

    if [[ $passed_tests -eq $total_tests ]]; then
        print_status "SUCCESS" "所有测试通过！项目重构成功。"
        echo ""
        echo "🎉 恭喜！重构后的MCPSecTrace项目已准备就绪。"
        echo ""
        echo "下一步建议："
        echo "1. 运行 'uv sync' 确保依赖完整"
        echo "2. 阅读 docs/development/ 中的开发文档"
        echo "3. 使用新的启动脚本测试功能"
        return 0
    else
        print_status "WARNING" "部分测试失败，建议检查问题。"
        echo ""
        echo "故障排除："
        echo "1. 检查Python环境和依赖"
        echo "2. 确认项目结构完整"
        echo "3. 参考 docs/development/post-refactor-testing-guide.md"
        return 1
    fi
}

# 检查是否在项目根目录
if [[ ! -f "pyproject.toml" ]] || [[ ! -d "src/mcpsectrace" ]]; then
    print_status "ERROR" "请在项目根目录运行此脚本"
    exit 1
fi

# 运行主函数
main "$@"