CREATE DATABASE car_sales ENCODING 'UTF8';

-- 1. 品牌表
CREATE TABLE brand (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(50) NOT NULL UNIQUE
);

-- 2. 车型表
CREATE TABLE car_model (
    model_id SERIAL PRIMARY KEY,
    brand_id INT NOT NULL,
    series_name VARCHAR(100) NOT NULL,
    year_model VARCHAR(20) NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    guide_price NUMERIC(12, 2) NOT NULL,
    displacement NUMERIC(3, 1),
    model_type VARCHAR(20) NOT NULL,
    CONSTRAINT fk_model_brand FOREIGN KEY (brand_id) REFERENCES brand(brand_id)
);

-- 3. 库存车辆表
CREATE TABLE inventory_vehicle (
    vin VARCHAR(17) PRIMARY KEY,
    model_id INT NOT NULL,
    color VARCHAR(20) NOT NULL,
    production_date DATE NOT NULL,
    entry_date DATE NOT NULL,
    purchase_cost NUMERIC(12, 2) NOT NULL,
    suggested_retail_price NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT '在途'
        CHECK (status IN ('在库', '已锁定', '已售出', '在途')),
    CONSTRAINT fk_vehicle_model FOREIGN KEY (model_id) REFERENCES car_model(model_id)
);

-- 4. 员工表，supervisor_id 指回自己的上级
CREATE TABLE employee (
    employee_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    employee_code VARCHAR(20) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL,
    department VARCHAR(50) NOT NULL,
    hire_date DATE NOT NULL,
    supervisor_id INT,
    CONSTRAINT fk_employee_supervisor FOREIGN KEY (supervisor_id) REFERENCES employee(employee_id)
);

-- 5. 客户表
CREATE TABLE customer (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    gender VARCHAR(5) NOT NULL CHECK (gender IN ('男', '女')),
    phone VARCHAR(20) NOT NULL UNIQUE,
    id_card VARCHAR(18) UNIQUE,
    address VARCHAR(200),
    first_visit_date DATE NOT NULL
);

-- 6. 客户意向表，记录谁对哪款车感兴趣
CREATE TABLE customer_intention (
    intention_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    intended_model_id INT,
    intention_level VARCHAR(5) NOT NULL DEFAULT '中'
        CHECK (intention_level IN ('高', '中', '低')),
    remarks TEXT,
    follow_up_consultant_id INT NOT NULL,
    next_contact_time TIMESTAMP,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_intention_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    CONSTRAINT fk_intention_model FOREIGN KEY (intended_model_id) REFERENCES car_model(model_id),
    CONSTRAINT fk_intention_consultant FOREIGN KEY (follow_up_consultant_id) REFERENCES employee(employee_id)
);

-- 7. 销售订单表，核心表
CREATE TABLE sales_order (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    sales_consultant_id INT NOT NULL,
    vin VARCHAR(17) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    deposit_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    order_status VARCHAR(20) NOT NULL DEFAULT '待定'
        CHECK (order_status IN ('待定', '已锁定', '已付定金', '已完成', '已取消')),
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    delivery_time TIMESTAMP,
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    CONSTRAINT fk_order_consultant FOREIGN KEY (sales_consultant_id) REFERENCES employee(employee_id),
    CONSTRAINT fk_order_vehicle FOREIGN KEY (vin) REFERENCES inventory_vehicle(vin)
);

-- 8. 订单明细表，一个订单可以有多条明细
CREATE TABLE order_detail (
    detail_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    detail_type VARCHAR(20) NOT NULL,
    description VARCHAR(200) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    CONSTRAINT fk_detail_order FOREIGN KEY (order_id) REFERENCES sales_order(order_id)
);

-- 9. 服务工单表，记录售后维修保养
CREATE TABLE service_order (
    service_order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    vin VARCHAR(17) NOT NULL,
    service_type VARCHAR(30) NOT NULL,
    service_consultant_id INT NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estimated_completion_time TIMESTAMP,
    total_cost NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT '待处理'
        CHECK (status IN ('待处理', '进行中', '已完成', '已取消')),
    CONSTRAINT fk_svc_order_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    CONSTRAINT fk_svc_order_vehicle FOREIGN KEY (vin) REFERENCES inventory_vehicle(vin),
    CONSTRAINT fk_svc_order_consultant FOREIGN KEY (service_consultant_id) REFERENCES employee(employee_id)
);

-- 10. 服务明细表
CREATE TABLE service_detail (
    detail_id SERIAL PRIMARY KEY,
    service_order_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price NUMERIC(10, 2) NOT NULL,
    CONSTRAINT fk_svc_detail_order FOREIGN KEY (service_order_id) REFERENCES service_order(service_order_id)
);
