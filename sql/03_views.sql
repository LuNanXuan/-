CREATE VIEW v_sales_performance AS
SELECT
    e.employee_id,
    e.name AS consultant_name,
    e.employee_code,
    e.department,
    COUNT(so.order_id) AS total_orders,
    COALESCE(SUM(so.total_amount), 0) AS total_sales_amount,
    COALESCE(SUM(so.total_amount - iv.purchase_cost), 0) AS total_profit
FROM employee e
LEFT JOIN sales_order so
    ON e.employee_id = so.sales_consultant_id
    AND so.order_status = '已完成'
LEFT JOIN inventory_vehicle iv
    ON so.vin = iv.vin
WHERE e.role = '销售顾问'
GROUP BY e.employee_id, e.name, e.employee_code, e.department
ORDER BY total_sales_amount DESC;

CREATE VIEW v_inventory_summary AS
SELECT
    cm.model_id,
    b.brand_name,
    cm.series_name,
    cm.year_model,
    cm.config_name,
    cm.guide_price,
    COUNT(CASE WHEN iv.status = '在库' THEN 1 END) AS in_stock,
    COUNT(CASE WHEN iv.status = '已锁定' THEN 1 END) AS locked,
    COUNT(CASE WHEN iv.status = '已售出' THEN 1 END) AS sold,
    COUNT(CASE WHEN iv.status = '在途' THEN 1 END) AS in_transit,
    COUNT(iv.vin) AS total_count
FROM car_model cm
JOIN brand b ON cm.brand_id = b.brand_id
LEFT JOIN inventory_vehicle iv ON cm.model_id = iv.model_id
GROUP BY cm.model_id, b.brand_name, cm.series_name, cm.year_model, cm.config_name, cm.guide_price
ORDER BY cm.model_id;

CREATE VIEW v_customer_value AS
SELECT
    c.customer_id,
    c.name,
    c.phone,
    c.first_visit_date,
    COALESCE(p.purchase_total, 0) AS total_purchase,
    COALESCE(s.service_total, 0) AS total_service,
    COALESCE(p.purchase_total, 0) + COALESCE(s.service_total, 0) AS total_consumption,
    CASE
        WHEN COALESCE(p.purchase_total, 0) + COALESCE(s.service_total, 0) >= 300000 THEN '金卡客户'
        WHEN COALESCE(p.purchase_total, 0) + COALESCE(s.service_total, 0) >= 100000 THEN '银卡客户'
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
