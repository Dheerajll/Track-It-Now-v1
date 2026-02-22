-- ============================================================
-- FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION log_status_changed()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.current_status <> OLD.current_status THEN
        INSERT INTO parcel_status_history(parcel_id, status)
        VALUES (NEW.id, NEW.current_status);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION validate_parcel_status_transition()
RETURNS TRIGGER AS $$
DECLARE
    old_order INT;
    new_order INT;
BEGIN
    old_order := CASE OLD.current_status
        WHEN 'created'    THEN 1
        WHEN 'assigned'   THEN 2
        WHEN 'picked_up'  THEN 3
        WHEN 'in_transit' THEN 4
        WHEN 'delivered'  THEN 5
    END;

    new_order := CASE NEW.current_status
        WHEN 'created'    THEN 1
        WHEN 'assigned'   THEN 2
        WHEN 'picked_up'  THEN 3
        WHEN 'in_transit' THEN 4
        WHEN 'delivered'  THEN 5
    END;

    IF new_order <> old_order + 1 THEN
        RAISE EXCEPTION
        'Invalid parcel status transition: % → %',
        OLD.current_status, NEW.current_status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION sync_delivery_times_ordered()
RETURNS TRIGGER AS $$
DECLARE
    old_order INT;
    new_order INT;
BEGIN
    old_order := CASE OLD.current_status
        WHEN 'created'    THEN 1
        WHEN 'assigned'   THEN 2
        WHEN 'picked_up'  THEN 3
        WHEN 'in_transit' THEN 4
        WHEN 'delivered'  THEN 5
    END;

    new_order := CASE NEW.current_status
        WHEN 'created'    THEN 1
        WHEN 'assigned'   THEN 2
        WHEN 'picked_up'  THEN 3
        WHEN 'in_transit' THEN 4
        WHEN 'delivered'  THEN 5
    END;

    IF new_order > old_order THEN

        IF new_order = 2 THEN
            UPDATE delivery_assignment
            SET assigned_time = NOW()
            WHERE parcel_id = NEW.id;
        END IF;

        IF new_order = 4 THEN
            UPDATE delivery_assignment
            SET started_time = NOW()
            WHERE parcel_id = NEW.id;
        END IF;

        IF new_order = 5 THEN
            UPDATE delivery_assignment
            SET completed_time = NOW()
            WHERE parcel_id = NEW.id;
        END IF;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL   NOT NULL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    password    TEXT        NOT NULL,
    role        VARCHAR(55) NOT NULL,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT user_role_chk CHECK (role IN ('agent', 'customer'))
);


CREATE TABLE IF NOT EXISTS parcels (
    id              BIGSERIAL   NOT NULL PRIMARY KEY,
    sender_id       BIGINT      NOT NULL,
    receiver_id     BIGINT      NOT NULL,
    description     TEXT,
    current_status  VARCHAR(55) NOT NULL DEFAULT 'created',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id)   REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT status_chk CHECK (current_status IN ('created', 'assigned', 'picked_up', 'in_transit', 'delivered'))
);


CREATE TABLE IF NOT EXISTS parcel_status_history (
    id          BIGSERIAL   NOT NULL PRIMARY KEY,
    parcel_id   BIGINT      NOT NULL,
    status      VARCHAR(55) NOT NULL,
    changed_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parcel_id) REFERENCES parcels(id) ON DELETE CASCADE,
    CONSTRAINT status_chk CHECK (status IN ('created', 'assigned', 'picked_up', 'in_transit', 'delivered'))
);


CREATE TABLE IF NOT EXISTS parcel_points (
    id          BIGSERIAL   NOT NULL PRIMARY KEY,
    parcel_id   BIGINT      NOT NULL,
    source      POINT       NOT NULL,
    destination POINT       NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parcel_id) REFERENCES parcels(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS delivery_assignment (
    id              BIGSERIAL   NOT NULL PRIMARY KEY,
    parcel_id       BIGINT      NOT NULL UNIQUE,
    agent_id        BIGINT      NOT NULL,
    assigned_time   TIMESTAMPTZ,
    started_time    TIMESTAMPTZ,
    completed_time  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parcel_id) REFERENCES parcels(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id)  REFERENCES users(id)   ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS location_table (
    id                  BIGSERIAL        PRIMARY KEY,
    delivery_id         BIGINT           NOT NULL,
    agent_id            BIGINT           NOT NULL,
    lat                 DOUBLE PRECISION NOT NULL,
    long                DOUBLE PRECISION NOT NULL,
    location_timestamp  TIMESTAMPTZ      NOT NULL,
    created_at          TIMESTAMPTZ      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (delivery_id) REFERENCES delivery_assignment(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id)    REFERENCES users(id)               ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS parcel_requests (
    id                  SERIAL      PRIMARY KEY,
    sender_id           BIGINT      NOT NULL,
    receiver_id         BIGINT      NOT NULL,
    status              VARCHAR(55) NOT NULL DEFAULT 'pending',
    parcel_description  TEXT,
    sender_location     POINT       NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at          TIMESTAMPTZ,
    FOREIGN KEY (sender_id)   REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);


CREATE TABLE IF NOT EXISTS trackingcode (
    id              SERIAL      PRIMARY KEY,
    parcel_id       BIGINT      REFERENCES parcels(id),
    agent_id        BIGINT      REFERENCES users(id),
    tracking_code   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- INDEXES (IF NOT EXISTS supported in Postgres 9.5+)
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_parcel_status_history
ON parcel_status_history(changed_at ASC);

CREATE INDEX IF NOT EXISTS idx_delivery_time
ON location_table(delivery_id, location_timestamp DESC);


-- ============================================================
-- TRIGGERS (drop-and-recreate pattern since triggers don't
-- support IF NOT EXISTS — but OR REPLACE is safe for functions)
-- ============================================================

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'parcels_set_updated_at'
    ) THEN
        CREATE TRIGGER parcels_set_updated_at
        BEFORE UPDATE ON parcels
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'parcel_status_order_trigger'
    ) THEN
        CREATE TRIGGER parcel_status_order_trigger
        BEFORE UPDATE OF current_status ON parcels
        FOR EACH ROW EXECUTE FUNCTION validate_parcel_status_transition();
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'sync_delivery_times_trigger'
    ) THEN
        CREATE TRIGGER sync_delivery_times_trigger
        AFTER UPDATE OF current_status ON parcels
        FOR EACH ROW EXECUTE FUNCTION sync_delivery_times_ordered();
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'parcel_status_history_trigger'
    ) THEN
        CREATE TRIGGER parcel_status_history_trigger
        AFTER UPDATE OF current_status ON parcels
        FOR EACH ROW EXECUTE FUNCTION log_status_changed();
    END IF;
END $$;