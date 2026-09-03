CREATE FUNCTION sp_create_sales_order(
    p_customer_id INT,
    p_sales_consultant_id INT,
    p_vin VARCHAR(17),
    p_deposit_amount NUMERIC(12, 2),
    p_details_json JSON
)
RETURNS INT AS $$
DECLARE
    v_total NUMERIC(12, 2) := 0;
    v_idx INT := 0;
    v_len INT;
    v_dtype VARCHAR(20);
    v_desc VARCHAR(200);
    v_amount NUMERIC(10, 2);
    v_order_id INT;
BEGIN
    v_len := json_array_length(p_details_json);
    WHILE v_idx < v_len LOOP
        v_amount := (p_details_json -> v_idx ->> 'amount')::NUMERIC(10, 2);
        v_total := v_total + v_amount;
        v_idx := v_idx + 1;
    END LOOP;

    INSERT INTO sales_order (
        customer_id,
        sales_consultant_id,
        vin,
        total_amount,
        deposit_amount,
        order_status
    ) VALUES (
        p_customer_id,
        p_sales_consultant_id,
        p_vin,
        v_total,
        p_deposit_amount,
        '已锁定'
    )
    RETURNING order_id INTO v_order_id;

    v_idx := 0;
    WHILE v_idx < v_len LOOP
        v_dtype := p_details_json -> v_idx ->> 'detail_type';
        v_desc := p_details_json -> v_idx ->> 'description';
        v_amount := (p_details_json -> v_idx ->> 'amount')::NUMERIC(10, 2);

        INSERT INTO order_detail (order_id, detail_type, description, amount)
        VALUES (v_order_id, v_dtype, v_desc, v_amount);

        v_idx := v_idx + 1;
    END LOOP;

    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION sp_get_monthly_report(
    p_year INT,
    p_month INT
)
RETURNS TABLE(
    brand TEXT,
    series TEXT,
    order_count BIGINT,
    total_sales NUMERIC,
    total_profit NUMERIC,
    consultant_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.brand_name::TEXT AS brand,
        cm.series_name::TEXT AS series,
        COUNT(so.order_id) AS order_count,
        COALESCE(SUM(so.total_amount), 0) AS total_sales,
        COALESCE(SUM(so.total_amount - iv.purchase_cost), 0) AS total_profit,
        COUNT(DISTINCT so.sales_consultant_id) AS consultant_count
    FROM sales_order so
    JOIN inventory_vehicle iv ON so.vin = iv.vin
    JOIN car_model cm ON iv.model_id = cm.model_id
    JOIN brand b ON cm.brand_id = b.brand_id
    WHERE so.order_status = '已完成'
      AND EXTRACT(YEAR FROM so.delivery_time) = p_year
      AND EXTRACT(MONTH FROM so.delivery_time) = p_month
    GROUP BY b.brand_name, cm.series_name

    UNION ALL

    SELECT
        '【合计】'::TEXT,
        ''::TEXT,
        COUNT(so.order_id),
        COALESCE(SUM(so.total_amount), 0),
        COALESCE(SUM(so.total_amount - iv.purchase_cost), 0),
        COUNT(DISTINCT so.sales_consultant_id)
    FROM sales_order so
    JOIN inventory_vehicle iv ON so.vin = iv.vin
    WHERE so.order_status = '已完成'
      AND EXTRACT(YEAR FROM so.delivery_time) = p_year
      AND EXTRACT(MONTH FROM so.delivery_time) = p_month

    ORDER BY order_count DESC;
END;
$$ LANGUAGE plpgsql;
