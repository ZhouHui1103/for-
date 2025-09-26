# JSON定义规范与模板

**版本**: 1.1

| 版本 | 日期       | 修改人 | 备注 |
| :--- | :--- | :--- | :--- |
| 1.1 | YYYY-MM-DD | @SiliconLuo | 根据TASK-002，添加版本日志系统。 |
| 1.0 | (初始日期) | @SiliconLuo | 初始版本 |

---

### 一、JSON定义规范

这份规范旨在为“业务对象”、“角色”和“场域”提供一个标准的、机器可读的数据结构。其最终产物是一个完整的JSON文件，该文件包含一个组织内所有核心业务的元定义。

#### **总体结构**

输出的JSON文件应有一个根对象，包含三个顶级键：`objects`、 `roles` 和 `fields`。这三个键的值都是数组。

```json
{
  "objects": [
    // ... 所有对象定义的JSON对象
  ],
  "roles": [
    // ... 所有角色定义的JSON对象
  ],
  "fields": [
    // ... 所有场域定义的JSON对象
  ]
}
```

---

#### **对象 (Object) JSON 结构规范**

每个对象数组中的元素都是一个JSON对象，其键名和数据类型应遵循以下规范，这与我们之前定义的Markdown规范一一对应。

| Markdown项 | JSON键名 | 数据类型 | 备注 |
| :--- | :--- | :--- | :--- |
| 对象名称 | `name` | `String` | 对象的唯一标识符。 |
| 概述 | `overview` | `String` | 一句话精准定义。 |
| 属性 | `attributes` | `Object` | 包含对象所有内在特征的集合。 |
| ├─ 存续性 | `persistence` | `String` | 枚举值: "短期" 或 "长续"。 |
| ├─ 主动性 | `agency` | `String` | 枚举值: "状态变量" 或 "被动承接"。 |
| ├─ 目标性 | `hasGoal` | `Boolean` | `true` 或 `false`。 |
| ├─ 任务性 | `isTask` | `Boolean` | `true` 或 `false`。 |
| ├─ 其他属性| `otherAttributes`| `Array<String>` | 例如: `["定期触发", "版本管理"]`。 |
| 状态 | `statusFlow` | `Array<String>` | 按顺序描述状态流转，例如: `["待分配", "交付中", "已结束"]`。 |
| 类别 | `categories` | `Array<Object>`| 包含多个分类维度，每个维度是一个对象 `{"dimension": "名称", "options": ["选项1", "选项2"]}`。|
| 角色关系 | `roleRelationships`| `Object` | 键值对，例如: `{"maintainer": "角色A", "executor": "角色B"}`。 |
| 关联关系 | `relations` | `Object` | 包含所有关联信息的集合。 |
| ├─ 关联对象 | `relatedObjects` | `Array<String>` | 关联的其他对象的`name`列表。 |
| ├─ 关联场域 | `relatedFields` | `Array<String>` | 关联的场域的`name`列表。 |
| ├─ 关联文档 | `relatedDocuments` | `Array<String>` | 关联文档的URL或路径列表。 |
| ├─ 关联报表 | `relatedReports` | `Array<String>` | 关联报表的名称列表。 |
| 数据字段 | `dataFields` | `Array<Object>`| 每个字段是一个对象 `{"name": "字段名", "type": "数据类型", "formula": "计算公式(可选)"}`。|
| 储存位置 | `storageLocation` | `String` | 关联的`数据表`类型场域的`name`。|

---

#### **场域 (Field) JSON 结构规范**

每个场域数组中的元素都是一个JSON对象，其键名和数据类型如下：

| Markdown项 | JSON键名 | 数据类型 | 备注 |
| :--- | :--- | :--- | :--- |
| 场域名称 | `name` | `String` | 场域的唯一名称。 |
| 场域类型 | `type` | `String` | 枚举值: "群聊", "文档", "数据表"。 |
| 概述 | `overview` | `String` | 一句话核心功能描述。 |
| 详细信息 | `details` | `Object` | 包含该类型场域的特定信息。 |
| ├─ (数据表)类型 | `tableType` | `String` | `type`为"数据表"时填写，枚举值: "总表", "子表"。 |
| ├─ (数据表)关联对象 | `relatedObject` | `String` | `tableType`为"子表"时填写，关联对象的`name`。 |
| ├─ (群聊)平台 | `platform` | `String` | `type`为"群聊"时填写，如: "微信", "飞书"。 |
| ├─ (文档/数据表)链接 | `url` | `String` | `type`为"文档"或"数据表"时填写，指向资源的链接。 |

---

#### **角色 (Role) JSON 结构规范**

每个角色数组中的元素都是一个JSON对象，其键名 и数据类型如下：

| Markdown项 | JSON键名 | 数据类型 | 备注 |
| :--- | :--- | :--- | :--- |
| 外部角色 | `externalName` | `String` | 角色的唯一外部名称。 |
| 内部细分角色| `internalDivisions`| `Array<String>` | 内部细分角色列表。 |
| 角色概述 | `overview` | `String` | 一句话核心价值定位。 |
| 核心权责 | `coreResponsibilities`| `Object` | 包含职责范围的集合。 |
| ├─ 负责对象 | `responsibleObjects` | `Array<Object>` | 每个对象包含 `{"objectName": "对象名", "duties": "职责描述"}`。 |
| ├─ 负责流程 | `responsibleFlows` | `Array<Object>` | 每个对象包含 `{"flowName": "流程名", "roleInFlow": "承担的角色"}`。 |
| 生命周期 | `lifecycle` | `Object` | 包含角色生命周期管理的集合。 |
| ├─ 招募与考核| `recruitment` | `String` | 招募和考核标准的简述。 |
| ├─ 培训与成长| `training` | `String` | 培训路径和成长要求的简述。 |
| ├─ 薪酬绩效 | `compensationLogic`| `String` | 薪酬绩效核心逻辑的简述。 |

---

### 二、JSON定义模板

这是一个可以直接复制和修改的完整JSON模板，它遵循了上述所有规范。

```json
{
  "objects": [
    {
      "name": "服务进程",
      "overview": "一次完整的客户服务交付过程，记录了从开始到结束的所有关键信息。",
      "attributes": {
        "persistence": "长续",
        "agency": "状态变量",
        "hasGoal": true,
        "isTask": false,
        "otherAttributes": []
      },
      "statusFlow": [
        "待开启",
        "进程中",
        "已结束"
      ],
      "categories": [
        {
          "dimension": "服务类型",
          "options": ["ADHD督导", "个人成长咨询"]
        }
      ],
      "roleRelationships": {
        "maintainer": "支撑运营",
        "executor": "督导师",
        "responsible": "培训师",
        "auditor": "培训师"
      },
      "relations": {
        "relatedObjects": [
          "订单信息",
          "客户信息",
          "每日计划"
        ],
        "relatedFields": [
          "全域跟踪总表",
          "客户服务群",
          "L3-2.0-核心服务交付流程"
        ],
        "relatedDocuments": [
          "/docs/SOP/3.1-服务交付流程.md"
        ],
        "relatedReports": [
          "服务质量周报"
        ]
      },
      "dataFields": [
        {
          "name": "服务进程ID",
          "type": "UUID",
          "formula": null
        },
        {
          "name": "开启时间",
          "type": "Timestamp",
          "formula": null
        },
        {
          "name": "复购率",
          "type": "Percentage",
          "formula": "（总复购订单数 / 首次订单数）* 100"
        }
      ],
      "storageLocation": "全域跟踪总表"
    }
  ],
  "roles": [
    {
      "externalName": "督导师",
      "internalDivisions": [
        "白班督导师",
        "晚班督导师"
      ],
      "overview": "完成全部具体交付服务流程，是服务质量的核心保障者。",
      "coreResponsibilities": {
        "responsibleObjects": [
          {
            "objectName": "服务进程",
            "duties": "负责将服务进程的状态从“进程中”推进至“已结束”。"
          },
          {
            "objectName": "每日计划",
            "duties": "负责每日计划的创建、跟踪和数据录入。"
          }
        ],
        "responsibleFlows": [
          {
            "flowName": "L3-服务交付流程",
            "roleInFlow": "执行角色"
          }
        ]
      },
      "lifecycle": {
        "recruitment": "要求有耐心、责任心，通过业务知识笔试和模拟场景面试。",
        "training": "为期3天的线上集中培训，考核通过后进入为期1周的实习期。",
        "compensationLogic": "薪酬由“基础服务费”和“绩效奖金”构成，绩效与所负责的‘服务进程’对象的‘客户满意度’和‘复购率’指标挂钩。"
      }
    }
  ],
  "fields": [
    {
      "name": "全域跟踪总表",
      "type": "数据表",
      "overview": "跟踪所有核心业务对象宏观状态的全局索引。",
      "details": {
        "tableType": "总表",
        "url": "https://docs.google.com/spreadsheets/d/xxxx"
      }
    },
    {
      "name": "客户服务群",
      "type": "群聊",
      "overview": "用于督导师、培训师与客户直接沟通的即时消息群。",
      "details": {
        "platform": "微信"
      }
    },
    {
      "name": "L3-2.0-核心服务交付流程",
      "type": "文档",
      "overview": "定义了核心服务交付过程中的标准操作程序（SOP）。",
      "details": {
        "url": "/SOP_L/ADHD-Process/L3 - 2.0 核心服务交付流程.md"
      }
    }
  ]
}
``` 