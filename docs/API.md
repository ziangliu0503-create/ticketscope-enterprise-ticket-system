# API 接口说明

本地基础地址：`http://127.0.0.1:5000/api`。除健康检查和登录外，接口需携带：

```http
Authorization: Bearer <登录返回的 token>
```

## 接口总览

| 方法 | 地址 | 权限 | 说明 |
|---|---|---|---|
| GET | `/health` | 公开 | 健康检查 |
| POST | `/auth/login` | 公开 | 邮箱密码登录 |
| GET | `/auth/me` | 已登录 | 当前用户 |
| GET | `/meta` | 已登录 | 枚举、SLA 配置、可见用户 |
| GET | `/tickets` | 已登录 | 查询权限范围内工单 |
| POST | `/tickets` | 普通员工/管理员 | 创建工单 |
| GET | `/tickets/{id}` | 有数据权限 | 详情、日志、可执行操作 |
| PATCH | `/tickets/{id}` | 技术人员/管理员 | 编辑工单 |
| POST | `/tickets/{id}/transition` | 按角色与状态 | 状态流转 |
| POST | `/tickets/{id}/escalate` | 管理员 | 升级超时工单 |
| GET | `/dashboard` | 已登录 | 当前数据范围看板 |
| GET | `/reports/tickets.csv` | 已登录 | 导出筛选结果 |
| GET | `/reports/tickets.xlsx` | 已登录 | 导出筛选结果 |

## 登录

```json
POST /api/auth/login
{
  "email": "ziang.liu@example.com",
  "password": "Demo123!"
}
```

返回 `token` 和脱敏后的 `user`。令牌默认有效 86400 秒，可通过 `AUTH_TOKEN_MAX_AGE` 调整。

## 查询工单

支持 `search`、`status`、`priority`、`department`、`category`、`sla`、`page` 和 `per_page`。`sla` 可取 `WARNING`、`OVERDUE`、`ESCALATED`。

```text
GET /api/tickets?priority=HIGH&sla=OVERDUE&page=1&per_page=20
```

## 创建与流转

普通员工无需也不能指定 `requester_id`；管理员代建时必须指定。

```json
POST /api/tickets
{
  "title": "供应链数据导入失败",
  "description": "导入 CSV 时报日期字段错误",
  "department": "供应链部",
  "category": "数据问题",
  "priority": "HIGH"
}
```

```json
POST /api/tickets/23/transition
{
  "status": "RESOLVED",
  "resolution": "修正日期格式后重新导入成功",
  "note": "已完成回归验证"
}
```

管理员分派时可传 `assignee_id`；技术人员认领待受理工单时系统自动把当前用户设为负责人。

## 错误格式

```json
{
  "error": "缺少必填字段",
  "details": ["title", "description"]
}
```

常见状态码：`400` 参数或业务规则错误，`401` 未登录/令牌失效，`403` 权限不足，`404` 不存在或无权查看。

