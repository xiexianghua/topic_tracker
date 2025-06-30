# Docker 部署说明

## 快速启动

### 使用 Docker Compose（推荐）

1. 克隆或下载项目文件

2. 在项目根目录创建 `.env` 文件（可选）：
```bash
GOOGLE_API_KEY=你的API密钥
RSS_HOST=http://192.168.8.3:5000
```

3. 构建并启动服务：
```bash
docker-compose up -d
```

4. 查看日志：
```bash
docker-compose logs -f
```

5. 停止服务：
```bash
docker-compose down
```

### 使用 Docker 命令

1. 构建镜像：
```bash
docker build -t topic-tracker .
```

2. 运行容器：
```bash
docker run -d \
  --name topic-tracker \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -e GOOGLE_API_KEY=你的API密钥 \
  -e RSS_HOST=http://192.168.8.3:5000 \
  -e TZ=Asia/Shanghai \
  topic-tracker
```

## 访问方式

部署成功后，可以通过以下方式访问：

- Web界面：`http://192.168.8.3:5000`
- 全部话题RSS：`http://192.168.8.3:5000/rss`
- 单个话题RSS：`http://192.168.8.3:5000/rss/{话题ID}`

## 数据持久化

- 数据库文件存储在 `./data` 目录下
- 使用 Docker 时，这个目录会被挂载到容器内
- 重启容器不会丢失数据

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| GOOGLE_API_KEY | Google AI API密钥 | 内置测试密钥 |
| RSS_HOST | RSS订阅的基础URL | http://localhost:5000 |
| TZ | 时区设置 | Asia/Shanghai |

## 注意事项

1. **网络访问**：确保防火墙允许 5000 端口访问
2. **API密钥**：建议使用自己的 Google API 密钥
3. **RSS_HOST**：设置为实际访问地址，如 `http://192.168.8.3:5000`

## 常见问题

### 无法通过IP访问
- 检查防火墙设置
- 确认 Docker 端口映射正确
- 使用 `docker ps` 查看容器状态

### 时间显示不正确
- 容器已设置为北京时间
- RSS 标题中会显示 "北京时间"
- Web 界面也会显示北京时间

### 数据库位置
- 宿主机：`./data/topic_tracker.db`
- 容器内：`/app/data/topic_tracker.db`