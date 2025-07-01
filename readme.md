## 使用说明

### 1. 环境准备
```bash
# 克隆或创建项目目录
mkdir ai-bark-system
cd ai-bark-system

# 创建目录结构
mkdir -p backend frontend data scripts/templates
```

### 2. 配置环境变量
编辑 `docker-compose.yml` 文件，替换以下配置：
- `GEMINI_API_KEY`: 您的Google Gemini API密钥
- `BARK_DEVICE_KEY`: 您的Bark设备密钥

### 3. 启动服务
```bash
# 使用Docker Compose启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 访问系统
打开浏览器访问：http://localhost:5000

## 功能特点

1. **脚本管理**
   - 创建、编辑、删除脚本
   - 在线代码编辑器
   - 脚本模板支持

2. **自动运行**
   - 设置运行间隔
   - 启用/禁用自动运行
   - 后台定时执行

3. **运行监控**
   - 查看运行历史
   - 查看输出和错误信息
   - 运行状态显示

4. **Docker部署**
   - 一键部署
   - 数据持久化
   - 容器化运行

## 注意事项

1. 请确保正确配置API密钥
2. 脚本运行有5分钟超时限制
3. 建议定期备份 `data` 目录
4. 生产环境建议使用PostgreSQL替代SQLite

## 扩展功能建议

1. 添加用户认证系统
2. 支持更多推送渠道（邮件、微信等）
3. 添加脚本版本控制
4. 支持脚本依赖管理
5. 添加运行日志分析功能

## 快速部署脚本

### deploy.sh (Linux/Mac)
```bash
#!/bin/bash

# AI Bark System 快速部署脚本

echo "🚀 AI Bark System 快速部署脚本"
echo "================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 创建项目目录结构
echo "📁 创建项目目录结构..."
mkdir -p ai-bark-system/{backend,frontend,data,scripts/templates}
cd ai-bark-system

# 创建所有必要的文件
echo "📝 创建项目文件..."

# 创建bark_sender.py
cat > backend/bark_sender.py << 'EOF'
# 这里插入完整的bark_sender.py内容
EOF

# 创建其他backend文件...
# (这里省略，实际使用时需要创建所有文件)

# 提示用户配置
echo ""
echo "⚙️  请配置以下环境变量："
echo "1. 编辑 docker-compose.yml 文件"
echo "2. 替换 GEMINI_API_KEY 为您的Google Gemini API密钥"
echo "3. 替换 BARK_DEVICE_KEY 为您的Bark设备密钥"
echo ""
read -p "配置完成后按Enter继续..."

# 启动服务
echo "🐳 启动Docker容器..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo "✅ 服务启动成功！"
    echo "🌐 访问地址: http://localhost:5000"
    echo ""
    echo "📊 查看日志: docker-compose logs -f"
    echo "🛑 停止服务: docker-compose down"
else
    echo "❌ 服务启动失败，请检查日志"
    docker-compose logs
fi
```

### deploy.bat (Windows)
```batch
@echo off
echo 🚀 AI Bark System 快速部署脚本
echo ================================

REM 检查Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

REM 创建目录结构
echo 📁 创建项目目录结构...
mkdir ai-bark-system\backend 2>nul
mkdir ai-bark-system\frontend 2>nul
mkdir ai-bark-system\data 2>nul
mkdir ai-bark-system\scripts\templates 2>nul
cd ai-bark-system

REM 提示配置
echo.
echo ⚙️  请配置以下环境变量：
echo 1. 编辑 docker-compose.yml 文件
echo 2. 替换 GEMINI_API_KEY 为您的Google Gemini API密钥
echo 3. 替换 BARK_DEVICE_KEY 为您的Bark设备密钥
echo.
pause

REM 启动服务
echo 🐳 启动Docker容器...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
docker-compose ps | find "Up" >nul
if errorlevel 1 (
    echo ❌ 服务启动失败，请检查日志
    docker-compose logs
) else (
    echo ✅ 服务启动成功！
    echo 🌐 访问地址: http://localhost:5000
    echo.
    echo 📊 查看日志: docker-compose logs -f
    echo 🛑 停止服务: docker-compose down
)

pause
```

## README.md
```markdown
# AI搜索与Bark推送管理系统

一个基于Web的AI搜索和Bark推送管理平台，支持创建、编辑和定时执行Python脚本。

## 功能特点

- 🤖 集成Google Gemini AI搜索功能
- 📱 支持Bark推送通知
- 📝 在线脚本编辑器
- ⏰ 定时任务调度
- 📊 运行历史记录
- 🐳 Docker一键部署
- 🎨 现代化Web界面

## 快速开始

### 方式一：使用部署脚本

**Linux/Mac:**
```bash
curl -O https://raw.githubusercontent.com/your-repo/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

**Windows:**
下载并运行 `deploy.bat`

### 方式二：手动部署

1. 克隆项目（或创建项目目录）
```bash
git clone https://github.com/your-repo/ai-bark-system.git
cd ai-bark-system
```

2. 配置环境变量
编辑 `docker-compose.yml`，设置：
- `GEMINI_API_KEY`: Google Gemini API密钥
- `BARK_DEVICE_KEY`: Bark设备密钥

3. 启动服务
```bash
docker-compose up -d
```

4. 访问系统
打开浏览器访问: http://localhost:5000

## 使用指南

### 创建脚本
1. 点击"创建新脚本"按钮
2. 输入脚本名称和描述
3. 编写Python代码或使用模板
4. 设置运行间隔（可选）
5. 保存脚本

### 脚本模板
系统提供了多个实用模板：
- AI搜索并推送
- 定时天气推送
- 股票价格监控

### 定时执行
- 设置运行间隔（分钟）
- 勾选"启用自动运行"
- 系统将按设定间隔自动执行脚本

## 配置说明

### 环境变量
- `GEMINI_API_KEY`: Google Gemini API密钥
- `BARK_DEVICE_KEY`: Bark设备密钥
- `BARK_API_SERVER`: 自定义Bark服务器地址（可选）
- `DATABASE_URL`: 数据库连接URL（默认SQLite）

### 目录结构
```
ai-bark-system/
├── backend/          # 后端代码
├── frontend/         # 前端代码
├── data/            # 数据存储
├── scripts/         # 脚本存储
└── docker-compose.yml
```

## API文档

### 脚本管理
- `GET /api/scripts` - 获取所有脚本
- `POST /api/scripts` - 创建新脚本
- `PUT /api/scripts/:id` - 更新脚本
- `DELETE /api/scripts/:id` - 删除脚本

### 脚本执行
- `POST /api/scripts/:id/run` - 立即运行脚本
- `GET /api/scripts/:id/runs` - 获取运行历史

### 模板
- `GET /api/templates` - 获取脚本模板

## 开发指南

### 本地开发
```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 启动后端
python app.py

# 前端直接使用浏览器打开 frontend/index.html
```

### 添加新模板
在 `backend/app.py` 的 `get_templates` 函数中添加模板。

## 故障排除

### Docker容器无法启动
- 检查端口5000是否被占用
- 查看日志: `docker-compose logs`

### API密钥错误
- 确认已正确设置环境变量
- 检查API密钥是否有效

### 脚本执行失败
- 查看运行历史中的错误信息
- 确认脚本代码无语法错误
- 检查依赖是否已安装

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License