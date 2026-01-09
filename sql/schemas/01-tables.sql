/* =========================================================
    01_tables.sql — CREATION TABLES (POSTGRES COMPATIBLE)
   ========================================================= */

-- Extensions (Postgres)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------- ENUM TYPES (Postgres requires CREATE TYPE) ----------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'dependency_kind') THEN
        CREATE TYPE dependency_kind AS ENUM ('CAUSE','SEQUENCE','RELATED');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'requirement_rule') THEN
        CREATE TYPE requirement_rule AS ENUM ('ALL','ANY');
    END IF;
END$$;

-- =========================================================
-- 1) TABLES "REFERENTIELS"
-- =========================================================

CREATE TABLE operators (
    operator_id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE vehicle_consumable_types (
    vehicle_consumable_type_id UUID PRIMARY KEY,
    label VARCHAR(100) NOT NULL UNIQUE,
    unit  VARCHAR(255) NOT NULL
);

CREATE TABLE vehicle_types (
    vehicle_type_id UUID PRIMARY KEY,
    code  VARCHAR(255) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE vehicle_status (
    vehicle_status_id UUID PRIMARY KEY,
    label VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE interest_point_kinds (
    interest_point_kind_id UUID PRIMARY KEY,
    label VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE interest_point_consumable_types (
    interest_point_consumable_type_id UUID PRIMARY KEY,
    label VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE casualty_types (
    casualty_type_id UUID PRIMARY KEY,
    code  VARCHAR(20)  NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE energies (
    energy_id UUID PRIMARY KEY,
    label VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE casualty_status (
    casualty_status_id UUID PRIMARY KEY,
    label VARCHAR(50) NOT NULL UNIQUE
);


CREATE TABLE phase_categories(
    phase_category_id UUID PRIMARY KEY,
    code  VARCHAR(50) UNIQUE,
    label VARCHAR(50)
);

-- =========================================================
-- 2) TABLES DEPENDANTES DES REFERENTIELS
-- =========================================================

CREATE TABLE phase_types(
    phase_type_id UUID PRIMARY KEY,
    phase_category_id UUID,
    code  VARCHAR(50) UNIQUE,
    label VARCHAR(50),
    default_criticity SMALLINT CHECK (default_criticity BETWEEN 0 AND 7)
);

CREATE TABLE interest_points (
    interest_point_id UUID PRIMARY KEY,

    name    VARCHAR(100) NOT NULL UNIQUE,
    address VARCHAR(255) NOT NULL,
    zipcode VARCHAR(10) NOT NULL,
    city    VARCHAR(100) NOT NULL,
    latitude  DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,

    interest_point_kind_id UUID NOT NULL
);

-- =========================================================
-- 3) VEHICLES + STOCKS
-- =========================================================

CREATE TABLE vehicles (
    vehicle_id UUID PRIMARY KEY,

    vehicle_type_id UUID NOT NULL,
    immatriculation VARCHAR(20) NOT NULL UNIQUE,

    energy_id UUID NOT NULL,
    energy_level FLOAT NOT NULL
        CHECK (energy_level >= 0 AND energy_level <= 1),

    base_interest_point_id UUID NOT NULL,
    status_id UUID NOT NULL
);

CREATE TABLE vehicle_position_logs (
    vehicle_position_id UUID PRIMARY KEY,
    vehicle_id UUID NOT NULL,
    latitude  DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Stock: pas de PK ici (composite ajoutée dans 02_constraints.sql)
CREATE TABLE vehicle_consumables_stock (
    vehicle_id UUID NOT NULL,
    consumable_type_id UUID NOT NULL,
    current_quantity INTEGER NOT NULL,
    last_update TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Specs: pas de PK ici (composite ajoutée dans 02_constraints.sql)
CREATE TABLE vehicle_type_consumable_specs (
    vehicle_type_id UUID NOT NULL,
    consumable_type_id UUID NOT NULL,
    capacity_quantity INTEGER NOT NULL,
    initial_quantity INTEGER NOT NULL,
    is_applicable BOOLEAN NOT NULL
);

-- =========================================================
-- 4) INTEREST POINT CONSUMABLES
-- =========================================================

CREATE TABLE interest_point_consumables (
    interest_point_id UUID NOT NULL,
    interest_point_consumable_type_id UUID NOT NULL,

    current_quantity NUMERIC,
    last_update TIMESTAMPTZ NOT NULL
);

-- =========================================================
-- 5) INCIDENTS / PHASES / DEPENDENCIES
-- =========================================================

CREATE TABLE incidents (
    incident_id UUID PRIMARY KEY,

    created_by_operator_id UUID,
    address VARCHAR(255) NOT NULL,
    zipcode VARCHAR(10) NOT NULL,
    city VARCHAR(100) NOT NULL,

    latitude  DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,

    description VARCHAR(255),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Déclaration de l'incident
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Dernière modification
    ended_at TIMESTAMPTZ  -- Clôture de l'incident
);

CREATE TABLE incident_phases (
    incident_phase_id UUID PRIMARY KEY,

    incident_id UUID NOT NULL,
    phase_type_id UUID NOT NULL,

    priority INTEGER,

    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ
);

CREATE TABLE incident_phase_dependencies (
    incident_phase_id UUID NOT NULL,
    depends_on_incident_phase_id UUID NOT NULL,

    kind dependency_kind NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 6) CASUALTIES / TRANSPORTS
-- =========================================================

CREATE TABLE casualties(
    casualty_id UUID PRIMARY KEY,
    incident_phase_id UUID,
    casualty_type_id UUID,
    casualty_status_id UUID,

    reported_at TIMESTAMPTZ,
    notes TEXT
);

CREATE TABLE vehicle_assignments (
    vehicle_assignment_id UUID PRIMARY KEY,
    vehicle_id UUID NOT NULL,
    incident_phase_id UUID NOT NULL,

    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by_operator_id UUID,

    validated_at TIMESTAMPTZ,
    validated_by_operator_id UUID,

    unassigned_at TIMESTAMPTZ,

    notes TEXT
);

CREATE TABLE casualty_transports (
    casualty_transport_id UUID PRIMARY KEY,
    casualty_id UUID,
    vehicle_assignment_id UUID,

    picked_up_at TIMESTAMPTZ,
    dropped_off_at TIMESTAMPTZ,
    picked_up_latitude DOUBLE PRECISION NOT NULL,
    picked_up_longitude DOUBLE PRECISION NOT NULL,
    dropped_off_latitude DOUBLE PRECISION NOT NULL,
    dropped_off_longitude DOUBLE PRECISION NOT NULL,

    notes TEXT
);

-- =========================================================
-- 7) REINFORCEMENTS
-- =========================================================

CREATE TABLE reinforcement (
    reinforcement_id UUID PRIMARY KEY,
    incident_phase_id UUID NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMPTZ
);

CREATE TABLE reinforcement_vehicle_requests (
    reinforcement_id UUID NOT NULL,
    vehicle_type_id UUID NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);

-- =========================================================
-- 8) REQUIREMENTS
-- =========================================================

CREATE TABLE phase_type_vehicle_requirement_groups(
    group_id UUID PRIMARY KEY,
    phase_type_id UUID,
    label VARCHAR(50),

    rule requirement_rule,   -- ALL / ANY
    min_total INTEGER,
    max_total INTEGER,
    priority SMALLINT,
    is_hard BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE phase_type_vehicle_requirements(
    group_id UUID NOT NULL,
    vehicle_type_id UUID,

    min_quantity INTEGER DEFAULT 0,
    max_quantity INTEGER DEFAULT NULL,
    mandatory BOOLEAN DEFAULT TRUE,
    preference_rank SMALLINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 9) LOG
-- =========================================================

CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_type VARCHAR(50) NOT NULL,
    actor_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    diff JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 10) Assignments Propositions
-- =========================================================
CREATE TABLE vehicle_assignment_proposals (
    proposal_id   UUID PRIMARY KEY,      -- id renvoyé par le moteur
    incident_id   UUID NOT NULL,
    generated_at  TIMESTAMPTZ NOT NULL,  -- generated_at du moteur
    received_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    validated_at   TIMESTAMPTZ,
    rejected_at   TIMESTAMPTZ
);

CREATE TABLE vehicle_assignment_proposal_items (
    proposal_id        UUID NOT NULL,
    incident_phase_id  UUID NOT NULL,
    vehicle_id         UUID NOT NULL,

    proposal_rank      INTEGER NOT NULL,      -- ordre renvoyé (1..N)

    distance_km        DOUBLE PRECISION NOT NULL,
    estimated_time_min INTEGER NOT NULL,
    route_geometry     JSONB NOT NULL,

    energy_level       FLOAT NOT NULL,
    score              DOUBLE PRECISION NOT NULL,

    rationale          TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);


CREATE TABLE vehicle_assignment_proposal_missing (
    proposal_id       UUID NOT NULL,
    incident_phase_id UUID NULL,         -- NULL = global, sinon par phase
    vehicle_type_id   UUID NOT NULL,

    missing_quantity  INTEGER NOT NULL CHECK (missing_quantity >= 0),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
