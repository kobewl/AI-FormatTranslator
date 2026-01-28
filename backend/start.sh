#!/bin/bash
# DocTranslator 后端启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到项目目录
cd "$SCRIPT_DIR"

echo "📂 当前目录: $SCRIPT_DIR"

# 先取消任何已激活的虚拟环境
deactivate 2>/dev/null

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建：python3 -m venv venv"
    exit 1
fi

# 激活当前项目的虚拟环境
echo "🔧 激活虚拟环境: $SCRIPT_DIR/venv"
source "$SCRIPT_DIR/venv/bin/activate"

echo "🐍 Python 环境: $(which python)"
echo ""

# 检查依赖是否安装
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 安装依赖..."
    pip install -r requirements.txt
fi

# 检查端口是否被占用
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 8000 已被占用，尝试关闭旧进程..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# 启动服务
echo "🚀 启动 DocTranslator API..."
python run.py
