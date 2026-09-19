# TicketScope 企业 IT 工单管理系统

TicketScope 是一个面向企业内部 IT 服务台的全栈演示项目。它把员工报障、技术人员处理、管理员分派、SLA 监控、运营看板和报表导出串成一条可追踪的闭环，适合用于数字化实施、IT 支持、需求分析、产品助理和数据运营岗位的作品集展示。

> 项目数据均为程序生成的模拟数据。项目经历可以真实写入简历，但不要描述成真实公司上线成果或虚构业务指标。

## 已实现功能

- 邮箱密码登录与签名令牌认证
- 普通员工、技术人员、管理员三角色权限控制
- 工单创建、搜索、多条件筛选、分页和详情查看
- 待受理 → 已分配 → 处理中 → 已解决 → 已关闭的受控状态流转
- 不同优先级 SLA、临期预警、超时识别及 L1–L3 升级
- 负责人、解决方案和完整操作日志
- 角色数据隔离的运营看板
- 管理员按当前筛选条件导出 CSV 或 Excel
- 三种角色使用差异化工作台与独立标签页登录会话
- Pytest 自动化测试、Gunicorn 生产启动、Docker 与 Render 部署配置

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | Vue 3、Vite、ECharts、原生 CSS |
| 后端 | Python 3.12、Flask、REST API、itsdangerous |
| 数据 | SQLite、SQL、openpyxl |
| 测试与部署 | Pytest、Gunicorn、Docker、Render Blueprint |

## 演示账号

三个账号的密码均为 `Demo123!`。

| 角色 | 邮箱 | 可执行操作 |
|---|---|---|
| 管理员 | `ziang.liu@example.com` | 查看全部、分派、推进流程、升级超时工单、导出全部可见数据 |
| 技术人员 | `wang.chen@example.com` | 查看本人负责工单与待认领队列、认领并处理工单，不可创建或导出 |
| 普通员工 | `user1@example.com` | 创建并查看本人工单、确认关闭或重新打开，不可查看他人工单 |

## 本地运行

macOS 终端中依次执行：

```bash
cd /你的路径/enterprise-ticket-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m backend.seed --database backend/data/tickets.db --count 220
cd frontend
npm install
npm run build
cd ..
python run.py
```

浏览器打开 `http://127.0.0.1:5000`。其中：

- `cd`：进入指定文件夹。
- `python3 -m venv .venv`：创建项目专属 Python 环境。
- `source .venv/bin/activate`：启用该环境。
- `pip install -r requirements.txt`：安装后端依赖。
- `npm install`：安装前端依赖。
- `npm run build`：把前端打包到 `frontend/dist`。
- `python run.py`：启动本地服务。
- `Ctrl+C`：停止正在运行的服务。

以后再次运行通常只需：

```bash
cd /你的路径/enterprise-ticket-system
source .venv/bin/activate
python run.py
```

## 自动化验证

```bash
pytest -q
cd frontend && npm run build
```

当前版本验收结果：8 个后端/API 测试全部通过，前端生产构建通过，Gunicorn 生产模式健康检查、登录、列表、看板和 Excel 导出均通过。

## SLA 规则

| 优先级 | 处理期限 | 临期预警 |
|---|---:|---:|
| 低 | 72 小时 | 剩余 18 小时 |
| 中 | 48 小时 | 剩余 12 小时 |
| 高 | 24 小时 | 剩余 6 小时 |
| 紧急 | 8 小时 | 剩余 2 小时 |

未完成工单超过截止时间后显示“已超时”。管理员可执行 L1–L3 升级，操作会写入日志。已解决工单按解决时间与截止时间判断“达标/违约”。

## 项目结构

```text
enterprise-ticket-system/
├── backend/              Flask API、数据访问、初始化与模拟数据
├── frontend/             Vue 源码及生产构建产物
├── tests/                Pytest 接口与权限测试
├── docs/                 PRD、架构、API、数据库、测试、部署与面试材料
├── Dockerfile            容器部署配置
├── docker-compose.yml    带持久化卷的本地容器编排
├── render.yaml           Render Blueprint 配置
├── requirements.txt      Python 依赖
└── run.py                本地启动入口
```

## 文档导航

- [产品需求](docs/PRD.md)
- [系统架构](docs/architecture.md)
- [API 接口](docs/API.md)
- [数据库设计](docs/database-design.md)
- [测试用例与验收报告](docs/test-cases.md)
- [部署说明](docs/deployment.md)
- [简历写法](docs/resume-materials.md)
- [面试讲解](docs/interview-guide.md)

## 项目边界

这个版本足以作为校招作品集和现场演示，但仍是单机演示系统。真实企业落地还需要接入统一身份认证、PostgreSQL/MySQL、附件对象存储、消息通知、审计日志、监控告警、数据库迁移与更完善的安全策略。
