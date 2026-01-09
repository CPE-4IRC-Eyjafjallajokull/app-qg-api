/* =========================================================
   02_constraints.sql — CONSTRAINTS (FK / PK / UNIQUE / INDEX)
   ========================================================= */

-- =========================================================
-- 0) PRE-REQ POUR FK SUR LABELS (casualty_status)
-- =========================================================
-- FK depuis casualties.status (VARCHAR) vers casualty_status.label
-- => label doit être UNIQUE (et pas seulement "UNIQUE" logique, mais une contrainte unique)
ALTER TABLE casualty_status
    ADD CONSTRAINT uq_casualty_status_label UNIQUE (label);

-- =========================================================
-- 1) PRIMARY KEYS COMPOSITES (tables d'association)
-- =========================================================

-- interest_point_consumables : 1 ligne par (interest_point, consumable_type)
ALTER TABLE interest_point_consumables
    ADD CONSTRAINT pk_interest_point_consumables
    PRIMARY KEY (interest_point_id, interest_point_consumable_type_id);

-- vehicle_consumables_stock : 1 ligne par (vehicle, consumable_type)
ALTER TABLE vehicle_consumables_stock
    ADD CONSTRAINT pk_vehicle_consumables_stock
    PRIMARY KEY (vehicle_id, consumable_type_id);

-- vehicle_type_consumable_specs : 1 ligne par (vehicle_type, consumable_type)
ALTER TABLE vehicle_type_consumable_specs
    ADD CONSTRAINT pk_vehicle_type_consumable_specs
    PRIMARY KEY (vehicle_type_id, consumable_type_id);

-- incident_phase_dependencies : 1 dépendance par (phase, depends_on)
ALTER TABLE incident_phase_dependencies
    ADD CONSTRAINT pk_incident_phase_dependencies
    PRIMARY KEY (incident_phase_id, depends_on_incident_phase_id);

-- empêche une phase de dépendre d'elle-même
ALTER TABLE incident_phase_dependencies
    ADD CONSTRAINT chk_ipd_not_self
    CHECK (incident_phase_id <> depends_on_incident_phase_id);

-- phase_type_vehicle_requirements : 1 requirement par (group, vehicle_type)
ALTER TABLE phase_type_vehicle_requirements
    ADD CONSTRAINT pk_phase_type_vehicle_requirements
    PRIMARY KEY (group_id, vehicle_type_id);

-- reinforcement_vehicle_requests : 1 ligne par (reinforcement, vehicle_type)
ALTER TABLE reinforcement_vehicle_requests
    ADD CONSTRAINT pk_reinforcement_vehicle_requests
    PRIMARY KEY (reinforcement_id, vehicle_type_id);

-- =========================================================
-- 2) FOREIGN KEYS (références du schéma)
-- =========================================================

-- ---------- phase_types -> phase_categories ----------
ALTER TABLE phase_types
    ADD CONSTRAINT fk_phase_types_phase_category
    FOREIGN KEY (phase_category_id)
    REFERENCES phase_categories (phase_category_id)
    ON DELETE RESTRICT;

-- ---------- interest_points -> interest_point_kinds ----------
ALTER TABLE interest_points
    ADD CONSTRAINT fk_interest_points_kind
    FOREIGN KEY (interest_point_kind_id)
    REFERENCES interest_point_kinds (interest_point_kind_id)
    ON DELETE RESTRICT;

-- ---------- vehicles -> vehicle_types / energies / interest_points / vehicle_status ----------
ALTER TABLE vehicles
    ADD CONSTRAINT fk_vehicles_vehicle_type
    FOREIGN KEY (vehicle_type_id)
    REFERENCES vehicle_types (vehicle_type_id)
    ON DELETE RESTRICT;

ALTER TABLE vehicles
    ADD CONSTRAINT fk_vehicles_energy
    FOREIGN KEY (energy_id)
    REFERENCES energies (energy_id)
    ON DELETE RESTRICT;

ALTER TABLE vehicles
    ADD CONSTRAINT fk_vehicles_base_interest_point
    FOREIGN KEY (base_interest_point_id)
    REFERENCES interest_points (interest_point_id)
    ON DELETE RESTRICT;

ALTER TABLE vehicles
    ADD CONSTRAINT fk_vehicles_status
    FOREIGN KEY (status_id)
    REFERENCES vehicle_status (vehicle_status_id)
    ON DELETE RESTRICT;

-- ---------- vehicle_position_logs -> vehicles ----------
ALTER TABLE vehicle_position_logs
    ADD CONSTRAINT fk_vehicle_position_logs_vehicle
    FOREIGN KEY (vehicle_id)
    REFERENCES vehicles (vehicle_id)
    ON DELETE CASCADE;

-- ---------- vehicle_consumables_stock -> vehicles / vehicle_consumable_types ----------
ALTER TABLE vehicle_consumables_stock
    ADD CONSTRAINT fk_vcs_vehicle
    FOREIGN KEY (vehicle_id)
    REFERENCES vehicles (vehicle_id)
    ON DELETE CASCADE;

ALTER TABLE vehicle_consumables_stock
    ADD CONSTRAINT fk_vcs_consumable_type
    FOREIGN KEY (consumable_type_id)
    REFERENCES vehicle_consumable_types (vehicle_consumable_type_id)
    ON DELETE RESTRICT;

-- ---------- vehicle_type_consumable_specs -> vehicle_types / vehicle_consumable_types ----------
ALTER TABLE vehicle_type_consumable_specs
    ADD CONSTRAINT fk_vtcs_vehicle_type
    FOREIGN KEY (vehicle_type_id)
    REFERENCES vehicle_types (vehicle_type_id)
    ON DELETE CASCADE;

ALTER TABLE vehicle_type_consumable_specs
    ADD CONSTRAINT fk_vtcs_consumable_type
    FOREIGN KEY (consumable_type_id)
    REFERENCES vehicle_consumable_types (vehicle_consumable_type_id)
    ON DELETE RESTRICT;

-- ---------- interest_point_consumables -> interest_points / interest_point_consumable_types ----------
ALTER TABLE interest_point_consumables
    ADD CONSTRAINT fk_ipc_interest_point
    FOREIGN KEY (interest_point_id)
    REFERENCES interest_points (interest_point_id)
    ON DELETE CASCADE;

ALTER TABLE interest_point_consumables
    ADD CONSTRAINT fk_ipc_consumable_type
    FOREIGN KEY (interest_point_consumable_type_id)
    REFERENCES interest_point_consumable_types (interest_point_consumable_type_id)
    ON DELETE RESTRICT;

-- ---------- incidents -> operators ----------
ALTER TABLE incidents
    ADD CONSTRAINT fk_incidents_created_by_operator
    FOREIGN KEY (created_by_operator_id)
    REFERENCES operators (operator_id)
    ON DELETE SET NULL;

-- ---------- incident_phases -> incidents / phase_types ----------
ALTER TABLE incident_phases
    ADD CONSTRAINT fk_incident_phases_incident
    FOREIGN KEY (incident_id)
    REFERENCES incidents (incident_id)
    ON DELETE CASCADE;

ALTER TABLE incident_phases
    ADD CONSTRAINT fk_incident_phases_phase_type
    FOREIGN KEY (phase_type_id)
    REFERENCES phase_types (phase_type_id)
    ON DELETE RESTRICT;

-- ---------- incident_phase_dependencies -> incident_phases ----------
ALTER TABLE incident_phase_dependencies
    ADD CONSTRAINT fk_ipd_incident_phase
    FOREIGN KEY (incident_phase_id)
    REFERENCES incident_phases (incident_phase_id)
    ON DELETE CASCADE;

ALTER TABLE incident_phase_dependencies
    ADD CONSTRAINT fk_ipd_depends_on_phase
    FOREIGN KEY (depends_on_incident_phase_id)
    REFERENCES incident_phases (incident_phase_id)
    ON DELETE CASCADE;

-- ---------- casualties -> incident_phases / casualty_types / casualty_status ----------
ALTER TABLE casualties
    ADD CONSTRAINT fk_casualties_incident_phase
    FOREIGN KEY (incident_phase_id)
    REFERENCES incident_phases (incident_phase_id)
    ON DELETE CASCADE;

ALTER TABLE casualties
    ADD CONSTRAINT fk_casualties_type
    FOREIGN KEY (casualty_type_id)
    REFERENCES casualty_types (casualty_type_id)
    ON DELETE RESTRICT;

-- status contrôlé par la table casualty_status (sur la colonne label)
ALTER TABLE casualties
    ADD CONSTRAINT fk_casualty_status_id
    FOREIGN KEY (casualty_status_id)
    REFERENCES casualty_status (casualty_status_id)
    ON DELETE RESTRICT;

-- ---------- vehicle_assignments -> vehicles / incident_phases / operators ----------
ALTER TABLE vehicle_assignments
    ADD CONSTRAINT fk_vehicle_assignments_vehicle
    FOREIGN KEY (vehicle_id)
    REFERENCES vehicles (vehicle_id)
    ON DELETE RESTRICT;

ALTER TABLE vehicle_assignments
    ADD CONSTRAINT fk_vehicle_assignments_incident_phase
    FOREIGN KEY (incident_phase_id)
    REFERENCES incident_phases (incident_phase_id)
    ON DELETE CASCADE;

ALTER TABLE vehicle_assignments
    ADD CONSTRAINT fk_vehicle_assignments_assigned_by
    FOREIGN KEY (assigned_by_operator_id)
    REFERENCES operators (operator_id)
    ON DELETE SET NULL;

ALTER TABLE vehicle_assignments
    ADD CONSTRAINT fk_vehicle_assignments_validated_by
    FOREIGN KEY (validated_by_operator_id)
    REFERENCES operators (operator_id)
    ON DELETE SET NULL;

-- Contrainte du schéma : un véhicule ne peut pas avoir 2 affectations actives simultanément
CREATE UNIQUE INDEX IF NOT EXISTS uq_vehicle_assignments_vehicle_active
    ON vehicle_assignments (vehicle_id)
    WHERE unassigned_at IS NULL;

-- ---------- casualty_transports -> casualties / vehicle_assignments ----------
ALTER TABLE casualty_transports
    ADD CONSTRAINT fk_casualty_transports_casualty
    FOREIGN KEY (casualty_id)
    REFERENCES casualties (casualty_id)
    ON DELETE CASCADE;

ALTER TABLE casualty_transports
    ADD CONSTRAINT fk_casualty_transports_vehicle_assignment
    FOREIGN KEY (vehicle_assignment_id)
    REFERENCES vehicle_assignments (vehicle_assignment_id)
    ON DELETE SET NULL;

-- ---------- phase_type_vehicle_requirement_groups -> phase_types ----------
ALTER TABLE phase_type_vehicle_requirement_groups
    ADD CONSTRAINT fk_ptrg_phase_type
    FOREIGN KEY (phase_type_id)
    REFERENCES phase_types (phase_type_id)
    ON DELETE RESTRICT;

-- ---------- phase_type_vehicle_requirements -> groups / vehicle_types ----------
ALTER TABLE phase_type_vehicle_requirements
    ADD CONSTRAINT fk_ptr_group
    FOREIGN KEY (group_id)
    REFERENCES phase_type_vehicle_requirement_groups (group_id)
    ON DELETE CASCADE;

ALTER TABLE phase_type_vehicle_requirements
    ADD CONSTRAINT fk_ptr_vehicle_type
    FOREIGN KEY (vehicle_type_id)
    REFERENCES vehicle_types (vehicle_type_id)
    ON DELETE RESTRICT;

-- ---------- reinforcement -> incident_phases  ----------
ALTER TABLE reinforcement
    ADD CONSTRAINT fk_reinforcement_incident_phase
    FOREIGN KEY (incident_phase_id)
    REFERENCES incident_phases (incident_phase_id)
    ON DELETE CASCADE;

-- ---------- reinforcement_vehicle_requests -> reinforcement / vehicle_types ----------
ALTER TABLE reinforcement_vehicle_requests
    ADD CONSTRAINT fk_rvr_reinforcement
    FOREIGN KEY (reinforcement_id)
    REFERENCES reinforcement (reinforcement_id)
    ON DELETE CASCADE;

ALTER TABLE reinforcement_vehicle_requests
    ADD CONSTRAINT fk_rvr_vehicle_type
    FOREIGN KEY (vehicle_type_id)
    REFERENCES vehicle_types (vehicle_type_id)
    ON DELETE RESTRICT;

-- ---------- vehicle_assignment_proposals / vehicle_assignment_proposal_items / vehicle_assignment_proposal_missing ----------
ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT pk_vehicle_assignment_proposal_items
    PRIMARY KEY (proposal_id, incident_phase_id, vehicle_id);

ALTER TABLE vehicle_assignment_proposal_missing
    ADD CONSTRAINT pk_vehicle_assignment_proposal_missing
    PRIMARY KEY (proposal_id, incident_phase_id, vehicle_type_id);

ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT uq_vehicle_assignment_proposal_items_rank
    UNIQUE (proposal_id, incident_phase_id, proposal_rank);

ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT chk_vapi_distance_km_nonneg
    CHECK (distance_km >= 0);

ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT chk_vapi_estimated_time_min_nonneg
    CHECK (estimated_time_min >= 0);

ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT chk_vapi_energy_level_range
    CHECK (energy_level >= 0 AND energy_level <= 1);

ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT chk_vapi_score_range
    CHECK (score >= 0 AND score <= 1);

-- GeoJSON “shape” minimal
ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT chk_vapi_route_geometry_shape
    CHECK (
        route_geometry ? 'type'
        AND route_geometry ? 'coordinates'
        AND jsonb_typeof(route_geometry->'type') = 'string'
        AND jsonb_typeof(route_geometry->'coordinates') = 'array'
    );

ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT chk_vapi_route_geometry_type
    CHECK (route_geometry->>'type' = 'LineString');

ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT fk_vapi_proposal
    FOREIGN KEY (proposal_id)
    REFERENCES vehicle_assignment_proposals (proposal_id)
    ON DELETE CASCADE;

ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT fk_vapi_phase
    FOREIGN KEY (incident_phase_id)
    REFERENCES incident_phases (incident_phase_id)
    ON DELETE CASCADE;

ALTER TABLE vehicle_assignment_proposal_items
    ADD CONSTRAINT fk_vapi_vehicle
    FOREIGN KEY (vehicle_id)
    REFERENCES vehicles (vehicle_id)
    ON DELETE RESTRICT;

ALTER TABLE vehicle_assignment_proposal_missing
    ADD CONSTRAINT fk_vapm_proposal
    FOREIGN KEY (proposal_id)
    REFERENCES vehicle_assignment_proposals (proposal_id)
    ON DELETE CASCADE;

ALTER TABLE vehicle_assignment_proposal_missing
    ADD CONSTRAINT fk_vapm_phase
    FOREIGN KEY (incident_phase_id)
    REFERENCES incident_phases (incident_phase_id)
    ON DELETE CASCADE;

ALTER TABLE vehicle_assignment_proposal_missing
    ADD CONSTRAINT fk_vapm_vehicle_type
    FOREIGN KEY (vehicle_type_id)
    REFERENCES vehicle_types (vehicle_type_id)
    ON DELETE RESTRICT;

ALTER TABLE vehicle_assignment_proposal_missing
    ADD CONSTRAINT chk_vapm_missing_quantity_nonneg
    CHECK (missing_quantity >= 0);

ALTER TABLE vehicle_assignment_proposals
    ADD CONSTRAINT fk_vap_incident
    FOREIGN KEY (incident_id)
    REFERENCES incidents (incident_id)
    ON DELETE CASCADE;

ALTER TABLE vehicle_assignment_proposals
    ADD CONSTRAINT chk_vap_validation_xor
    CHECK (
        (validated_at IS NULL) OR (rejected_at IS NULL)
    );

-- =========================================================
-- 3) UNIQUES METIER
-- =========================================================

-- Empêche de dupliquer un groupe requirement avec le même label pour un même phase_type
ALTER TABLE phase_type_vehicle_requirement_groups
    ADD CONSTRAINT uq_ptrg_phase_type_label UNIQUE (phase_type_id, label);

-- unique global (incident_phase_id NULL)
CREATE UNIQUE INDEX IF NOT EXISTS uq_vapm_global
    ON vehicle_assignment_proposal_missing (proposal_id, vehicle_type_id)
    WHERE incident_phase_id IS NULL;

-- unique par phase
CREATE UNIQUE INDEX IF NOT EXISTS uq_vapm_by_phase
    ON vehicle_assignment_proposal_missing (proposal_id, incident_phase_id, vehicle_type_id)
    WHERE incident_phase_id IS NOT NULL;

-- =========================================================
-- 4) INDEX (perf sur FK + PostGIS)
-- =========================================================

-- Index FK classiques
CREATE INDEX IF NOT EXISTS idx_phase_types_category
    ON phase_types (phase_category_id);

CREATE INDEX IF NOT EXISTS idx_interest_points_kind
    ON interest_points (interest_point_kind_id);

CREATE INDEX IF NOT EXISTS idx_vehicles_vehicle_type
    ON vehicles (vehicle_type_id);

CREATE INDEX IF NOT EXISTS idx_vehicles_energy
    ON vehicles (energy_id);

CREATE INDEX IF NOT EXISTS idx_vehicles_base_interest_point
    ON vehicles (base_interest_point_id);

CREATE INDEX IF NOT EXISTS idx_vehicles_status
    ON vehicles (status_id);

CREATE INDEX IF NOT EXISTS idx_incident_phases_incident
    ON incident_phases (incident_id);

CREATE INDEX IF NOT EXISTS idx_incident_phases_phase_type
    ON incident_phases (phase_type_id);

CREATE INDEX IF NOT EXISTS idx_ipd_depends_on
    ON incident_phase_dependencies (depends_on_incident_phase_id);

CREATE INDEX IF NOT EXISTS idx_vehicle_assignments_phase
    ON vehicle_assignments (incident_phase_id);

CREATE INDEX IF NOT EXISTS idx_casualties_phase
    ON casualties (incident_phase_id);

CREATE INDEX IF NOT EXISTS idx_casualties_type
    ON casualties (casualty_type_id);

CREATE INDEX IF NOT EXISTS idx_vap_incident_generated_at
    ON vehicle_assignment_proposals (incident_id, generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_vapi_phase_score
    ON vehicle_assignment_proposal_items (incident_phase_id, score DESC);

CREATE INDEX IF NOT EXISTS idx_vapi_vehicle
    ON vehicle_assignment_proposal_items (vehicle_id);

CREATE INDEX IF NOT EXISTS idx_vapm_proposal
    ON vehicle_assignment_proposal_missing (proposal_id);

CREATE INDEX IF NOT EXISTS idx_reinforcement_phase
    ON reinforcement (incident_phase_id);

CREATE INDEX IF NOT EXISTS idx_rvr_vehicle_type
    ON reinforcement_vehicle_requests (vehicle_type_id);