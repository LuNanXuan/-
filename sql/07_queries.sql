-- Q1：查询指定时间段内（2026年第一季度）的销售统计，包括总订单数、总销售额、总毛利。
SELECT
    COUNT(so.order_id) AS total_orders,
    COALESCE(SUM(so.total_amount), 0) AS total_sales,
    COALESCE(SUM(so.total_amount - iv.purchase_cost), 0) AS total_profit
FROM sales_order so
JOIN inventory_vehicle iv ON so.vin = iv.vin
WHERE so.order_status = '已完成'
  AND so.delivery_time >= '2026-01-01'
  AND so.delivery_time < '2026-04-01';

-- Q2：查询每位销售顾问的季度业绩（订单数、销售额、毛利），并进行排名。
SELECT
    RANK() OVER (ORDER BY COALESCE(SUM(so.total_amount), 0) DESC) AS rank,
    e.name AS consultant_name,
    e.employee_code,
    COUNT(so.order_id) AS order_count,
    COALESCE(SUM(so.total_amount), 0) AS total_sales,
    COALESCE(SUM(so.total_amount - iv.purchase_cost), 0) AS total_profit
FROM employee e
LEFT JOIN sales_order so
    ON e.employee_id = so.sales_consultant_id
    AND so.order_status = '已完成'
    AND so.delivery_time >= '2026-01-01'
    AND so.delivery_time < '2026-04-01'
LEFT JOIN inventory_vehicle iv ON so.vin = iv.vin
WHERE e.role = '销售顾问'
GROUP BY e.employee_id, e.name, e.employee_code
ORDER BY total_sales DESC;

-- Q3：查询最畅销的车型Top 5及其销量。
SELECT
    b.brand_name,
    cm.series_name,
    cm.config_name,
    cm.year_model,
    cm.guide_price,
    COUNT(so.order_id) AS sales_count,
    COALESCE(SUM(so.total_amount), 0) AS total_sales
FROM car_model cm
JOIN brand b ON cm.brand_id = b.brand_id
JOIN inventory_vehicle iv ON cm.model_id = iv.model_id
JOIN sales_order so ON iv.vin = so.vin AND so.order_status = '已完成'
GROUP BY b.brand_name, cm.series_name, cm.config_name, cm.year_model,
         cm.guide_price, cm.model_id
ORDER BY sales_count DESC
LIMIT 5;

-- Q4：查询所有“库存周期”（从入库到售出的天数）超过90天的滞销车辆清单。
SELECT
    iv.vin,
    b.brand_name,
    cm.series_name,
    cm.config_name,
    iv.color,
    iv.entry_date,
    so.delivery_time::DATE AS sold_date,
    (so.delivery_time::DATE - iv.entry_date) AS inventory_days,
    iv.purchase_cost,
    so.total_amount,
    (so.total_amount - iv.purchase_cost) AS profit
FROM inventory_vehicle iv
JOIN car_model cm ON iv.model_id = cm.model_id
JOIN brand b ON cm.brand_id = b.brand_id
JOIN sales_order so ON iv.vin = so.vin AND so.order_status = '已完成'
WHERE (so.delivery_time::DATE - iv.entry_date) > 90
ORDER BY inventory_days DESC;

-- Q5：根据客户的历史消费总额，对客户进行分类（普通客户<10万，银卡客户10-30万，金卡客户>30万）。
SELECT
    c.customer_id,
    c.name,
    c.phone,
    COALESCE(p.purchase_total, 0) AS total_purchase,
    COALESCE(s.service_total, 0) AS total_service,
    COALESCE(p.purchase_total, 0) + COALESCE(s.service_total, 0) AS total_consumption,
    CASE
        WHEN COALESCE(p.purchase_total, 0) + COALESCE(s.service_total, 0) >= 300000
            THEN '金卡客户'
        WHEN COALESCE(p.purchase_total, 0) + COALESCE(s.service_total, 0) >= 100000
            THEN '银卡客户'
        ELSE '普通客户'
    END AS customer_tier
FROM customer c
LEFT JOIN (
    SELECT customer_id, SUM(total_amount) AS purchase_total
    FROM sales_order
    WHERE order_status = '已完成'
    GROUP BY customer_id
) p ON c.customer_id = p.customer_id
LEFT JOIN (
    SELECT customer_id, SUM(total_cost) AS service_total
    FROM service_order
    WHERE status = '已完成'
    GROUP BY customer_id
) s ON c.customer_id = s.customer_id
ORDER BY total_consumption DESC;

-- Q6：查询特定客户的完整购车及服务历史。
SELECT
    '购车' AS record_type,
    so.order_id AS record_id,
    so.created_time AS record_time,
    b.brand_name || ' ' || cm.series_name || ' ' || cm.config_name AS detail,
    so.total_amount AS amount,
    so.order_status AS status
FROM sales_order so
JOIN inventory_vehicle iv ON so.vin = iv.vin
JOIN car_model cm ON iv.model_id = cm.model_id
JOIN brand b ON cm.brand_id = b.brand_id
WHERE so.customer_id = 1 -- 替换为 :customer_id

UNION ALL

SELECT
    '服务' AS record_type,
    svo.service_order_id AS record_id,
    svo.created_time AS record_time,
    svo.service_type AS detail,
    svo.total_cost AS amount,
    svo.status AS status
FROM service_order svo
WHERE svo.customer_id = 1 -- 替换为 :customer_id

ORDER BY record_time DESC;

-- Q7：生成库存预警报表，列出库存数量低于安全库存阈值（3台）的车型。
SELECT
    b.brand_name,
    cm.series_name,
    cm.config_name,
    cm.year_model,
    cm.guide_price,
    COUNT(CASE WHEN iv.status = '在库' THEN 1 END) AS in_stock,
    COUNT(CASE WHEN iv.status = '已锁定' THEN 1 END) AS locked,
    COUNT(CASE WHEN iv.status = '在途' THEN 1 END) AS in_transit,
    COUNT(iv.vin) AS total_count
FROM car_model cm
JOIN brand b ON cm.brand_id = b.brand_id
LEFT JOIN inventory_vehicle iv ON cm.model_id = iv.model_id
GROUP BY b.brand_name, cm.series_name, cm.config_name, cm.year_model,
         cm.guide_price, cm.model_id
HAVING COUNT(CASE WHEN iv.status = '在库' THEN 1 END) < 3
ORDER BY in_stock ASC;


-- Q8（附加题）：各品牌销售占比及毛利率分析
SELECT
    b.brand_name,
    COUNT(DISTINCT so.order_id) AS order_count,
    COUNT(DISTINCT iv.vin) AS vehicle_count,
    COALESCE(SUM(so.total_amount), 0) AS total_sales,
    COALESCE(SUM(so.total_amount - iv.purchase_cost), 0) AS total_profit,
    ROUND(
        COALESCE(SUM(so.total_amount - iv.purchase_cost) * 100.0
            / NULLIF(SUM(so.total_amount), 0), 0), 2
    ) AS profit_margin_pct,
    ROUND(
        COALESCE(SUM(so.total_amount) * 100.0
            / NULLIF(SUM(SUM(so.total_amount)) OVER (), 0), 0), 2
    ) AS sales_share_pct,
    ROUND(
        COALESCE(AVG(so.total_amount - iv.purchase_cost), 0), 0
    ) AS avg_profit_per_order
FROM brand b
JOIN car_model cm ON b.brand_id = cm.brand_id
JOIN inventory_vehicle iv ON cm.model_id = iv.model_id
JOIN sales_order so ON iv.vin = so.vin AND so.order_status = '已完成'
GROUP BY b.brand_id, b.brand_name
ORDER BY total_sales DESC;
