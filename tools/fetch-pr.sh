#!/bin/bash

# ==================== 用户可配置区域 =====================
# 清理模式（递归清理全仓库）
CLEAN_PATTERNS=(
    ".logs"
    ".results"
    ".pytest_cache"
    "__pycache__"
)

# 主分支默认值
DEFAULT_MAIN_BRANCH="dev"

# PR 分支前缀
PR_BRANCH_PREFIX="pr-review"
# =======================================================

# 全局变量
declare -i VERBOSE=0
declare -i QUIET=0
MAIN_BRANCH=""
PR_NUMBER=""
UPDATE_ONLY=0

# ==================== 工具函数 =====================

# 输出日志 - DEBUG 级别
log_debug() {
    if [[ $VERBOSE -eq 1 ]]; then
        echo "[DEBUG] $*"
    fi
}

# 输出日志 - INFO 级别
log_info() {
    if [[ $QUIET -eq 0 ]]; then
        echo "[INFO] $*"
    fi
}

# 输出日志 - ERROR 级别
log_error() {
    echo "[ERROR] $*" >&2
}

# 输出日志 - SUCCESS 级别
log_success() {
    if [[ $QUIET -eq 0 ]]; then
        echo "[SUCCESS] $*"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
用法：$(basename "$0") [选项]

从 GitHub 拉取 PR 代码到本地，基于最新主分支创建审查环境。

选项:
  --pr <编号>        GitHub PR 编号（数字），与 --update-only 互斥
  --update-only      只更新主分支，不拉取 PR，与 --pr 互斥
  --branch <名称>    主分支名称（默认：$DEFAULT_MAIN_BRANCH）
  --verbose          详细输出模式
  --quiet            静默模式（只显示错误和关键信息）
  --help             显示此帮助信息

示例:
  $(basename "$0") --pr 42                    # 拉取 PR #42
  $(basename "$0") --pr 42 --branch main      # 指定主分支为 main
  $(basename "$0") --update-only              # 只更新主分支
  $(basename "$0") --update-only --branch dev # 指定主分支并更新

EOF
}

# 错误退出函数
error_exit() {
    local message="$1"
    local code="${2:-1}"
    log_error "$message"
    exit "$code"
}

# ==================== 核心功能函数 =====================

# 解析命令行参数
parse_args() {
    log_debug "开始解析参数：$*"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --pr)
                if [[ -z "$2" || "$2" == --* ]]; then
                    error_exit "错误：--pr 需要指定 PR 编号"
                fi
                PR_NUMBER="$2"
                shift 2
                ;;
            --update-only)
                UPDATE_ONLY=1
                shift
                ;;
            --branch)
                if [[ -z "$2" || "$2" == --* ]]; then
                    error_exit "错误：--branch 需要指定分支名称"
                fi
                MAIN_BRANCH="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=1
                shift
                ;;
            --quiet)
                QUIET=1
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error_exit "错误：未知参数 '$1'，使用 --help 查看用法"
                ;;
        esac
    done

    # 验证参数
    # 1. --pr 和 --update-only 互斥
    if [[ -n "$PR_NUMBER" && $UPDATE_ONLY -eq 1 ]]; then
        error_exit "错误：--pr 和 --update-only 不能同时使用"
    fi

    # 2. 必须提供 --pr 或 --update-only 之一
    if [[ -z "$PR_NUMBER" && $UPDATE_ONLY -eq 0 ]]; then
        error_exit "错误：必须指定 --pr 或 --update-only"
    fi

    # 3. PR 编号必须是数字
    if [[ -n "$PR_NUMBER" ]]; then
        if ! [[ "$PR_NUMBER" =~ ^[0-9]+$ ]]; then
            error_exit "错误：PR 编号必须是数字，收到：$PR_NUMBER"
        fi
    fi

    # 4. 设置主分支默认值
    if [[ -z "$MAIN_BRANCH" ]]; then
        MAIN_BRANCH="$DEFAULT_MAIN_BRANCH"
    fi

    log_debug "参数解析完成：PR_NUMBER=$PR_NUMBER, MAIN_BRANCH=$MAIN_BRANCH, UPDATE_ONLY=$UPDATE_ONLY"
}

# 检查是否在 git 仓库内
check_git_repo() {
    log_info "检查 git 仓库..."

    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error_exit "错误：当前目录不是 git 仓库"
    fi

    log_debug "执行：git rev-parse --git-dir"
    log_info "检查 git 仓库... ✓"
}

# 检查当前是否在指定的主分支上
check_current_branch() {
    log_info "检查当前分支..."

    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

    if [[ "$current_branch" != "$MAIN_BRANCH" ]]; then
        error_exit "错误：请先切换到 $MAIN_BRANCH 分支后运行此脚本（当前分支：$current_branch）"
    fi

    log_debug "当前分支：$current_branch"
    log_info "检查当前分支... ✓ ($MAIN_BRANCH)"
}

# 检查是否有未提交的更改
check_working_tree() {
    log_info "检查工作区状态..."

    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        error_exit "错误：请先提交或暂存当前更改"
    fi

    log_debug "工作区干净"
    log_info "检查工作区状态... ✓"
}

# 更新主分支
update_main_branch() {
    log_info "获取远程更新..."

    # Fetch 远程主分支
    if ! git fetch origin "$MAIN_BRANCH" 2>&1; then
        error_exit "错误：无法连接到远程仓库，请检查网络连接和 remote 配置"
    fi

    log_debug "执行：git fetch origin $MAIN_BRANCH"

    # Pull 更新主分支（使用 rebase）
    log_info "更新 $MAIN_BRANCH 分支..."
    if ! git pull --rebase origin "$MAIN_BRANCH" > /dev/null 2>&1; then
        error_exit "错误：更新 $MAIN_BRANCH 分支失败"
    fi

    log_debug "执行：git pull --rebase origin $MAIN_BRANCH"
    log_info "更新 $MAIN_BRANCH 分支... ✓"
}

# 清理缓存文件
cleanup_cache() {
    log_info "清理缓存文件..."

    local deleted_count=0

    for pattern in "${CLEAN_PATTERNS[@]}"; do
        log_debug "清理模式：$pattern"

        # 使用 find 递归查找并删除
        while IFS= read -r -d '' file; do
            if [[ -e "$file" ]]; then
                rm -rf "$file" 2>/dev/null && ((deleted_count++))
                log_debug "已删除：$file"
            fi
        done < <(find . -name "$pattern" -print0 2>/dev/null)
    done

    log_info "清理缓存文件... ✓ (删除 $deleted_count 个目录/文件)"
}

# 拉取 PR 分支
fetch_pr_branch() {
    local pr_branch="$PR_BRANCH_PREFIX/$PR_NUMBER"

    # 检查 PR 分支是否已存在
    if git rev-parse --verify "$pr_branch" > /dev/null 2>&1; then
        error_exit "错误：分支 $pr_branch 已存在，请先删除（git branch -D $pr_branch）"
    fi

    log_info "创建 PR 分支..."
    log_debug "执行：git fetch origin pull/$PR_NUMBER/head:$pr_branch"

    # Fetch PR 代码
    if ! git fetch origin "pull/$PR_NUMBER/head:$pr_branch" 2>&1; then
        error_exit "错误：无法获取 PR #$PR_NUMBER，请检查 PR 编号是否正确"
    fi

    # Checkout 到 PR 分支
    if ! git checkout "$pr_branch" > /dev/null 2>&1; then
        # 回滚：删除已创建的分支
        git branch -D "$pr_branch" 2>/dev/null
        error_exit "错误：切换到 PR 分支失败"
    fi

    log_info "创建 PR 分支... ✓ ($pr_branch)"
}

# ==================== 主函数 =====================

main() {
    # 解析参数
    parse_args "$@"

    # 执行检查
    check_git_repo
    check_current_branch
    check_working_tree

    # 更新主分支
    update_main_branch

    # 清理缓存
    cleanup_cache

    # 如果是 update-only 模式，直接完成
    if [[ $UPDATE_ONLY -eq 1 ]]; then
        log_success "完成！当前分支：$MAIN_BRANCH"
        exit 0
    fi

    # 拉取 PR 分支
    fetch_pr_branch

    # 完成
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    log_success "完成！当前分支：$current_branch"
}

# 脚本入口
main "$@"
