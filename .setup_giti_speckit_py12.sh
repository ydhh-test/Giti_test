#!/bin/bash

# ==================== 配置区域 ====================
ENV_NAME="py12_giti_speckit"
PROJECT_PATH="/Users/guiyu/aiProjects/claudeProjects/giti-tire-ai-pattern"

# ==================== 1. 检查conda环境（不存在则报错退出） ====================
echo -e "\n===== conda env: ${ENV_NAME} ===== START ====="
# 检查环境是否存在
conda env list | grep -q "^${ENV_NAME}\s"
if [ $? -ne 0 ]; then
    echo -e "❌ 错误：conda环境 ${ENV_NAME} 不存在！请先手动创建环境后再运行脚本。"
    exit 1
else
    echo "环境 ${ENV_NAME} 已存在，开始激活..."
fi

# 改用 conda activate 激活环境（按你的要求修改）
conda activate ${ENV_NAME}
# 若执行后提示"CommandNotFoundError"，可取消下面这行注释（兼容方案）
# eval "$(conda shell.bash hook)" && conda activate ${ENV_NAME}

echo -e "===== conda env: ${PROJECT_PATH} ===== END =====\n"

# ==================== 2. 切换到PROJECT目录 ====================
echo -e "===== cd ${PROJECT_PATH} ===== START ====="
if [ ! -d "${PROJECT_PATH}" ]; then
    echo -e "❌ 错误：目录 ${PROJECT_PATH} 不存在！"
    exit 1
fi

cd ${PROJECT_PATH}
echo "当前目录: $(pwd)"
echo -e "===== cd ${PROJECT_PATH} ===== END =====\n"

# ==================== 3. 配置PYTHONPATH ====================
echo -e "===== export PYTHONPATH ===== START ====="
export PYTHONPATH=${PROJECT_PATH}:$PYTHONPATH
echo "当前PYTHONPATH: ${PYTHONPATH}"
echo -e "===== export PYTHONPATH ===== END =====\n"

# 最终提示
echo "✅ DPIR环境配置完成！"
echo "  - Conda环境：${ENV_NAME}"
echo "  - 工作目录：${PROJECT_PATH}"
echo "  - PYTHONPATH已包含：${PROJECT_PATH}"
