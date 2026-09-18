# 部署说明

## 方式一：本地生产模式

先构建前端，再由 Gunicorn 同时提供 API 和静态页面：

```bash
cd frontend
npm install
npm run build
cd ..
pip install -r requirements.txt
TICKET_SECRET_KEY='请替换为随机长字符串' \
TICKET_DATABASE='backend/data/tickets.db' \
gunicorn --workers 2 --threads 4 --bind 0.0.0.0:5000 'backend.app:create_app()'
```

## 方式二：Docker Compose

```bash
docker compose up --build
```

访问 `http://127.0.0.1:5000`。Compose 使用名为 `ticket-data` 的卷保存 SQLite 数据。

## 方式三：Render 在线演示

仓库根目录已提供 `render.yaml`：

1. 把项目推送到自己的 GitHub 仓库。
2. 在 Render 新建 Blueprint，授权并选择该仓库。
3. Render 会读取 `render.yaml`，安装依赖并用 Gunicorn 启动。
4. 部署完成后打开平台生成的公网地址，使用 README 中的演示账号登录。

配置中启用了 `TICKET_SEED_DEMO=true`，空数据库首次启动时自动生成 220 条模拟数据。

## 环境变量

| 变量 | 作用 | 建议 |
|---|---|---|
| `TICKET_SECRET_KEY` | 签名登录令牌 | 生产环境使用随机长字符串 |
| `TICKET_DATABASE` | SQLite 文件路径 | 本地可用项目路径，临时云实例可用 `/tmp/tickets.db` |
| `TICKET_SEED_DEMO` | 空库自动生成演示数据 | 演示站设 `true`，真实环境设 `false` |
| `AUTH_TOKEN_MAX_AGE` | 登录有效期（秒） | 默认 `86400` |
| `PORT` | 服务监听端口 | 通常由平台注入 |

## 数据持久化说明

`render.yaml` 使用 `/tmp/tickets.db`，适合无需保留用户修改的作品集演示；实例重建后数据可能恢复为新一批模拟数据。真实使用应接入 PostgreSQL 或平台持久化磁盘，并关闭自动模拟数据。

## 上线检查

- `/api/health` 返回 `status: ok`。
- 三个演示角色均能登录，且可见数据和按钮不同。
- 管理员能完成分派、处理、解决、关闭与超时升级。
- CSV、Excel 文件可以正常下载和打开。
- `FLASK_DEBUG=0`，`TICKET_SECRET_KEY` 未使用示例值。

