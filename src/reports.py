from db import execute_query, call_procedure


def sales_performance():
    print("\n=== 销售顾问业绩榜 ===")
    print("（仅统计「已完成」订单）\n")

    _, rows = execute_query(
        "SELECT consultant_name, employee_code, department, "
        "       total_orders, total_sales_amount, total_profit "
        "FROM v_sales_performance "
        "ORDER BY total_sales_amount DESC"
    )
    if not rows:
        print("暂无业绩数据。")
        return

    print(f"{'排名':<5} {'姓名':<10} {'工号':<8} {'部门':<8} {'订单数':>6} {'销售额':>14} {'毛利':>14}")
    print("-" * 70)
    for idx, r in enumerate(rows, 1):
        name, code, dept, orders, sales, profit = r
        print(
            f"{idx:<5} {name:<10} {code:<8} {dept:<8} "
            f"{orders:>6} {sales:>14,.0f} {profit:>14,.0f}"
        )


def top_models():

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
        "JOIN sales_order so ON iv.vin = so.vin "
        "WHERE so.order_status = '已完成' "
        "GROUP BY b.brand_name, cm.series_name, cm.config_name, cm.year_model, cm.guide_price "
        "ORDER BY sales_count DESC "
        "LIMIT %s"
    )

    print(f"\n=== 畅销车型 Top {top_n} ===")
    _, rows = execute_query(sql, (top_n,))
    if not rows:
        print("暂无销售数据。")
        return

    print(f"{'排名':<5} {'品牌':<6} {'车系':<8} {'配置':<16} {'年款':<8} {'指导价':>10} {'销量':>6} {'销售额':>14}")
    print("-" * 85)
    for idx, r in enumerate(rows, 1):
        brand, series, cfg, year, price, cnt, sales = r
        print(
            f"{idx:<5} {brand:<6} {series:<8} {cfg:<16} {year:<8} "
            f"{price:>10,.0f} {cnt:>6} {sales:>14,.0f}"
        )


def monthly_report():

    year = input("年份（如2026）: ").strip()
    month = input("月份（1-12）: ").strip()

    try:
        year, month = int(year), int(month)
    except ValueError:
        print("年份或月份格式错误。")
        return

    print(f"\n=== {year}年{month}月 销售统计报表 ===")

    _, rows = call_procedure("sp_get_monthly_report", [year, month])
    if not rows:
        print("该月无已完成的销售数据。")
        return

    print(f"\n{'品牌/合计':<12} {'车系':<10} {'订单数':>6} {'销售额':>14} {'毛利':>14} {'顾问数':>6}")
    print("-" * 65)
    for r in rows:
        brand, series, cnt, sales, profit, consultants = r
        series = series or ""
        print(
            f"{brand:<12} {series:<10} {cnt:>6} {sales:>14,.0f} "
            f"{profit:>14,.0f} {consultants:>6}"
        )

def report_center():
    while True:
        print(f"\n{'='*50}")
        print("  报表中心")
        print(f"{'='*50}")
        print("  1. 查询销售业绩榜")
        print("  2. 查询畅销车型排行")
        print("  3. 生成月度销售统计")
        print("  0. 返回主菜单")
        choice = input("请选择: ").strip()

        if choice == "1":
            sales_performance()
        elif choice == "2":
            top_models()
        elif choice == "3":
            monthly_report()
        elif choice == "0":
            break
        else:
            print("无效选项，请重新输入。")
