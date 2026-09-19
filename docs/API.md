# API接口说明

基础地址：`http://127.0.0.1:5000/api`

所有提交数据使用JSON格式。

## 基础接口

| 方法 | 地址 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/meta` | 获取状态、优先级、部门、类型及演示用户 |
| GET | `/dashboard` | 获取运营看板数据 |

## 工单接口

| 方法 | 地址 | 说明 |
|---|---|---|
| GET | `/tickets` | 查询工单列表 |
| POST | `/tickets` | 创建工单 |
| GET | `/tickets/{id}` | 获取工单及日志 |
| PATCH | `/tickets/{id}` | 更新基础信息 |
| POST | `/tickets/{id}/transition` | 变更状态 |

## 查询参数

`GET /tickets`支持：

- `search`
- `status`
- `priority`
- `department`
- `category`
- `page`
- `per_page`

示例：

```text
GET /api/tickets?status=IN_PROGRESS&priority=HIGH&page=1&per_page=20
```

## 创建工单

```json
{
  "title": "供应链数据导入失败",
  "description": "导入CSV时报字段格式错误",
  "department": "供应链部",
  "category": "数据问题",
  "priority": "HIGH",
  "requester_id": 5
}
```

成功返回HTTP 201及创建后的工单。

## 状态变更

```json
{
  "status": "RESOLVED",
  "assignee_id": 2,
  "operator_id": 2,
  "resolution": "修正日期格式后重新导入成功",
  "note": "已由提交人验证"
}
```

服务端校验合法状态流转。非法跳转返回HTTP 400。

## 错误格式

```json
{
  "error": "缺少必填字段",
  "details": ["title", "description"]
}
```

