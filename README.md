# 企业IT工单与运营管理系统

这是一个面向校招作品集的全栈演示项目。项目模拟企业内部IT服务台，从需求拆解、数据库设计、REST API、前端页面、状态流转、运营指标到测试文档形成完整闭环。

> 数据声明：仓库内工单、人员和部门均由程序生成，仅用于功能演示，不代表任何真实企业或真实业务数据。

## 项目价值

项目用于展示以下岗位能力：

- 数字化实施与软件实施
- 需求分析与产品助理
- IT运营与技术支持
- 售前解决方案与项目助理
- 数据分析与运营看板

## 已实现功能

- 创建工单，设置部门、类型和优先级
- 工单分页、关键词检索及多条件筛选
- 分配负责人并按照规则推进状态
- 记录解决方案和完整操作日志
- 根据优先级自动生成SLA截止时间
- 统计总量、解决率、平均处理时长及超时工单
- 展示状态、问题类型、部门和近30天趋势图表
- 生成220条可复现的模拟数据
- 提供5项后端自动化测试

状态流转规则：

```text
待受理 → 已分配 → 处理中 → 已解决 → 已关闭
                          ↘ 重新打开 ↗
```

## 技术栈

### 后端

- Python 3.11+
- Flask 3
- SQLite
- Flask-Cors
- Pytest

### 前端

- Vue 3
- Vite
- ECharts
- 原生Fetch API

## 项目结构

```text
enterprise-ticket-system/
├── backend/
│   ├── app.py              # Flask应用和REST API
│   ├── db.py               # 数据库连接与初始化
│   ├── schema.sql          # 数据表和索引
│   ├── seed.py             # 模拟数据生成脚本
│   └── data/
│       └── tickets.db      # 运行种子脚本后生成
├── frontend/
│   ├── src/
│   │   ├── components/     # 看板、列表、表单和详情组件
│   │   ├── api.js          # 接口封装
│   │   ├── App.vue
│   │   └── styles.css
│   └── package.json
├── docs/                   # 需求、数据库、API和测试文档
├── tests/                  # 后端自动化测试
├── requirements.txt
└── run.py                  # 单端口启动入口
```

## 快速启动

### 1. 准备环境

需要安装：

- Python 3.11或更高版本
- Node.js 20或更高版本
- Git

### 2. 安装后端依赖

macOS/Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell：

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. 生成模拟数据

```bash
python -m backend.seed --database backend/data/tickets.db --count 220
```

该命令会重新生成数据库。请勿将其用于保存真实数据的数据库。

### 4. 安装并构建前端

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. 启动完整系统

```bash
python run.py
```

浏览器打开：`http://127.0.0.1:5000`

构建前端后，Flask会同时提供网页和API，因此演示时只需启动一个服务。

## 开发模式

终端一：

```bash
python -m backend.app
```

终端二：

```bash
cd frontend
npm run dev
```

浏览器打开：`http://127.0.0.1:5173`

Vite会把`/api`请求转发到5000端口。

## 自动化测试

```bash
pytest -q
```

当前覆盖：

- 健康检查与基础配置
- 工单分页和筛选
- 工单创建
- 正常状态流转
- 非法状态流转拦截
- 看板总数与状态分组核对

## 文档

- [产品需求说明](docs/PRD.md)
- [数据库设计](docs/database-design.md)
- [API接口说明](docs/API.md)
- [测试用例](docs/test-cases.md)
- [面试讲解提纲](docs/interview-guide.md)

## 当前范围与限制

这是校招作品集项目，不是生产系统。目前未实现：

- 真实账户登录和企业单点登录
- 邮件、短信或企业微信通知
- 文件上传和附件安全扫描
- 多租户数据隔离
- 生产级审计、限流和权限模型

在面试中应明确说明这些限制，并介绍如果进入生产环境会如何补充。

