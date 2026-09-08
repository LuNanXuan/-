from db import execute_query


def q1_sales_stats():
    print("\n=== Q1: 指定时间段销售统计 ===")
    start = input("开始日期（YYYY-MM-DD，默认 2026-01-01）: ").strip() or "2026-01-01"
    end = input("结束日期（YYYY-MM-DD，默认 2026-03-31）: ").strip() or "2026-03-31"

    sql = (
        "SELECT COUNT(so.order_id) AS total_orders, "
        "       COALESCE(SUM(so.total_amount), 0) AS total_sales, "
        "       COALESCE(SUM(so.total_amount - iv.purchase_cost), 0) AS total_profit "
        "FROM sales_order so "
        "JOIN inventory_vehicle iv ON so.vin = iv.vin "
        "WHERE so.order_status = '已完成' "
        "  AND so.delivery_time >= %s::DATE "
        "  AND so.delivery_time <  %s::DATE + INTERVAL '1 day'"
    )
    _, rows = execute_query(sql, (start, end))
    if rows:
        orders, sales, profit = rows[0]
        print(f"\n时间段: {start} ~ {end}")
        print(f"  总订单数: {orders}")
        print(f"  总销售额: ¥{sales:,.0f}")
        print(f"  总毛利:   ¥{profit:,.0f}")


def q2_consultant_ranking():
    print("\n=== Q2: 销售顾问业绩排名 ===")
    start = input("开始日期（YYYY-MM-DD，默认 2026-01-01）: ").strip() or "2026-01-01"
    end = input("结束日期（YYYY-MM-DD，默认 2026-03-31）: ").strip() or "2026-03-31"

    sql = (
        "SELECT RANK() OVER (ORDER BY COALESCE(SUM(so.total_amount), 0) DESC) AS rank, "
        "       e.name AS consultant_name, e.employee_code, "
        "       COUNT(so.order_id) AS order_count, "
        "       COALESCE(SUM(so.total_amount), 0) AS total_sales, "
        "       COALESCE(SUM(so.total_amount - iv.purchase_cost), 0) AS total_profit "
        "FROM employee e "
        "LEFT JOIN sales_order so "
        "    ON e.employee_id = so.sales_consultant_id "
        "    AND so.order_status = '已完成' "
        "    AND so.delivery_time >= %s::DATE "
        "    AND so.delivery_time <  %s::DATE + INTERVAL '1 day' "
        "LEFT JOIN inventory_vehicle iv ON so.vin = iv.vin "
        "WHERE e.role = '销售顾问' "
        "GROUP BY e.employee_id, e.name, e.employee_code "
        "ORDER BY total_sales DESC"
    )
    _, rows = execute_query(sql, (start, end))
    if not rows:
        print("该时间段暂无业绩数据。")
        return

    print(f"\n时间段: {start} ~ {end}")
    print(f"{'排名':<5} {'姓名':<10} {'工号':<8} {'订单数':>6} {'销售额':>14} {'毛利':>14}")
    print("-" * 62)
    for r in rows:
        rank, name, code, orders, sales, profit = r
        print(f"{rank:<5} {name:<10} {code:<8} {orders:>6} {sales:>14,.0f} {profit:>14,.0f}")


def q3_top_models():
    print("\n=== Q3: 最畅销车型 Top 5 ===")
    top_n = input("显示前几名？（默认5）: ").strip()
    try:
        top_n = int(top_n) if top_n else 5
    except ValueError:
        top_n = 5

    sql = (
        "SELECT b.brand_name, cm.series_name, cm.config_name, cm.year_model, "
        "       cm.guide_price, COUNT(so.order_id) AS sales_count, "
        "       COALESCE(SUM(so.total_amount), 0) AS total_sales "
        "FROM car_model cm "
        "JOIN brand b ON cm.brand_id = b.brand_id "
        "JOIN inventory_vehicle iv ON cm.model_id = iv.model_id "
        "JOIN sales_order so ON iv.vin = so.vin AND so.order_status = '已完成' "
        "GROUP BY b.brand_name, cm.series_name, cm.config_name, cm.year_model, "
        "         cm.guide_price, cm.model_id "
        "ORDER BY sales_count DESC LIMIT %s"
    )
    _, rows = execute_query(sql, (top_n,))
    if not rows:
        print("暂无销售数据。")
        return

    print(f"\n{'排名':<5} {'品牌':<6} {'车系':<8} {'配置':<16} {'年款':<8} {'指导价':>10} {'销量':>6} {'销售额':>14}")
    print("-" * 78)
    for idx, r in enumerate(rows, 1):
        brand, series, cfg, year, price, cnt, sales = r
        print(f"{idx:<5} {brand:<6} {series:<8} {cfg:<16} {year:<8} {price:>10,.0f} {cnt:>6} {sales:>14,.0f}")


def q4_slow_moving():
    print("\n=== Q4: 滞销车辆清单（库存周期 > 90天）===")
    threshold = input("库存周期阈值（天，默认90）: ").strip()
    try:
        threshold = int(threshold) if threshold else 90
    except ValueError:
        threshold = 90

    sql = (
        "SELECT iv.vin, b.brand_name, cm.series_name, cm.config_name, iv.color, "
        "       iv.entry_date, so.delivery_time::DATE AS sold_date, "
        "       (so.delivery_time::DATE - iv.entry_date) AS inventory_days, "
        "       iv.purchase_cost, so.total_amount, "
        "       (so.total_amount - iv.purchase_cost) AS profit "
        "FROM inventory_vehicle iv "
        "JOIN car_model cm ON iv.model_id = cm.model_id "
        "JOIN brand b ON cm.brand_id = b.brand_id "
        "JOIN sales_order so ON iv.vin = so.vin AND so.order_status = '已完成' "
        "WHERE (so.delivery_time::DATE - iv.entry_date) > %s "
        "ORDER BY inventory_days DESC"
    )
    _, rows = execute_query(sql, (threshold,))
    if not rows:
        print(f"没有库存周期超过 {threshold} 天的滞销车辆。")
        return

    print(f"\n{'VIN':<20} {'品牌':<6} {'车系':<8} {'配置':<16} {'颜色':<8} {'入库日期':<12} {'售出日期':<12} {'库存天数':>8} {'成本':>10} {'售价':>10} {'毛利':>10}")
    print("-" * 130)
    for r in rows:
        vin, brand, series, cfg, color, entry, sold, days, cost, price, profit = r
        print(f"{vin:<20} {brand:<6} {series:<8} {cfg:<16} {color:<8} "
              f"{str(entry):<12} {str(sold):<12} {days:>8} "
              f"{cost:>10,.0f} {price:>10,.0f} {profit:>10,.0f}")


def q5_customer_tier():
    print("\n=== Q5: 客户价值分类 ===")
    print("（普通客户 < 10万，银卡客户 10-30万，金卡客户 > 30万）\n")

    _, rows = execute_query(
        "SELECT customer_id, name, phone, total_purchase, total_service, "
        "       total_consumption, customer_tier "
        "FROM v_customer_value "
        "ORDER BY total_consumption DESC"
    )
    if not rows:
        print("暂无客户数据。")
        return

    print(f"{'ID':<4} {'姓名':<10} {'手机号':<14} {'购车消费':>12} {'服务消费':>12} {'总消费':>12} {'等级'}")
    print("-" * 82)
    for r in rows:
        cid, name, phone, purchase, service, total, tier = r
        print(f"{cid:<4} {name:<10} {phone:<14} {purchase:>12,.0f} {service:>12,.0f} {total:>12,.0f} {tier}")


def q6_customer_history():
    print("\n=== Q6: 客户购车及服务历史 ===")
    phone = input("客户手机号: ").strip()
    if not phone:
        print("手机号不能为空。")
        return

    _, cust = execute_query(
        "SELECT customer_id, name FROM customer WHERE phone = %s", (phone,)
    )
    if not cust:
        print("未找到该客户。")
        return
    cid, cname = cust[0]
    print(f"\n客户: {cname} (ID={cid})")

    sql = (
        "SELECT '购车' AS record_type, so.order_id AS record_id, "
        "       so.created_time AS record_time, "
        "       b.brand_name || ' ' || cm.series_name || ' ' || cm.config_name AS detail, "
        "       so.total_amount AS amount, so.order_status AS status "
        "FROM sales_order so "
        "JOIN inventory_vehicle iv ON so.vin = iv.vin "
        "JOIN car_model cm ON iv.model_id = cm.model_id "
        "JOIN brand b ON cm.brand_id = b.brand_id "
        "WHERE so.customer_id = %s "
        "UNION ALL "
        "SELECT '服务' AS record_type, svo.service_order_id AS record_id, "
        "       svo.created_time AS record_time, svo.service_type AS detail, "
        "       svo.total_cost AS amount, svo.status AS status "
        "FROM service_order svo "
        "WHERE svo.customer_id = %s "
        "ORDER BY record_time DESC"
    )
    _, rows = execute_query(sql, (cid, cid))
    if not rows:
        print("该客户暂无购车或服务记录。")
        return

    print(f"\n{'类型':<5} {'记录ID':<8} {'时间':<22} {'详情':<40} {'金额':>12} {'状态'}")
    print("-" * 100)
    for r in rows:
        rtype, rid, rtime, detail, amount, status = r
        print(f"{rtype:<5} {rid:<8} {str(rtime):<22} {detail:<40} {amount:>12,.0f} {status}")


def q7_inventory_alert():
    print("\n=== Q7: 库存预警报表 ===")
    threshold = input("安全库存阈值（默认3）: ").strip()
    try:
        threshold = int(threshold) if threshold else 3
    except ValueError:
        threshold = 3

    _, rows = execute_query(
        "SELECT brand_name, series_name, config_name, year_model, guide_price, "
        "       in_stock, locked, in_transit, total_count "
        "FROM v_inventory_summary "
        "WHERE in_stock < %s "
        "ORDER BY in_stock ASC",
        (threshold,),
    )
    if not rows:
        print(f"所有车型在库数量均 ≥ {threshold}，库存充足。")
        return

    print(f"\n安全阈值: {threshold} 台")
    print(f"{'品牌':<6} {'车系':<8} {'配置':<16} {'年款':<8} {'指导价':>10} {'在库':>5} {'锁定':>5} {'在途':>5} {'合计':>5}")
    print("-" * 85)
    for r in rows:
        brand, series, cfg, year, price, in_stock, locked, transit, total = r
        print(f"{brand:<6} {series:<8} {cfg:<16} {year:<8} {price:>10,.0f} "
              f"{in_stock:>5} {locked:>5} {transit:>5} {total:>5}")


def q8_brand_analysis():
    print("\n=== Q8: 各品牌销售占比及毛利率分析 ===")

    sql = (
        "SELECT b.brand_name, "
        "       COUNT(DISTINCT so.order_id) AS order_count, "
        "       COUNT(DISTINCT iv.vin) AS vehicle_count, "
        "       COALESCE(SUM(so.total_amount), 0) AS total_sales, "
        "       COALESCE(SUM(so.total_amount - iv.purchase_cost), 0) AS total_profit, "
        "       ROUND(COALESCE(SUM(so.total_amount - iv.purchase_cost) * 100.0 "
        "           / NULLIF(SUM(so.total_amount), 0), 0), 2) AS profit_margin_pct, "
        "       ROUND(COALESCE(SUM(so.total_amount) * 100.0 "
        "           / NULLIF(SUM(SUM(so.total_amount)) OVER (), 0), 0), 2) AS sales_share_pct, "
        "       ROUND(COALESCE(AVG(so.total_amount - iv.purchase_cost), 0), 0) AS avg_profit_per_order "
        "FROM brand b "
        "JOIN car_model cm ON b.brand_id = cm.brand_id "
        "JOIN inventory_vehicle iv ON cm.model_id = iv.model_id "
        "JOIN sales_order so ON iv.vin = so.vin AND so.order_status = '已完成' "
        "GROUP BY b.brand_id, b.brand_name "
        "ORDER BY total_sales DESC"
    )
    _, rows = execute_query(sql)
    if not rows:
        print("暂无已完成销售数据。")
        return

    print(f"\n{'品牌':<6} {'订单数':>6} {'售出车辆':>8} {'销售额':>14} {'毛利':>12} {'毛利率%':>8} {'销售占比%':>9} {'均单毛利':>10}")
    print("-" * 82)
    for r in rows:
        brand, orders, vehicles, sales, profit, margin, share, avg = r
        print(f"{brand:<6} {orders:>6} {vehicles:>8} {sales:>14,.0f} {profit:>12,.0f} "
              f"{margin:>8.2f} {share:>9.2f} {avg:>10,.0f}")


def query_center():
    while True:
        print(f"\n{'='*50}")
        print("  数据查询中心（任务四 Q1–Q8）")
        print(f"{'='*50}")
        print("  1. Q1 - 指定时间段销售统计")
        print("  2. Q2 - 销售顾问业绩排名")
        print("  3. Q3 - 最畅销车型 Top N")
        print("  4. Q4 - 滞销车辆清单")
        print("  5. Q5 - 客户价值分类")
        print("  6. Q6 - 客户购车及服务历史")
        print("  7. Q7 - 库存预警报表")
        print("  8. Q8 - 品牌销售占比及毛利率分析")
        print("  0. 返回主菜单")
        choice = input("请选择: ").strip()

        if choice == "1":
            q1_sales_stats()
        elif choice == "2":
            q2_consultant_ranking()
        elif choice == "3":
            q3_top_models()
        elif choice == "4":
            q4_slow_moving()
        elif choice == "5":
            q5_customer_tier()
        elif choice == "6":
            q6_customer_history()
        elif choice == "7":
            q7_inventory_alert()
        elif choice == "8":
            q8_brand_analysis()
        elif choice == "0":
            break
        else:
            print("无效选项，请重新输入。")
