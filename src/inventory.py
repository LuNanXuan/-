from db import execute_query, execute_update
from config import SAFETY_STOCK_THRESHOLD


def vehicle_entry():
    print("\n=== 车辆入库 ===")

    vin = input("VIN码（17位）: ").strip()
    if not vin:
        print("VIN码不能为空。")
        return

    _, rows = execute_query(
        "SELECT vin FROM inventory_vehicle WHERE vin = %s", (vin,)
    )
    if rows:
        print(f"VIN {vin} 已存在于库存中，请勿重复录入。")
        return


    _, models = execute_query(
        "SELECT cm.model_id, b.brand_name, cm.series_name, cm.config_name, cm.guide_price "
        "FROM car_model cm JOIN brand b ON cm.brand_id = b.brand_id ORDER BY cm.model_id"
    )
    print("\n--- 可选车型 ---")
    for m in models:
        print(f"  [{m[0]}] {m[1]} {m[2]} {m[3]} 指导价¥{m[4]:,.0f}")

    model_id = input("车型ID: ").strip()
    color = input("颜色: ").strip()
    production_date = input("生产日期（YYYY-MM-DD）: ").strip() or None
    entry_date = input("入库日期（YYYY-MM-DD，默认今天）: ").strip() or None
    purchase_cost = input("采购成本: ").strip()
    suggested_retail_price = input("建议零售价: ").strip()
    status = input("车辆状态（在库/在途，默认:在途）: ").strip() or "在途"
    if status not in ("在库", "在途"):
        print("状态仅支持「在库」或「在途」，已改为「在途」。")
        status = "在途"

    try:
        cnt = execute_update(
            "INSERT INTO inventory_vehicle "
            "(vin, model_id, color, production_date, entry_date, purchase_cost, "
            " suggested_retail_price, status) "
            "VALUES (%s, %s, %s, %s::DATE, COALESCE(%s::DATE, CURRENT_DATE), %s, %s, %s)",
            (
                vin, int(model_id), color, production_date,
                entry_date, float(purchase_cost), float(suggested_retail_price), status,
            ),
        )
        print(f"车辆入库成功！VIN={vin}，影响行数: {cnt}")
    except Exception as e:
        print(f"入库失败: {e}")


def query_inventory():
    print("\n=== 查询车辆库存 ===")
    print("（回车跳过该筛选条件）")

    conditions = []
    params = []

    vin = input("VIN码（支持模糊）: ").strip()
    if vin:
        conditions.append("iv.vin ILIKE %s")
        params.append(f"%{vin}%")

    status = input("车辆状态（在库/已锁定/已售出/在途）: ").strip()
    if status:
        conditions.append("iv.status = %s")
        params.append(status)

    brand = input("品牌名（支持模糊）: ").strip()
    if brand:
        conditions.append("b.brand_name ILIKE %s")
        params.append(f"%{brand}%")

    model_id = input("车型ID: ").strip()
    if model_id:
        conditions.append("iv.model_id = %s")
        params.append(int(model_id))

    color = input("颜色: ").strip()
    if color:
        conditions.append("iv.color = %s")
        params.append(color)


    entry_from = input("入库日期从（YYYY-MM-DD）: ").strip()
    if entry_from:
        conditions.append("iv.entry_date >= %s::DATE")
        params.append(entry_from)
    entry_to = input("入库日期至（YYYY-MM-DD）: ").strip()
    if entry_to:
        conditions.append("iv.entry_date <= %s::DATE")
        params.append(entry_to)

    where = " AND ".join(conditions) if conditions else "1=1"

    sql = (
        "SELECT iv.vin, b.brand_name, cm.series_name, cm.config_name, cm.year_model, "
        "       iv.color, iv.status, iv.purchase_cost, iv.suggested_retail_price, "
        "       iv.production_date, iv.entry_date "
        "FROM inventory_vehicle iv "
        "JOIN car_model cm ON iv.model_id = cm.model_id "
        "JOIN brand b ON cm.brand_id = b.brand_id "
        f"WHERE {where} "
        "ORDER BY iv.entry_date DESC"
    )

    _, rows = execute_query(sql, tuple(params))
    if not rows:
        print("没有符合条件的车辆。")
        return

    print(f"\n共 {len(rows)} 台车辆：")
    print("-" * 130)
    header = f"{'VIN':<20} {'品牌':<6} {'车系':<8} {'配置':<14} {'年款':<8} {'颜色':<8} {'状态':<8} {'成本':>10} {'售价':>10} {'入库日期'}"
    print(header)
    print("-" * 130)
    for r in rows:
        v, b, s, cfg, y, col, st, cost, price, pd, ed = r
        print(
            f"{v:<20} {b:<6} {s:<8} {cfg:<14} {y:<8} {col:<8} {st:<8} "
            f"{cost:>10,.0f} {price:>10,.0f} {str(ed)}"
        )


def inventory_alert():
    print(f"\n=== 库存预警报表（安全阈值: {SAFETY_STOCK_THRESHOLD} 台）===")

    _, rows = execute_query(
        "SELECT brand_name, series_name, config_name, year_model, guide_price, "
        "       in_stock, locked, in_transit, total_count "
        "FROM v_inventory_summary "
        "ORDER BY in_stock ASC"
    )
    if not rows:
        print("暂无库存数据。")
        return

    warned = [r for r in rows if r[5] is not None and int(r[5]) < SAFETY_STOCK_THRESHOLD]

    print(f"\n{'品牌':<6} {'车系':<8} {'配置':<16} {'年款':<8} {'指导价':>10} {'在库':>5} {'锁定':>5} {'在途':>5} {'合计':>5} {'状态'}")
    print("-" * 100)
    for r in rows:
        brand, series, cfg, year, price, in_stock, locked, transit, total = r
        in_stock = int(in_stock) if in_stock else 0
        locked = int(locked) if locked else 0
        transit = int(transit) if transit else 0
        total = int(total) if total else 0
        alert = "⚠️库存不足" if in_stock < SAFETY_STOCK_THRESHOLD else ""
        print(
            f"{brand:<6} {series:<8} {cfg:<16} {year:<8} {price:>10,.0f} "
            f"{in_stock:>5} {locked:>5} {transit:>5} {total:>5} {alert}"
        )

    if warned:
        print(f"\n共有 {len(warned)} 款车型库存低于阈值 {SAFETY_STOCK_THRESHOLD}，建议尽快补货。")
    else:
        print(f"\n所有车型库存充足（均在 {SAFETY_STOCK_THRESHOLD} 台以上）。")


def inventory_management():
    while True:
        print(f"\n{'='*50}")
        print("  库存管理")
        print(f"{'='*50}")
        print("  1. 车辆入库")
        print("  2. 查询车辆库存（多条件筛选）")
        print("  3. 查看库存预警报表")
        print("  0. 返回主菜单")
        choice = input("请选择: ").strip()

        if choice == "1":
            vehicle_entry()
        elif choice == "2":
            query_inventory()
        elif choice == "3":
            inventory_alert()
        elif choice == "0":
            break
        else:
            print("无效选项，请重新输入。")
