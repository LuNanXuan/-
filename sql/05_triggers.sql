CREATE FUNCTION fn_lock_car_on_order()
RETURNS TRIGGER AS $$
DECLARE
    v_status VARCHAR(10);
BEGIN
    SELECT status INTO v_status
    FROM inventory_vehicle
    WHERE vin = NEW.vin;

    IF v_status IS NULL THEN
        RAISE EXCEPTION '车辆VIN不存在，请核实';
    END IF;

    IF v_status != '在库' THEN
        RAISE EXCEPTION '车辆当前状态为"%"非"在库"状态，无法创建订单', v_status;
    END IF;

    UPDATE inventory_vehicle
    SET status = '已锁定'
    WHERE vin = NEW.vin;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_lock_car_on_order
BEFORE INSERT ON sales_order
FOR EACH ROW
EXECUTE FUNCTION fn_lock_car_on_order();


CREATE FUNCTION fn_update_inventory_on_delivery()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.order_status = '已完成' AND OLD.order_status != '已完成' THEN
        UPDATE inventory_vehicle
        SET status = '已售出'
        WHERE vin = NEW.vin;

        IF NEW.delivery_time IS NULL THEN
            NEW.delivery_time = CURRENT_TIMESTAMP;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_inventory_on_delivery
BEFORE UPDATE ON sales_order
FOR EACH ROW
EXECUTE FUNCTION fn_update_inventory_on_delivery();
