-- Additive, idempotent cost provenance migration.
-- Applied by app.database.init_db.upgrade_cost_schema().
ALTER TABLE cost_cache ADD COLUMN IF NOT EXISTS cost_status VARCHAR;
ALTER TABLE cost_history ADD COLUMN IF NOT EXISTS cost_status VARCHAR;
ALTER TABLE cost_records ADD COLUMN IF NOT EXISTS cost_status VARCHAR;

UPDATE cost_cache SET cost_status = CASE
    WHEN monthly_cost IS NOT NULL AND is_estimated IS TRUE THEN 'estimated'
    WHEN monthly_cost IS NOT NULL THEN 'available'
    ELSE 'unavailable'
END WHERE cost_status IS NULL;
UPDATE cost_history SET cost_status = CASE
    WHEN monthly_cost IS NOT NULL AND is_estimated IS TRUE THEN 'estimated'
    WHEN monthly_cost IS NOT NULL THEN 'available'
    ELSE 'unavailable'
END WHERE cost_status IS NULL;
UPDATE cost_records SET cost_status = CASE
    WHEN monthly_cost IS NOT NULL AND is_estimated IS TRUE THEN 'estimated'
    WHEN monthly_cost IS NOT NULL THEN 'available'
    ELSE 'unavailable'
END WHERE cost_status IS NULL;
