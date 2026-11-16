CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE users (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email varchar(254) NOT NULL UNIQUE CHECK (email = lower(email)),
    full_name varchar(120) NOT NULL CHECK (length(trim(full_name)) > 0),
    password_hash text NOT NULL,
    role varchar(16) NOT NULL CHECK (role IN ('borrower', 'admin')),
    borrower_type varchar(16) CHECK (borrower_type IN ('student', 'faculty')),
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT borrower_type_required CHECK (
        (role = 'borrower' AND borrower_type IS NOT NULL) OR
        (role = 'admin' AND borrower_type IS NULL)
    )
);

CREATE TABLE equipment_categories (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name varchar(80) NOT NULL UNIQUE,
    description text NOT NULL DEFAULT ''
);

CREATE TABLE equipment_items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id bigint NOT NULL REFERENCES equipment_categories(id) ON DELETE RESTRICT,
    asset_code varchar(40) NOT NULL UNIQUE CHECK (length(trim(asset_code)) > 0),
    name varchar(120) NOT NULL CHECK (length(trim(name)) > 0),
    description text NOT NULL DEFAULT '',
    location varchar(120) NOT NULL,
    condition varchar(16) NOT NULL DEFAULT 'good'
        CHECK (condition IN ('good', 'fair', 'damaged')),
    service_status varchar(16) NOT NULL DEFAULT 'serviceable'
        CHECK (service_status IN ('serviceable', 'maintenance', 'retired')),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT damaged_not_serviceable CHECK (condition <> 'damaged' OR service_status <> 'serviceable')
);
CREATE INDEX equipment_category_idx ON equipment_items(category_id);
CREATE INDEX equipment_name_idx ON equipment_items(lower(name));

CREATE TABLE borrowing_requests (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    borrower_id bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    equipment_id bigint NOT NULL REFERENCES equipment_items(id) ON DELETE RESTRICT,
    borrow_at timestamptz NOT NULL,
    due_at timestamptz NOT NULL,
    purpose varchar(500) NOT NULL CHECK (length(trim(purpose)) BETWEEN 5 AND 500),
    status varchar(16) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'canceled', 'released', 'returned')),
    decided_by bigint REFERENCES users(id) ON DELETE RESTRICT,
    decided_at timestamptz,
    decision_remarks varchar(500),
    canceled_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT valid_booking_period CHECK (due_at > borrow_at),
    CONSTRAINT decision_consistent CHECK (
        (status IN ('pending', 'canceled') AND decided_by IS NULL AND decided_at IS NULL) OR
        (status IN ('approved', 'rejected', 'released', 'returned') AND decided_by IS NOT NULL AND decided_at IS NOT NULL)
    ),
    CONSTRAINT cancellation_consistent CHECK ((status = 'canceled') = (canceled_at IS NOT NULL)),
    CONSTRAINT request_equipment_pair UNIQUE (id, equipment_id),
    CONSTRAINT no_overlapping_reservations EXCLUDE USING gist (
        equipment_id WITH =,
        tstzrange(borrow_at, due_at, '[)') WITH &&
    ) WHERE (status IN ('approved', 'released'))
);
CREATE INDEX request_borrower_created_idx ON borrowing_requests(borrower_id, created_at DESC);
CREATE INDEX request_status_due_idx ON borrowing_requests(status, due_at);
CREATE INDEX request_equipment_idx ON borrowing_requests(equipment_id);

CREATE TABLE loan_records (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id bigint NOT NULL UNIQUE,
    equipment_id bigint NOT NULL REFERENCES equipment_items(id) ON DELETE RESTRICT,
    released_by bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    released_at timestamptz NOT NULL DEFAULT now(),
    release_condition varchar(16) NOT NULL CHECK (release_condition IN ('good', 'fair')),
    returned_by bigint REFERENCES users(id) ON DELETE RESTRICT,
    returned_at timestamptz,
    return_condition varchar(16) CHECK (return_condition IN ('good', 'fair', 'damaged')),
    return_remarks varchar(500),
    CONSTRAINT loan_request_equipment_fk FOREIGN KEY (request_id, equipment_id)
        REFERENCES borrowing_requests(id, equipment_id) ON DELETE RESTRICT,
    CONSTRAINT return_after_release CHECK (returned_at IS NULL OR returned_at >= released_at),
    CONSTRAINT return_fields_consistent CHECK (
        (returned_at IS NULL AND returned_by IS NULL AND return_condition IS NULL AND return_remarks IS NULL) OR
        (returned_at IS NOT NULL AND returned_by IS NOT NULL AND return_condition IS NOT NULL)
    )
);
CREATE UNIQUE INDEX one_active_loan_per_item ON loan_records(equipment_id) WHERE returned_at IS NULL;
CREATE INDEX loan_returned_idx ON loan_records(returned_at);

CREATE TABLE audit_logs (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    action varchar(40) NOT NULL,
    entity_type varchar(40) NOT NULL,
    entity_id bigint NOT NULL,
    details jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(details) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_entity_idx ON audit_logs(entity_type, entity_id, created_at DESC);
CREATE INDEX audit_actor_idx ON audit_logs(actor_id, created_at DESC);

CREATE FUNCTION reject_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are append-only';
END;
$$;
CREATE TRIGGER audit_append_only BEFORE UPDATE OR DELETE OR TRUNCATE ON audit_logs
    FOR EACH STATEMENT EXECUTE FUNCTION reject_audit_mutation();

-- Runtime is read-only in Phase 1. Broaden only in a reviewed Phase 2 migration.
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'equiptrack_app') THEN
        GRANT USAGE ON SCHEMA public TO equiptrack_app;
        GRANT SELECT ON equipment_categories, equipment_items, borrowing_requests, loan_records TO equiptrack_app;
    END IF;
END $$;
