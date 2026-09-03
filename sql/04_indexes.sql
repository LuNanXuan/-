CREATE INDEX idx_sales_order_created_time
ON sales_order(created_time);

CREATE INDEX idx_inventory_status_model
ON inventory_vehicle(status, model_id);

CREATE INDEX idx_customer_phone
ON customer(phone);

CREATE INDEX idx_sales_order_consultant
ON sales_order(sales_consultant_id);

CREATE INDEX idx_sales_order_customer
ON sales_order(customer_id);

CREATE INDEX idx_service_order_vin
ON service_order(vin);

CREATE INDEX idx_order_detail_order_id
ON order_detail(order_id);
