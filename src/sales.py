import json
from db import get_connection, execute_query, execute_update

def login_sales_consultant():
    employee_code = input("请输入您的工号: ").strip()
    _, rows = execute_query(
        "SELECT employee_id, name, employee_code, role, department "
        "FROM employee WHERE employee_code = %s AND role = '销售顾问'",
        (employee_code,),
    )
    if not rows:
        print("登录失败：工号不存在或非销售顾问角色。")
        return None
    emp = rows[0]
    print(f"登录成功！欢迎 {emp[1]}（{emp[3]}）\n")
    return {"employee_id": emp[0], "name": emp[1], "employee_code": emp[2]}

def create_intention(consultant_id):
    print("\n=== 创建意向客户 ===")
    name = input("客户姓名: ").strip()
    gender = input("性别（男/女）: ").strip()
    phone = input("手机号: ").strip()
    address = input("家庭地址（可选）: ").strip() or None
    first_visit = input("首次到店日期（YYYY-MM-DD，默认今天）: ").strip()

    if not name or not phone:
        print("姓名和手机号为必填项。")
        return

    _, rows = execute_query(
        "SELECT customer_id FROM customer WHERE phone = %s", (phone,)
    )
    if rows:
        customer_id = rows[0][0]
        print(f"客户已存在，customer_id={customer_id}")
    else:
        if not first_visit:
            first_visit = None
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO customer (name, gender, phone, address, first_visit_date) "
                    "VALUES (%s, %s, %s, %s, COALESCE(%s::DATE, CURRENT_DATE)) "
                    "RETURNING customer_id",
                    (name, gender, phone, address, first_visit),
                )
                customer_id = cur.fetchone()[0]
            conn.commit()
            print(f"新客户创建成功，customer_id={customer_id}")
        except Exception as e:
            conn.rollback()
            print(f"创建客户失败: {e}")
            return
        finally:
            conn.close()

    print("\n--- 可意向车型 ---")
    _, models = execute_query(
        "SELECT model_id, brand_name, series_name, config_name, guide_price "
        "FROM car_model cm JOIN brand b ON cm.brand_id = b.brand_id ORDER BY model_id"
    )
    for m in models:
        print(f"  [{m[0]}] {m[1]} {m[2]} {m[3]} 指导价¥{m[4]:,.0f}")
    model_id = input("意向车型ID（可留空）: ").strip()
    model_id = int(model_id) if model_id else None

    level = input("意向级别（高/中/低，默认:中）: ").strip() or "中"
    remarks = input("备注: ").strip() or None
    next_time = input("下次联系时间（YYYY-MM-DD HH:MI，可留空）: ").strip() or None

    try:
        cnt = execute_update(
            "INSERT INTO customer_intention "
            "(customer_id, intended_model_id, intention_level, remarks, "
            " follow_up_consultant_id, next_contact_time) "
            "VALUES (%s, %s, %s, %s, %s, %s::TIMESTAMP)",
            (customer_id, model_id, level, remarks, consultant_id, next_time),
        )
        print(f"意向记录创建成功，影响行数: {cnt}")
    except Exception as e:
        print(f"创建意向失败: {e}")


def create_sales_order(consultant_id):

    print("\n=== 创建销售订单 ===")

    phone = input("客户手机号: ").strip()
    _, rows = execute_query(
        "SELECT customer_id, name FROM customer WHERE phone = %s", (phone,)
    )
    if not rows:
        print("客户不存在，请先创建客户资料。")
        return
    customer_id, customer_name = rows[0]
    print(f"客户: {customer_name} (ID={customer_id})")

    vin = input("车辆VIN码: ").strip()
    _, rows = execute_query(
        "SELECT iv.vin, cm.series_name, cm.config_name, iv.color, iv.status "
        "FROM inventory_vehicle iv JOIN car_model cm ON iv.model_id = cm.model_id "
        "WHERE iv.vin = %s",
        (vin,),
    )
    if not rows:
        print("车辆VIN不存在。")
        return
    _, series, config, color, status = rows[0]
    print(f"车辆: {series} {config} ({color}) 状态: {status}")
    if status != "在库":
        print(f"该车辆当前状态为「{status}」，无法创建订单（必须为「在库」状态）。")
        return

    deposit = input("定金金额: ").strip()
    deposit = float(deposit) if deposit else 0.0

    print("\n--- 录入订单明细（逐条添加，空描述结束）---")
    details = []
    while True:
        desc = input("  项目描述（回车结束）: ").strip()
        if not desc:
            break
        dtype = input("  明细类型（车款/保险/上牌费/选装配件/折扣等）: ").strip()
        amount = input("  金额（折扣填负数）: ").strip()
        try:
            details.append({"detail_type": dtype, "description": desc, "amount": float(amount)})
        except ValueError:
            print("  金额格式错误，跳过该项。")
    if not details:
        print("至少需要一条订单明细，操作取消。")
        return

    details_json = json.dumps(details, ensure_ascii=False)
    print(f"\n明细: {details_json}")

    confirm = input("\n确认创建订单？(y/n): ").strip().lower()
    if confirm != "y":
        print("已取消。")
        return

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT sp_create_sales_order(%s, %s, %s, %s, %s::JSON)",
                (customer_id, consultant_id, vin, deposit, details_json),
            )
            order_id = cur.fetchone()[0]
        conn.commit()
        print(f"\n订单创建成功！订单号: {order_id}")
    except Exception as e:
        conn.rollback()
        print(f"订单创建失败: {e}")
    finally:
        conn.close()


def query_my_orders(consultant_id):
    print("\n=== 查询我的订单 ===")
    status_filter = input("按状态筛选（已锁定/已付定金/已完成/已取消/待定，回车=全部）: ").strip()

    sql = (
        "SELECT so.order_id, c.name AS customer, iv.vin, "
        "       b.brand_name, cm.series_name, cm.config_name, "
        "       so.total_amount, so.deposit_amount, so.order_status, "
        "       so.created_time, so.delivery_time "
        "FROM sales_order so "
        "JOIN customer c ON so.customer_id = c.customer_id "
        "JOIN inventory_vehicle iv ON so.vin = iv.vin "
        "JOIN car_model cm ON iv.model_id = cm.model_id "
        "JOIN brand b ON cm.brand_id = b.brand_id "
        "WHERE so.sales_consultant_id = %s"
    )
    params = [consultant_id]
    if status_filter:
        sql += " AND so.order_status = %s"
        params.append(status_filter)
    sql += " ORDER BY so.created_time DESC"

    _, rows = execute_query(sql, tuple(params))
    if not rows:
        print("没有找到订单。")
        return

    print(f"\n共 {len(rows)} 条订单：")
    print("-" * 120)
    print(f"{'单号':<5} {'客户':<10} {'VIN':<20} {'车型':<28} {'金额':>10} {'定金':>8} {'状态':<8} {'创建时间'}")
    print("-" * 120)
    for r in rows:
        oid, cust, vin, brand, series, cfg, total, deposit, st, ct, dt = r
        car_info = f"{brand}-{series} {cfg}" if brand else f"{series} {cfg}"
        print(
            f"{oid:<5} {cust:<10} {vin:<20} {car_info:<28} "
            f"{total:>10,.0f} {deposit:>8,.0f} {st:<8} {str(ct)[:19]}"
        )


def sales_front_desk():
    user = login_sales_consultant()
    if not user:
        return

    while True:
        print(f"\n{'='*50}")
        print(f"  销售前台 — 当前用户: {user['name']}")
        print(f"{'='*50}")
        print("  1. 创建意向客户")
        print("  2. 创建销售订单")
        print("  3. 查询我的订单")
        print("  0. 返回主菜单")
        choice = input("请选择: ").strip()

        if choice == "1":
            create_intention(user["employee_id"])
        elif choice == "2":
            create_sales_order(user["employee_id"])
        elif choice == "3":
            query_my_orders(user["employee_id"])
        elif choice == "0":
            break
        else:
            print("无效选项，请重新输入。")
