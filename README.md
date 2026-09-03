# 基于数据库的汽车销售管理系统

一个基于 **OpenGauss** 和 **Python** 的汽车销售与库存管理系统，实现对汽车经销商的核心业务流程的信息化管理。

## 功能模块

### 1. 销售前台
- **客户管理**：创建客户资料，记录客户意向及意向级别
- **销售订单**：基于 VIN 码创建销售订单，支持多明细录入（车款、保险、上牌费、选装配件、折扣等）
- **订单查询**：按状态筛选销售顾问自己的订单

### 2. 库存管理
- **车辆入库**：录入新车 VIN、车型、颜色、采购成本、建议零售价等信息
- **多条件查询**：支持按 VIN、状态、品牌、车型、颜色、入库日期范围等条件筛选
- **库存预警**：基于安全库阈值展示库存不足车型，提示补货

### 3. 报表中心
- **销售业绩榜**：按销售额降序展示所有销售顾问的业绩
- **畅销车型排行**：按销量统计畅销车型 Top N
- **月度销售统计**：按月汇总各品牌/车系的订单数、销售额、毛利

### 4. 数据查询中心
- **Q1** 指定时间段销售统计（订单数、销售额、毛利）
- **Q2** 销售顾问业绩排名（含 RANK 窗口函数）
- **Q3** 最畅销车型 Top N
- **Q4** 滞销车辆清单（库存周期超阈值）
- **Q5** 客户价值分类（金卡/银卡/普通客户）
- **Q6** 客户购车及服务历史（UNION ALL 联合查询）
- **Q7** 库存预警报表
- **Q8** 品牌销售占比及毛利率分析（含窗口函数）

## 数据库设计

系统包含 **10 张核心表**：

| 表名 | 说明 |
|------|------|
| `brand` | 品牌表 |
| `car_model` | 车型表 |
| `inventory_vehicle` | 库存车辆表（VIN 主键） |
| `employee` | 员工表（含自引用 supervisor_id） |
| `customer` | 客户表 |
| `customer_intention` | 客户意向表 |
| `sales_order` | 销售订单表 |
| `order_detail` | 订单明细表 |
| `service_order` | 服务工单表 |
| `service_detail` | 服务明细表 |

### 数据库对象
- **3 个视图**：`v_sales_performance`、`v_inventory_summary`、`v_customer_value`
- **2 个触发器**：
  - `trg_lock_car_on_order`：创建订单时自动锁定车辆
  - `trg_update_inventory_on_delivery`：订单完成时自动将车辆标记为已售出
- **2 个存储过程**：
  - `sp_create_sales_order`：创建销售订单（含 JSON 明细解析）
  - `sp_get_monthly_report`：按月汇总销售统计（含 ROLLUP 合计行）
- **索引**（`04_indexes.sql`）：为高频查询字段建立索引优化性能

## 项目结构

```
database_work/
├── sql/
│   ├── 01_create_schema.sql   # 建表 DDL
│   ├── 02_init_data.sql       # 初始数据
│   ├── 03_views.sql           # 视图定义
│   ├── 04_indexes.sql         # 索引定义
│   ├── 05_triggers.sql        # 触发器定义
│   ├── 06_procedures.sql      # 存储过程定义
│   └── 07_queries.sql         # 查询 SQL
├── src/
│   ├── config.py              # 数据库连接配置
│   ├── db.py                  # 数据库工具（连接、查询、事务管理）
│   ├── main.py                # 主入口（菜单导航）
│   ├── sales.py               # 销售前台模块
│   ├── inventory.py           # 库存管理模块
│   ├── reports.py             # 报表中心模块
│   └── queries.py             # 数据查询中心模块（Q1-Q8）
├── doc/
│   ├── 数据库设计说明书.pdf
│   ├── 测试文档.pdf
│   └── 课程设计报告.pdf
└── README.md
```

## 运行环境

- **数据库**：OpenGauss
- **Python**：3.8+
- **依赖**：`pg8000`

## 快速开始

1. 在 PostgreSQL 中创建数据库并执行 SQL 脚本：

```bash
psql -h <host> -p <port> -U <user> -d car_sales -f sql/01_create_schema.sql
psql -h <host> -p <port> -U <user> -d car_sales -f sql/02_init_data.sql
psql -h <host> -p <port> -U <user> -d car_sales -f sql/03_views.sql
psql -h <host> -p <port> -U <user> -d car_sales -f sql/04_indexes.sql
psql -h <host> -p <port> -U <user> -d car_sales -f sql/05_triggers.sql
psql -h <host> -p <port> -U <user> -d car_sales -f sql/06_procedures.sql
```

2. 修改 `src/config.py` 中的数据库连接参数：

```python
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 26000,
    "database": "数据库名称",
    "user": "用户名称",
    "password": "自己设置的密码",
}
```

3. 安装依赖并运行：

```bash
pip install pg8000
python src/main.py
```

4. 按终端菜单提示选择功能模块进行操作。
