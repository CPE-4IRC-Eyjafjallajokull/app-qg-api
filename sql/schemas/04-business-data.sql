/* =========================================================
   04_business_data.sql — BUSINESS DATA (SDMIS)
   ========================================================= */

-- ---------- OPERATORS ----------
INSERT INTO operators (operator_id, email) VALUES
    ('11111111-1111-1111-1111-111111111111'::uuid, 'dispatcher@sdmis.local'),
    ('22222222-2222-2222-2222-222222222222'::uuid, 'chief@sdmis.local'),
    ('33333333-3333-3333-3333-333333333333'::uuid, 'operator@sdmis.local')
ON CONFLICT (email) DO NOTHING;

-- ---------- INTEREST POINT CONSUMABLES ----------
INSERT INTO interest_point_consumables (
    interest_point_id,
    interest_point_consumable_type_id,
    current_quantity,
    last_update
)
SELECT
    ip.interest_point_id,
    ipct.interest_point_consumable_type_id,
    v.current_quantity,
    now()
FROM (
    VALUES
        ('Lyon-Gerland', 'Ressource humaine', 55),
        ('Lyon-Gerland', 'Places véhicules', 18),
        ('Lyon-Corneille', 'Ressource humaine', 40),
        ('Lyon-Corneille', 'Places véhicules', 14),
        ('Lyon-Confluence', 'Ressource humaine', 35),
        ('Lyon-Confluence', 'Places véhicules', 12),
        ('Hôpital Édouard-Herriot', 'Lits', 120),
        ('Hôpital de la Croix-Rousse', 'Lits', 80),
        ('Centre hospitalier Saint-Joseph - Saint-Luc', 'Lits', 90),
        ('Hôpital des Charpennes', 'Lits', 60),
        ('Médipôle Lyon-Villeurbanne', 'Lits', 110)
) AS v(point_name, consumable_label, current_quantity)
JOIN interest_points ip ON ip.name = v.point_name
JOIN interest_point_consumable_types ipct ON ipct.label = v.consumable_label
ON CONFLICT (interest_point_id, interest_point_consumable_type_id) DO NOTHING;

-- ---------- VEHICLES ----------
WITH vehicle_seed AS (
    SELECT * FROM (VALUES
        ('10000000-0000-0000-0000-000000000001'::uuid, 'FPT', 'SD-101-FR', 'Gazole', 0.92, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-000000000002'::uuid, 'VSAV', 'SD-202-FR', 'Gazole', 0.76, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000003'::uuid, 'VLM', 'SD-203-FR', 'Essence', 0.64, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000004'::uuid, 'VSR', 'SD-304-FR', 'Gazole', 0.81, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-000000000005'::uuid, 'EPA', 'SD-405-FR', 'Gazole', 0.88, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000006'::uuid, 'VPI', 'SD-506-FR', 'Essence', 0.57, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-000000000007'::uuid, 'CCF', 'SD-607-FR', 'Gazole', 0.93, 'Lyon-Duchère', 'Disponible'),
        ('10000000-0000-0000-0000-000000000008'::uuid, 'VIRT', 'SD-708-FR', 'Gazole', 0.71, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-000000000009'::uuid, 'VLCG', 'SD-809-FR', 'Gazole', 0.66, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-00000000000a'::uuid, 'VTU', 'SD-910-FR', 'Gazole', 0.83, 'Lyon-Rochat', 'Disponible'),
        ('10000000-0000-0000-0000-00000000000b'::uuid, 'VLR', 'SD-111-FR', 'Gazole', 0.79, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-00000000000c'::uuid, 'PC Mobile', 'SD-212-FR', 'Gazole', 0.72, 'SDMIS Lyon (Direction)', 'Disponible')
    ) AS v(vehicle_id, vehicle_code, immatriculation, energy_label, energy_level, base_point_name, status_label)
)
INSERT INTO vehicles (
    vehicle_id,
    vehicle_type_id,
    immatriculation,
    energy_id,
    energy_level,
    base_interest_point_id,
    status_id
)
SELECT
    v.vehicle_id,
    vt.vehicle_type_id,
    v.immatriculation,
    e.energy_id,
    v.energy_level,
    ip.interest_point_id,
    vs.vehicle_status_id
FROM vehicle_seed v
JOIN vehicle_types vt ON vt.code = v.vehicle_code
JOIN energies e ON e.label = v.energy_label
JOIN interest_points ip ON ip.name = v.base_point_name
JOIN vehicle_status vs ON vs.label = v.status_label
ON CONFLICT (immatriculation) DO NOTHING;

-- ---------- VEHICLE TYPE CONSUMABLE SPECS ----------
INSERT INTO vehicle_type_consumable_specs (
    vehicle_type_id,
    consumable_type_id,
    capacity_quantity,
    initial_quantity,
    is_applicable
)
SELECT
    vt.vehicle_type_id,
    vct.vehicle_consumable_type_id,
    v.capacity_quantity,
    v.initial_quantity,
    v.is_applicable
FROM (
    VALUES
        ('FPT', 'Eau', 2000, 2000, true),
        ('FPT', 'Mousse', 200, 200, true),
        ('FPT', 'Bouteille oxygène', 6, 6, true),
        ('VSAV', 'Compresse', 120, 120, true),
        ('VSAV', 'Pansement', 80, 80, true),
        ('VSAV', 'Oxygène médical', 500, 500, true),
        ('VSAV', 'Masque oxygène', 20, 20, true),
        ('VSAV', 'Couverture de survie', 30, 30, true),
        ('VSR', 'Bouteille oxygène', 4, 4, true),
        ('VPI', 'Eau', 400, 400, true),
        ('CCF', 'Eau', 3500, 3500, true),
        ('CCGC', 'Eau', 12000, 12000, true),
        ('VIRT', 'Désinfectant', 50, 50, true),
        ('VLR', 'Groupe électrogène', 1, 1, true),
        ('PC Mobile', 'Groupe électrogène', 1, 1, true)
    ) AS v(vehicle_code, consumable_label, capacity_quantity, initial_quantity, is_applicable)
JOIN vehicle_types vt ON vt.code = v.vehicle_code
JOIN vehicle_consumable_types vct ON vct.label = v.consumable_label
ON CONFLICT (vehicle_type_id, consumable_type_id) DO NOTHING;

-- ---------- VEHICLE CONSUMABLE STOCK ----------
INSERT INTO vehicle_consumables_stock (
    vehicle_id,
    consumable_type_id,
    current_quantity,
    last_update
)
SELECT
    v.vehicle_id,
    vct.vehicle_consumable_type_id,
    s.current_quantity,
    now()
FROM (
    VALUES
        ('SD-101-FR', 'Eau', 1850),
        ('SD-101-FR', 'Mousse', 180),
        ('SD-101-FR', 'Bouteille oxygène', 5),
        ('SD-202-FR', 'Compresse', 110),
        ('SD-202-FR', 'Pansement', 70),
        ('SD-202-FR', 'Oxygène médical', 420),
        ('SD-202-FR', 'Masque oxygène', 18),
        ('SD-202-FR', 'Couverture de survie', 26),
        ('SD-304-FR', 'Bouteille oxygène', 3),
        ('SD-506-FR', 'Eau', 320),
        ('SD-607-FR', 'Eau', 3200)
    ) AS s(immatriculation, consumable_label, current_quantity)
JOIN vehicles v ON v.immatriculation = s.immatriculation
JOIN vehicle_consumable_types vct ON vct.label = s.consumable_label
ON CONFLICT (vehicle_id, consumable_type_id) DO NOTHING;

-- ---------- PHASE TYPE REQUIREMENTS (GROUPS + VEHICLES) ----------
-- Définition complète des besoins véhicules pour chaque type de phase
-- Basé sur les standards d'intervention des sapeurs-pompiers français

INSERT INTO phase_type_vehicle_requirement_groups (
    group_id,
    phase_type_id,
    label,
    rule,
    min_total,
    max_total,
    priority,
    is_hard
)
SELECT
    v.group_id,
    pt.phase_type_id,
    v.label,
    v.rule::requirement_rule,
    v.min_total,
    v.max_total,
    v.priority,
    v.is_hard
FROM (
    VALUES
        -- ========== INCENDIES (FIRE) ==========
        -- Feu d'habitation - intervention lourde
        ('26000000-0000-0000-0000-000000000001'::uuid, 'FIRE_HABITATION', 'FIRE_HAB_CORE', 'ALL', 3, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000002'::uuid, 'FIRE_HABITATION', 'FIRE_HAB_SUPPORT', 'ANY', 1, NULL::integer, 2, false),
        
        -- Feu d'appartement - intervention standard
        ('26000000-0000-0000-0000-000000000003'::uuid, 'FIRE_APARTMENT', 'FIRE_APT_CORE', 'ALL', 2, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000004'::uuid, 'FIRE_APARTMENT', 'FIRE_APT_SUPPORT', 'ANY', 1, NULL::integer, 2, false),
        
        -- Feu industriel - intervention majeure
        ('26000000-0000-0000-0000-000000000005'::uuid, 'FIRE_INDUSTRIAL', 'FIRE_IND_CORE', 'ALL', 4, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000006'::uuid, 'FIRE_INDUSTRIAL', 'FIRE_IND_COMMAND', 'ALL', 1, NULL::integer, 2, true),
        ('26000000-0000-0000-0000-000000000007'::uuid, 'FIRE_INDUSTRIAL', 'FIRE_IND_SUPPORT', 'ANY', 2, NULL::integer, 3, false),
        
        -- Feu sur voie publique - intervention légère
        ('26000000-0000-0000-0000-000000000008'::uuid, 'FIRE_PUBLIC_SPACE', 'FIRE_PUB_CORE', 'ALL', 1, NULL::integer, 1, true),
        
        -- Feu de forêt/végétation - intervention spécialisée
        ('26000000-0000-0000-0000-000000000009'::uuid, 'FIRE_WILDLAND', 'FIRE_WILD_CORE', 'ALL', 2, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-00000000000a'::uuid, 'FIRE_WILDLAND', 'FIRE_WILD_SUPPORT', 'ANY', 1, NULL::integer, 2, false),
        
        -- Feu de sous-sol/local technique
        ('26000000-0000-0000-0000-00000000000b'::uuid, 'FIRE_BASEMENT', 'FIRE_BASE_CORE', 'ALL', 2, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-00000000000c'::uuid, 'FIRE_BASEMENT', 'FIRE_BASE_SUPPORT', 'ANY', 1, NULL::integer, 2, false),
        
        -- Feu de cheminée - intervention légère
        ('26000000-0000-0000-0000-00000000000d'::uuid, 'FIRE_CHIMNEY', 'FIRE_CHIM_CORE', 'ALL', 1, NULL::integer, 1, true),
        
        -- Explosion/risque d'explosion - intervention critique
        ('26000000-0000-0000-0000-00000000000e'::uuid, 'FIRE_EXPLOSION_RISK', 'FIRE_EXPL_CORE', 'ALL', 3, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-00000000000f'::uuid, 'FIRE_EXPLOSION_RISK', 'FIRE_EXPL_COMMAND', 'ALL', 1, NULL::integer, 2, true),
        ('26000000-0000-0000-0000-000000000010'::uuid, 'FIRE_EXPLOSION_RISK', 'FIRE_EXPL_SUPPORT', 'ANY', 2, NULL::integer, 3, false),

        -- ========== RISQUES TECHNOLOGIQUES (HAZMAT) ==========
        -- Fuite de gaz / odeur suspecte
        ('26000000-0000-0000-0000-000000000011'::uuid, 'HAZ_GAS_LEAK', 'HAZ_GAS_CORE', 'ALL', 2, NULL::integer, 1, true),
        
        -- Fuite de produit chimique
        ('26000000-0000-0000-0000-000000000012'::uuid, 'HAZ_CHEMICAL_LEAK', 'HAZ_CHEM_CORE', 'ALL', 2, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000013'::uuid, 'HAZ_CHEMICAL_LEAK', 'HAZ_CHEM_SUPPORT', 'ANY', 1, NULL::integer, 2, false),
        
        -- Fuite de carburant
        ('26000000-0000-0000-0000-000000000014'::uuid, 'HAZ_FUEL_LEAK', 'HAZ_FUEL_CORE', 'ALL', 1, NULL::integer, 1, true),
        
        -- Pollution de cours d'eau
        ('26000000-0000-0000-0000-000000000015'::uuid, 'ENV_WATER_POLLUTION', 'ENV_POLL_CORE', 'ALL', 1, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000016'::uuid, 'ENV_WATER_POLLUTION', 'ENV_POLL_SUPPORT', 'ANY', 1, NULL::integer, 2, false),

        -- ========== SECOURS À PERSONNE (SAP) ==========
        -- Malaise
        ('26000000-0000-0000-0000-000000000017'::uuid, 'SAP_MALAISE', 'SAP_MAL_CORE', 'ALL', 1, NULL::integer, 1, true),
        
        -- Arrêt cardiaque - intervention critique
        ('26000000-0000-0000-0000-000000000018'::uuid, 'SAP_CARDIAC_ARREST', 'SAP_CA_CORE', 'ALL', 2, NULL::integer, 1, true),
        
        -- Traumatisme
        ('26000000-0000-0000-0000-000000000019'::uuid, 'SAP_TRAUMA', 'SAP_TRAUMA_CORE', 'ALL', 1, NULL::integer, 1, true),
        
        -- Hémorragie
        ('26000000-0000-0000-0000-00000000001a'::uuid, 'SAP_HEMORRHAGE', 'SAP_HEM_CORE', 'ALL', 1, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-00000000001b'::uuid, 'SAP_HEMORRHAGE', 'SAP_HEM_SUPPORT', 'ANY', 1, NULL::integer, 2, false),
        
        -- Accouchement inopiné
        ('26000000-0000-0000-0000-00000000001c'::uuid, 'SAP_CHILDBIRTH', 'SAP_CHILD_CORE', 'ALL', 2, NULL::integer, 1, true),
        
        -- Personne coincée / relevage
        ('26000000-0000-0000-0000-00000000001d'::uuid, 'RESC_PERSON_TRAPPED', 'RESC_TRAP_CORE', 'ALL', 2, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-00000000001e'::uuid, 'RESC_PERSON_TRAPPED', 'RESC_TRAP_SUPPORT', 'ANY', 1, NULL::integer, 2, false),
        
        -- Intoxication (fumées, CO, chimiques)
        ('26000000-0000-0000-0000-00000000001f'::uuid, 'SAP_INTOXICATION', 'SAP_INTOX_CORE', 'ALL', 2, NULL::integer, 1, true),

        -- ========== ACCIDENTS ==========
        -- Accident avec matières dangereuses
        ('26000000-0000-0000-0000-000000000020'::uuid, 'ACC_HAZMAT', 'ACC_HAZ_CORE', 'ALL', 3, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000021'::uuid, 'ACC_HAZMAT', 'ACC_HAZ_COMMAND', 'ALL', 1, NULL::integer, 2, true),
        ('26000000-0000-0000-0000-000000000022'::uuid, 'ACC_HAZMAT', 'ACC_HAZ_SUPPORT', 'ANY', 2, NULL::integer, 3, false),
        
        -- Accident de la circulation
        ('26000000-0000-0000-0000-000000000023'::uuid, 'ACC_ROAD', 'ACC_ROAD_CORE', 'ALL', 2, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000024'::uuid, 'ACC_ROAD', 'ACC_ROAD_SUPPORT', 'ANY', 1, NULL::integer, 2, false),
        
        -- Collision train / véhicule
        ('26000000-0000-0000-0000-000000000025'::uuid, 'ACC_TRAIN_COLLISION', 'ACC_TRAIN_CORE', 'ALL', 4, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000026'::uuid, 'ACC_TRAIN_COLLISION', 'ACC_TRAIN_COMMAND', 'ALL', 1, NULL::integer, 2, true),
        ('26000000-0000-0000-0000-000000000027'::uuid, 'ACC_TRAIN_COLLISION', 'ACC_TRAIN_SUPPORT', 'ANY', 2, NULL::integer, 3, false),
        
        -- Déraillement / incident ferroviaire
        ('26000000-0000-0000-0000-000000000028'::uuid, 'ACC_RAIL_INCIDENT', 'ACC_RAIL_CORE', 'ALL', 4, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000029'::uuid, 'ACC_RAIL_INCIDENT', 'ACC_RAIL_COMMAND', 'ALL', 1, NULL::integer, 2, true),
        ('26000000-0000-0000-0000-00000000002a'::uuid, 'ACC_RAIL_INCIDENT', 'ACC_RAIL_SUPPORT', 'ANY', 2, NULL::integer, 3, false),
        
        -- Accident aérien (léger, drone)
        ('26000000-0000-0000-0000-00000000002b'::uuid, 'ACC_AIRCRAFT', 'ACC_AIR_CORE', 'ALL', 3, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-00000000002c'::uuid, 'ACC_AIRCRAFT', 'ACC_AIR_COMMAND', 'ALL', 1, NULL::integer, 2, true),
        ('26000000-0000-0000-0000-00000000002d'::uuid, 'ACC_AIRCRAFT', 'ACC_AIR_SUPPORT', 'ANY', 2, NULL::integer, 3, false),
        
        -- Accident industriel
        ('26000000-0000-0000-0000-00000000002e'::uuid, 'ACC_INDUSTRIAL', 'ACC_IND_CORE', 'ALL', 4, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-00000000002f'::uuid, 'ACC_INDUSTRIAL', 'ACC_IND_COMMAND', 'ALL', 1, NULL::integer, 2, true),
        ('26000000-0000-0000-0000-000000000030'::uuid, 'ACC_INDUSTRIAL', 'ACC_IND_SUPPORT', 'ANY', 2, NULL::integer, 3, false),

        -- ========== SECOURS DIVERS (MISC_RESCUE) ==========
        -- Inondation
        ('26000000-0000-0000-0000-000000000031'::uuid, 'ENV_FLOODING', 'ENV_FLOOD_CORE', 'ALL', 2, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000032'::uuid, 'ENV_FLOODING', 'ENV_FLOOD_SUPPORT', 'ANY', 1, NULL::integer, 2, false),
        
        -- Dégâts des eaux
        ('26000000-0000-0000-0000-000000000033'::uuid, 'ENV_WATER_DAMAGE', 'ENV_WDAM_CORE', 'ALL', 1, NULL::integer, 1, true),
        
        -- Sauvetage d'animaux
        ('26000000-0000-0000-0000-000000000034'::uuid, 'RESC_ANIMAL', 'RESC_ANIM_CORE', 'ALL', 1, NULL::integer, 1, true),
        
        -- Nids de guêpes / frelons
        ('26000000-0000-0000-0000-000000000035'::uuid, 'TECH_INSECTS', 'TECH_INS_CORE', 'ALL', 1, NULL::integer, 1, true),
        
        -- Sauvetage aquatique
        ('26000000-0000-0000-0000-000000000036'::uuid, 'RESC_WATER', 'RESC_WATER_CORE', 'ALL', 2, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-000000000037'::uuid, 'RESC_WATER', 'RESC_WATER_SUPPORT', 'ANY', 1, NULL::integer, 2, false),
        
        -- Personne bloquée dans un ascenseur
        ('26000000-0000-0000-0000-000000000038'::uuid, 'TECH_ELEVATOR', 'TECH_ELEV_CORE', 'ALL', 1, NULL::integer, 1, true),
        
        -- Déblai / bâchage après intempéries
        ('26000000-0000-0000-0000-000000000039'::uuid, 'ENV_POST_STORM', 'ENV_STORM_CORE', 'ALL', 1, NULL::integer, 1, true),
        ('26000000-0000-0000-0000-00000000003a'::uuid, 'ENV_POST_STORM', 'ENV_STORM_SUPPORT', 'ANY', 1, NULL::integer, 2, false)
        
    ) AS v(group_id, phase_code, label, rule, min_total, max_total, priority, is_hard)
JOIN phase_types pt ON pt.code = v.phase_code
ON CONFLICT (group_id) DO NOTHING;

-- Insertion des véhicules requis pour chaque groupe
INSERT INTO phase_type_vehicle_requirements (
    group_id,
    vehicle_type_id,
    min_quantity,
    max_quantity,
    mandatory,
    preference_rank
)
SELECT
    g.group_id,
    vt.vehicle_type_id,
    v.min_quantity,
    v.max_quantity,
    v.mandatory,
    v.preference_rank
FROM (
    VALUES
        -- ========== INCENDIES (FIRE) ==========
        
        -- FIRE_HABITATION - Feu d'habitation (intervention lourde)
        ('FIRE_HAB_CORE', 'FIRE_HABITATION', 'FPT', 2, NULL::integer, true, 1),      -- 2 FPT obligatoires
        ('FIRE_HAB_CORE', 'FIRE_HABITATION', 'EPA', 1, NULL::integer, true, 2),      -- 1 échelle obligatoire
        ('FIRE_HAB_CORE', 'FIRE_HABITATION', 'VSAV', 1, NULL::integer, true, 3),     -- 1 VSAV pour victimes potentielles
        ('FIRE_HAB_SUPPORT', 'FIRE_HABITATION', 'CCGC', 1, NULL::integer, false, 1), -- Citerne en renfort
        ('FIRE_HAB_SUPPORT', 'FIRE_HABITATION', 'VLCG', 1, NULL::integer, false, 2), -- Commandement si besoin
        ('FIRE_HAB_SUPPORT', 'FIRE_HABITATION', 'VLM', 1, NULL::integer, false, 3),  -- Médecin en renfort
        
        -- FIRE_APARTMENT - Feu d'appartement (intervention standard)
        ('FIRE_APT_CORE', 'FIRE_APARTMENT', 'FPT', 1, NULL::integer, true, 1),       -- 1 FPT obligatoire
        ('FIRE_APT_CORE', 'FIRE_APARTMENT', 'EPA', 1, NULL::integer, true, 2),       -- 1 échelle obligatoire
        ('FIRE_APT_SUPPORT', 'FIRE_APARTMENT', 'VSAV', 1, NULL::integer, false, 1),  -- VSAV en soutien
        ('FIRE_APT_SUPPORT', 'FIRE_APARTMENT', 'VLM', 1, NULL::integer, false, 2),   -- VLM si victimes
        
        -- FIRE_INDUSTRIAL - Feu industriel (intervention majeure)
        ('FIRE_IND_CORE', 'FIRE_INDUSTRIAL', 'FPT', 2, NULL::integer, true, 1),      -- 2 FPT obligatoires
        ('FIRE_IND_CORE', 'FIRE_INDUSTRIAL', 'CCGC', 1, NULL::integer, true, 2),     -- Grande citerne obligatoire
        ('FIRE_IND_CORE', 'FIRE_INDUSTRIAL', 'EPA', 1, NULL::integer, true, 3),      -- Échelle obligatoire
        ('FIRE_IND_CORE', 'FIRE_INDUSTRIAL', 'VIRT', 1, NULL::integer, true, 4),     -- Risques techno obligatoire
        ('FIRE_IND_COMMAND', 'FIRE_INDUSTRIAL', 'VLCG', 1, NULL::integer, true, 1),  -- Commandement obligatoire
        ('FIRE_IND_COMMAND', 'FIRE_INDUSTRIAL', 'PC Mobile', 1, NULL::integer, false, 2), -- PC si situation évolue
        ('FIRE_IND_SUPPORT', 'FIRE_INDUSTRIAL', 'VSAV', 2, NULL::integer, false, 1), -- 2 VSAV en soutien
        ('FIRE_IND_SUPPORT', 'FIRE_INDUSTRIAL', 'VLM', 1, NULL::integer, false, 2),  -- Médecin
        ('FIRE_IND_SUPPORT', 'FIRE_INDUSTRIAL', 'CCF', 1, NULL::integer, false, 3),  -- Renfort citerne
        
        -- FIRE_PUBLIC_SPACE - Feu sur voie publique (intervention légère)
        ('FIRE_PUB_CORE', 'FIRE_PUBLIC_SPACE', 'VPI', 1, NULL::integer, true, 1),    -- 1 VPI suffit souvent
        ('FIRE_PUB_CORE', 'FIRE_PUBLIC_SPACE', 'FPT', 1, NULL::integer, false, 2),   -- FPT si nécessaire
        
        -- FIRE_WILDLAND - Feu de forêt/végétation
        ('FIRE_WILD_CORE', 'FIRE_WILDLAND', 'CCF', 2, NULL::integer, true, 1),       -- 2 CCF obligatoires (spécialisés feux forêt)
        ('FIRE_WILD_CORE', 'FIRE_WILDLAND', 'VPI', 1, NULL::integer, true, 2),       -- VPI pour reconnaissance
        ('FIRE_WILD_SUPPORT', 'FIRE_WILDLAND', 'CCGC', 1, NULL::integer, false, 1),  -- Grande citerne en renfort
        ('FIRE_WILD_SUPPORT', 'FIRE_WILDLAND', 'VLCG', 1, NULL::integer, false, 2),  -- Commandement
        ('FIRE_WILD_SUPPORT', 'FIRE_WILDLAND', 'VTU', 1, NULL::integer, false, 3),   -- Transport/logistique
        
        -- FIRE_BASEMENT - Feu de sous-sol/local technique
        ('FIRE_BASE_CORE', 'FIRE_BASEMENT', 'FPT', 2, NULL::integer, true, 1),       -- 2 FPT (conditions difficiles)
        ('FIRE_BASE_CORE', 'FIRE_BASEMENT', 'VSAV', 1, NULL::integer, true, 2),      -- VSAV obligatoire (risque intox)
        ('FIRE_BASE_SUPPORT', 'FIRE_BASEMENT', 'VLM', 1, NULL::integer, false, 1),   -- Médecin si victimes
        ('FIRE_BASE_SUPPORT', 'FIRE_BASEMENT', 'EPA', 1, NULL::integer, false, 2),   -- Échelle en soutien
        
        -- FIRE_CHIMNEY - Feu de cheminée (intervention légère)
        ('FIRE_CHIM_CORE', 'FIRE_CHIMNEY', 'VPI', 1, NULL::integer, true, 1),        -- 1 VPI suffit généralement
        ('FIRE_CHIM_CORE', 'FIRE_CHIMNEY', 'FPT', 1, NULL::integer, false, 2),       -- FPT si propagation
        
        -- FIRE_EXPLOSION_RISK - Explosion/risque d'explosion (intervention critique)
        ('FIRE_EXPL_CORE', 'FIRE_EXPLOSION_RISK', 'FPT', 2, NULL::integer, true, 1),    -- 2 FPT obligatoires
        ('FIRE_EXPL_CORE', 'FIRE_EXPLOSION_RISK', 'VIRT', 1, NULL::integer, true, 2),   -- Risques techno obligatoire
        ('FIRE_EXPL_CORE', 'FIRE_EXPLOSION_RISK', 'VSAV', 2, NULL::integer, true, 3),   -- 2 VSAV obligatoires
        ('FIRE_EXPL_COMMAND', 'FIRE_EXPLOSION_RISK', 'VLCG', 1, NULL::integer, true, 1), -- Commandement obligatoire
        ('FIRE_EXPL_COMMAND', 'FIRE_EXPLOSION_RISK', 'PC Mobile', 1, NULL::integer, true, 2), -- PC obligatoire
        ('FIRE_EXPL_SUPPORT', 'FIRE_EXPLOSION_RISK', 'EPA', 1, NULL::integer, false, 1), -- Échelle en renfort
        ('FIRE_EXPL_SUPPORT', 'FIRE_EXPLOSION_RISK', 'CCGC', 1, NULL::integer, false, 2), -- Citerne en renfort
        ('FIRE_EXPL_SUPPORT', 'FIRE_EXPLOSION_RISK', 'VLM', 1, NULL::integer, false, 3), -- Médecin

        -- ========== RISQUES TECHNOLOGIQUES (HAZMAT) ==========
        
        -- HAZ_GAS_LEAK - Fuite de gaz / odeur suspecte
        ('HAZ_GAS_CORE', 'HAZ_GAS_LEAK', 'FPT', 1, NULL::integer, true, 1),          -- FPT pour reconnaissance
        ('HAZ_GAS_CORE', 'HAZ_GAS_LEAK', 'VIRT', 1, NULL::integer, true, 2),         -- VIRT obligatoire (détection)
        
        -- HAZ_CHEMICAL_LEAK - Fuite de produit chimique
        ('HAZ_CHEM_CORE', 'HAZ_CHEMICAL_LEAK', 'VIRT', 1, NULL::integer, true, 1),   -- VIRT obligatoire
        ('HAZ_CHEM_CORE', 'HAZ_CHEMICAL_LEAK', 'FPT', 1, NULL::integer, true, 2),    -- FPT soutien
        ('HAZ_CHEM_SUPPORT', 'HAZ_CHEMICAL_LEAK', 'VSAV', 1, NULL::integer, false, 1), -- VSAV si victimes
        ('HAZ_CHEM_SUPPORT', 'HAZ_CHEMICAL_LEAK', 'VLCG', 1, NULL::integer, false, 2), -- Commandement
        
        -- HAZ_FUEL_LEAK - Fuite de carburant
        ('HAZ_FUEL_CORE', 'HAZ_FUEL_LEAK', 'FPT', 1, NULL::integer, true, 1),        -- FPT avec mousse
        ('HAZ_FUEL_CORE', 'HAZ_FUEL_LEAK', 'VPI', 1, NULL::integer, false, 2),       -- VPI reconnaissance
        
        -- ENV_WATER_POLLUTION - Pollution de cours d'eau
        ('ENV_POLL_CORE', 'ENV_WATER_POLLUTION', 'VTU', 1, NULL::integer, true, 1),  -- VTU avec matériel antipollution
        ('ENV_POLL_CORE', 'ENV_WATER_POLLUTION', 'VIRT', 1, NULL::integer, false, 2), -- VIRT si produits dangereux
        ('ENV_POLL_SUPPORT', 'ENV_WATER_POLLUTION', 'VLR', 1, NULL::integer, false, 1), -- Logistique

        -- ========== SECOURS À PERSONNE (SAP) ==========
        
        -- SAP_MALAISE - Malaise (intervention standard)
        ('SAP_MAL_CORE', 'SAP_MALAISE', 'VSAV', 1, NULL::integer, true, 1),          -- 1 VSAV suffit
        
        -- SAP_CARDIAC_ARREST - Arrêt cardiaque (intervention critique)
        ('SAP_CA_CORE', 'SAP_CARDIAC_ARREST', 'VSAV', 1, NULL::integer, true, 1),    -- VSAV obligatoire
        ('SAP_CA_CORE', 'SAP_CARDIAC_ARREST', 'VLM', 1, NULL::integer, true, 2),     -- VLM médecin obligatoire
        
        -- SAP_TRAUMA - Traumatisme
        ('SAP_TRAUMA_CORE', 'SAP_TRAUMA', 'VSAV', 1, NULL::integer, true, 1),        -- VSAV obligatoire
        ('SAP_TRAUMA_CORE', 'SAP_TRAUMA', 'VLM', 1, NULL::integer, false, 2),        -- VLM si grave
        
        -- SAP_HEMORRHAGE - Hémorragie
        ('SAP_HEM_CORE', 'SAP_HEMORRHAGE', 'VSAV', 1, NULL::integer, true, 1),       -- VSAV obligatoire
        ('SAP_HEM_SUPPORT', 'SAP_HEMORRHAGE', 'VLM', 1, NULL::integer, false, 1),    -- VLM si hémorragie grave
        
        -- SAP_CHILDBIRTH - Accouchement inopiné
        ('SAP_CHILD_CORE', 'SAP_CHILDBIRTH', 'VSAV', 1, NULL::integer, true, 1),     -- VSAV obligatoire
        ('SAP_CHILD_CORE', 'SAP_CHILDBIRTH', 'VLM', 1, NULL::integer, true, 2),      -- VLM médecin obligatoire
        
        -- RESC_PERSON_TRAPPED - Personne coincée / relevage
        ('RESC_TRAP_CORE', 'RESC_PERSON_TRAPPED', 'VSR', 1, NULL::integer, true, 1), -- VSR obligatoire
        ('RESC_TRAP_CORE', 'RESC_PERSON_TRAPPED', 'VSAV', 1, NULL::integer, true, 2), -- VSAV obligatoire
        ('RESC_TRAP_SUPPORT', 'RESC_PERSON_TRAPPED', 'FPT', 1, NULL::integer, false, 1), -- FPT si besoin matériel
        ('RESC_TRAP_SUPPORT', 'RESC_PERSON_TRAPPED', 'VLM', 1, NULL::integer, false, 2), -- VLM si grave
        
        -- SAP_INTOXICATION - Intoxication (fumées, CO, chimiques)
        ('SAP_INTOX_CORE', 'SAP_INTOXICATION', 'VSAV', 1, NULL::integer, true, 1),   -- VSAV obligatoire
        ('SAP_INTOX_CORE', 'SAP_INTOXICATION', 'VLM', 1, NULL::integer, true, 2),    -- VLM obligatoire (oxygénothérapie)

        -- ========== ACCIDENTS ==========
        
        -- ACC_HAZMAT - Accident avec matières dangereuses
        ('ACC_HAZ_CORE', 'ACC_HAZMAT', 'VIRT', 1, NULL::integer, true, 1),           -- VIRT obligatoire
        ('ACC_HAZ_CORE', 'ACC_HAZMAT', 'VSR', 1, NULL::integer, true, 2),            -- VSR obligatoire
        ('ACC_HAZ_CORE', 'ACC_HAZMAT', 'VSAV', 2, NULL::integer, true, 3),           -- 2 VSAV obligatoires
        ('ACC_HAZ_COMMAND', 'ACC_HAZMAT', 'VLCG', 1, NULL::integer, true, 1),        -- Commandement obligatoire
        ('ACC_HAZ_COMMAND', 'ACC_HAZMAT', 'PC Mobile', 1, NULL::integer, false, 2),  -- PC si situation évolue
        ('ACC_HAZ_SUPPORT', 'ACC_HAZMAT', 'FPT', 1, NULL::integer, false, 1),        -- FPT en soutien
        ('ACC_HAZ_SUPPORT', 'ACC_HAZMAT', 'VLM', 1, NULL::integer, false, 2),        -- Médecin
        
        -- ACC_ROAD - Accident de la circulation
        ('ACC_ROAD_CORE', 'ACC_ROAD', 'VSR', 1, NULL::integer, true, 1),             -- VSR obligatoire
        ('ACC_ROAD_CORE', 'ACC_ROAD', 'VSAV', 1, NULL::integer, true, 2),            -- VSAV obligatoire
        ('ACC_ROAD_SUPPORT', 'ACC_ROAD', 'VLM', 1, NULL::integer, false, 1),         -- VLM si victime grave
        ('ACC_ROAD_SUPPORT', 'ACC_ROAD', 'FPT', 1, NULL::integer, false, 2),         -- FPT si risque incendie
        
        -- ACC_TRAIN_COLLISION - Collision train / véhicule
        ('ACC_TRAIN_CORE', 'ACC_TRAIN_COLLISION', 'VSR', 2, NULL::integer, true, 1), -- 2 VSR obligatoires
        ('ACC_TRAIN_CORE', 'ACC_TRAIN_COLLISION', 'VSAV', 2, NULL::integer, true, 2), -- 2 VSAV obligatoires
        ('ACC_TRAIN_CORE', 'ACC_TRAIN_COLLISION', 'FPT', 1, NULL::integer, true, 3), -- FPT obligatoire
        ('ACC_TRAIN_CORE', 'ACC_TRAIN_COLLISION', 'EPA', 1, NULL::integer, true, 4), -- Échelle obligatoire
        ('ACC_TRAIN_COMMAND', 'ACC_TRAIN_COLLISION', 'VLCG', 1, NULL::integer, true, 1), -- Commandement obligatoire
        ('ACC_TRAIN_COMMAND', 'ACC_TRAIN_COLLISION', 'PC Mobile', 1, NULL::integer, true, 2), -- PC obligatoire
        ('ACC_TRAIN_SUPPORT', 'ACC_TRAIN_COLLISION', 'VLM', 2, NULL::integer, false, 1), -- 2 médecins en soutien
        ('ACC_TRAIN_SUPPORT', 'ACC_TRAIN_COLLISION', 'CCGC', 1, NULL::integer, false, 2), -- Citerne en renfort
        
        -- ACC_RAIL_INCIDENT - Déraillement / incident ferroviaire
        ('ACC_RAIL_CORE', 'ACC_RAIL_INCIDENT', 'VSR', 2, NULL::integer, true, 1),    -- 2 VSR obligatoires
        ('ACC_RAIL_CORE', 'ACC_RAIL_INCIDENT', 'VSAV', 2, NULL::integer, true, 2),   -- 2 VSAV obligatoires
        ('ACC_RAIL_CORE', 'ACC_RAIL_INCIDENT', 'FPT', 2, NULL::integer, true, 3),    -- 2 FPT obligatoires
        ('ACC_RAIL_CORE', 'ACC_RAIL_INCIDENT', 'EPA', 1, NULL::integer, true, 4),    -- Échelle obligatoire
        ('ACC_RAIL_COMMAND', 'ACC_RAIL_INCIDENT', 'VLCG', 1, NULL::integer, true, 1), -- Commandement obligatoire
        ('ACC_RAIL_COMMAND', 'ACC_RAIL_INCIDENT', 'PC Mobile', 1, NULL::integer, true, 2), -- PC obligatoire
        ('ACC_RAIL_SUPPORT', 'ACC_RAIL_INCIDENT', 'VLM', 2, NULL::integer, false, 1), -- 2 médecins en soutien
        ('ACC_RAIL_SUPPORT', 'ACC_RAIL_INCIDENT', 'VIRT', 1, NULL::integer, false, 2), -- VIRT si matières dangereuses
        
        -- ACC_AIRCRAFT - Accident aérien (léger, drone)
        ('ACC_AIR_CORE', 'ACC_AIRCRAFT', 'FPT', 2, NULL::integer, true, 1),          -- 2 FPT obligatoires
        ('ACC_AIR_CORE', 'ACC_AIRCRAFT', 'VSAV', 2, NULL::integer, true, 2),         -- 2 VSAV obligatoires
        ('ACC_AIR_CORE', 'ACC_AIRCRAFT', 'VSR', 1, NULL::integer, true, 3),          -- VSR obligatoire
        ('ACC_AIR_COMMAND', 'ACC_AIRCRAFT', 'VLCG', 1, NULL::integer, true, 1),      -- Commandement obligatoire
        ('ACC_AIR_COMMAND', 'ACC_AIRCRAFT', 'PC Mobile', 1, NULL::integer, true, 2), -- PC obligatoire
        ('ACC_AIR_SUPPORT', 'ACC_AIRCRAFT', 'VLM', 1, NULL::integer, false, 1),      -- Médecin en renfort
        ('ACC_AIR_SUPPORT', 'ACC_AIRCRAFT', 'CCF', 1, NULL::integer, false, 2),      -- Citerne si besoin
        
        -- ACC_INDUSTRIAL - Accident industriel
        ('ACC_IND_CORE', 'ACC_INDUSTRIAL', 'FPT', 2, NULL::integer, true, 1),        -- 2 FPT obligatoires
        ('ACC_IND_CORE', 'ACC_INDUSTRIAL', 'VIRT', 1, NULL::integer, true, 2),       -- VIRT obligatoire
        ('ACC_IND_CORE', 'ACC_INDUSTRIAL', 'VSAV', 2, NULL::integer, true, 3),       -- 2 VSAV obligatoires
        ('ACC_IND_CORE', 'ACC_INDUSTRIAL', 'VSR', 1, NULL::integer, true, 4),        -- VSR obligatoire
        ('ACC_IND_COMMAND', 'ACC_INDUSTRIAL', 'VLCG', 1, NULL::integer, true, 1),    -- Commandement obligatoire
        ('ACC_IND_COMMAND', 'ACC_INDUSTRIAL', 'PC Mobile', 1, NULL::integer, true, 2), -- PC obligatoire
        ('ACC_IND_SUPPORT', 'ACC_INDUSTRIAL', 'CCGC', 1, NULL::integer, false, 1),   -- Citerne en renfort
        ('ACC_IND_SUPPORT', 'ACC_INDUSTRIAL', 'VLM', 2, NULL::integer, false, 2),    -- 2 médecins en soutien
        ('ACC_IND_SUPPORT', 'ACC_INDUSTRIAL', 'EPA', 1, NULL::integer, false, 3),    -- Échelle si besoin

        -- ========== SECOURS DIVERS (MISC_RESCUE) ==========
        
        -- ENV_FLOODING - Inondation
        ('ENV_FLOOD_CORE', 'ENV_FLOODING', 'VTU', 1, NULL::integer, true, 1),        -- VTU obligatoire
        ('ENV_FLOOD_CORE', 'ENV_FLOODING', 'FPT', 1, NULL::integer, true, 2),        -- FPT (pompage)
        ('ENV_FLOOD_SUPPORT', 'ENV_FLOODING', 'VLR', 1, NULL::integer, false, 1),    -- Logistique
        ('ENV_FLOOD_SUPPORT', 'ENV_FLOODING', 'VSAV', 1, NULL::integer, false, 2),   -- VSAV si victimes
        
        -- ENV_WATER_DAMAGE - Dégâts des eaux
        ('ENV_WDAM_CORE', 'ENV_WATER_DAMAGE', 'VTU', 1, NULL::integer, true, 1),     -- VTU suffit généralement
        ('ENV_WDAM_CORE', 'ENV_WATER_DAMAGE', 'FPT', 1, NULL::integer, false, 2),    -- FPT si pompage nécessaire
        
        -- RESC_ANIMAL - Sauvetage d'animaux
        ('RESC_ANIM_CORE', 'RESC_ANIMAL', 'VTU', 1, NULL::integer, true, 1),         -- VTU polyvalent
        ('RESC_ANIM_CORE', 'RESC_ANIMAL', 'VPI', 1, NULL::integer, false, 2),        -- VPI en soutien
        
        -- TECH_INSECTS - Nids de guêpes / frelons
        ('TECH_INS_CORE', 'TECH_INSECTS', 'VPI', 1, NULL::integer, true, 1),         -- VPI suffit
        
        -- RESC_WATER - Sauvetage aquatique
        ('RESC_WATER_CORE', 'RESC_WATER', 'VTU', 1, NULL::integer, true, 1),         -- VTU avec matériel aquatique
        ('RESC_WATER_CORE', 'RESC_WATER', 'VSAV', 1, NULL::integer, true, 2),        -- VSAV obligatoire
        ('RESC_WATER_SUPPORT', 'RESC_WATER', 'VLM', 1, NULL::integer, false, 1),     -- Médecin si noyade
        ('RESC_WATER_SUPPORT', 'RESC_WATER', 'FPT', 1, NULL::integer, false, 2),     -- FPT soutien
        
        -- TECH_ELEVATOR - Personne bloquée dans un ascenseur
        ('TECH_ELEV_CORE', 'TECH_ELEVATOR', 'VPI', 1, NULL::integer, true, 1),       -- VPI suffit généralement
        ('TECH_ELEV_CORE', 'TECH_ELEVATOR', 'VSAV', 1, NULL::integer, false, 2),     -- VSAV si malaise
        
        -- ENV_POST_STORM - Déblai / bâchage après intempéries
        ('ENV_STORM_CORE', 'ENV_POST_STORM', 'VTU', 1, NULL::integer, true, 1),      -- VTU obligatoire
        ('ENV_STORM_SUPPORT', 'ENV_POST_STORM', 'VLR', 1, NULL::integer, false, 1),  -- Logistique en renfort
        ('ENV_STORM_SUPPORT', 'ENV_POST_STORM', 'EPA', 1, NULL::integer, false, 2)   -- Échelle si travaux en hauteur
        
    ) AS v(group_label, phase_code, vehicle_code, min_quantity, max_quantity, mandatory, preference_rank)
JOIN phase_types pt ON pt.code = v.phase_code
JOIN phase_type_vehicle_requirement_groups g
    ON g.phase_type_id = pt.phase_type_id AND g.label = v.group_label
JOIN vehicle_types vt ON vt.code = v.vehicle_code
ON CONFLICT (group_id, vehicle_type_id) DO NOTHING;

-- ---------- INCIDENTS (PAST) ----------
INSERT INTO incidents (
    incident_id,
    created_by_operator_id,
    address,
    zipcode,
    city,
    latitude,
    longitude,
    description,
    created_at,
    updated_at,
    ended_at
)
VALUES
    (
        '20000000-0000-0000-0000-000000000001'::uuid,
        '11111111-1111-1111-1111-111111111111'::uuid,
        '25 rue Paul Bert',
        '69003',
        'Lyon',
        45.758612,
        4.856321,
        'Feu d''appartement au 3eme etage, fumee dense.',
        '2024-02-10 14:12:00'::timestamptz,
        '2024-02-10 16:05:00'::timestamptz,
        '2024-02-10 16:40:00'::timestamptz
    ),
    (
        '20000000-0000-0000-0000-000000000002'::uuid,
        '33333333-3333-3333-3333-333333333333'::uuid,
        '92 avenue Jean Jaures',
        '69007',
        'Lyon',
        45.739225,
        4.837912,
        'Accident VL contre poteau, une personne incarceree.',
        '2024-03-18 08:42:00'::timestamptz,
        '2024-03-18 10:10:00'::timestamptz,
        '2024-03-18 10:55:00'::timestamptz
    )
ON CONFLICT (incident_id) DO NOTHING;

INSERT INTO incident_phases (
    incident_phase_id,
    incident_id,
    phase_type_id,
    priority,
    started_at,
    ended_at
)
SELECT
    v.incident_phase_id,
    v.incident_id,
    pt.phase_type_id,
    v.priority,
    v.started_at,
    v.ended_at
FROM (
    VALUES
        ('21000000-0000-0000-0000-000000000001'::uuid, '20000000-0000-0000-0000-000000000001'::uuid, 'FIRE_APARTMENT', 1, '2024-02-10 14:20:00'::timestamptz, '2024-02-10 15:40:00'::timestamptz),
        ('21000000-0000-0000-0000-000000000002'::uuid, '20000000-0000-0000-0000-000000000001'::uuid, 'SAP_INTOXICATION', 2, '2024-02-10 14:35:00'::timestamptz, '2024-02-10 15:50:00'::timestamptz),
        ('21000000-0000-0000-0000-000000000003'::uuid, '20000000-0000-0000-0000-000000000002'::uuid, 'ACC_ROAD', 1, '2024-03-18 08:50:00'::timestamptz, '2024-03-18 10:20:00'::timestamptz),
        ('21000000-0000-0000-0000-000000000004'::uuid, '20000000-0000-0000-0000-000000000002'::uuid, 'SAP_TRAUMA', 2, '2024-03-18 09:05:00'::timestamptz, '2024-03-18 10:10:00'::timestamptz)
    ) AS v(incident_phase_id, incident_id, phase_code, priority, started_at, ended_at)
JOIN phase_types pt ON pt.code = v.phase_code
ON CONFLICT (incident_phase_id) DO NOTHING;

INSERT INTO incident_phase_dependencies (
    incident_phase_id,
    depends_on_incident_phase_id,
    kind,
    created_at
)
VALUES
    (
        '21000000-0000-0000-0000-000000000002'::uuid,
        '21000000-0000-0000-0000-000000000001'::uuid,
        'SEQUENCE',
        '2024-02-10 14:34:00'::timestamptz
    ),
    (
        '21000000-0000-0000-0000-000000000004'::uuid,
        '21000000-0000-0000-0000-000000000003'::uuid,
        'SEQUENCE',
        '2024-03-18 09:00:00'::timestamptz
    )
ON CONFLICT (incident_phase_id, depends_on_incident_phase_id) DO NOTHING;

-- ---------- VEHICLE ASSIGNMENTS ----------
INSERT INTO vehicle_assignments (
    vehicle_assignment_id,
    vehicle_id,
    incident_phase_id,
    assigned_at,
    assigned_by_operator_id,
    validated_at,
    validated_by_operator_id,
    unassigned_at,
    notes
)
VALUES
    (
        '23000000-0000-0000-0000-000000000001'::uuid,
        '10000000-0000-0000-0000-000000000001'::uuid,
        '21000000-0000-0000-0000-000000000001'::uuid,
        '2024-02-10 14:18:00'::timestamptz,
        '11111111-1111-1111-1111-111111111111'::uuid,
        '2024-02-10 14:20:00'::timestamptz,
        '22222222-2222-2222-2222-222222222222'::uuid,
        '2024-02-10 16:05:00'::timestamptz,
        'FPT assigné pour extinction incendie.'
    ),
    (
        '23000000-0000-0000-0000-000000000002'::uuid,
        '10000000-0000-0000-0000-000000000002'::uuid,
        '21000000-0000-0000-0000-000000000002'::uuid,
        '2024-02-10 14:22:00'::timestamptz,
        '11111111-1111-1111-1111-111111111111'::uuid,
        '2024-02-10 14:25:00'::timestamptz,
        '22222222-2222-2222-2222-222222222222'::uuid,
        '2024-02-10 15:55:00'::timestamptz,
        'VSAV pour secours aux victimes.'
    ),
    (
        '23000000-0000-0000-0000-000000000003'::uuid,
        '10000000-0000-0000-0000-000000000004'::uuid,
        '21000000-0000-0000-0000-000000000003'::uuid,
        '2024-03-18 08:52:00'::timestamptz,
        '33333333-3333-3333-3333-333333333333'::uuid,
        '2024-03-18 08:55:00'::timestamptz,
        '22222222-2222-2222-2222-222222222222'::uuid,
        '2024-03-18 10:10:00'::timestamptz,
        'VSR pour désincarcération.'
    ),
    (
        '23000000-0000-0000-0000-000000000004'::uuid,
        '10000000-0000-0000-0000-000000000002'::uuid,
        '21000000-0000-0000-0000-000000000004'::uuid,
        '2024-03-18 09:05:00'::timestamptz,
        '33333333-3333-3333-3333-333333333333'::uuid,
        '2024-03-18 09:08:00'::timestamptz,
        '22222222-2222-2222-2222-222222222222'::uuid,
        '2024-03-18 10:25:00'::timestamptz,
        'VSAV pour transport victime.'
    )
ON CONFLICT (vehicle_assignment_id) DO NOTHING;

-- ---------- CASUALTIES ----------
INSERT INTO casualties (
    casualty_id,
    incident_phase_id,
    casualty_type_id,
    casualty_status_id,
    reported_at,
    notes
)
SELECT
    v.casualty_id,
    v.incident_phase_id,
    ct.casualty_type_id,
    cs.casualty_status_id,
    v.reported_at,
    v.notes
FROM (
    VALUES
        ('24000000-0000-0000-0000-000000000001'::uuid, '21000000-0000-0000-0000-000000000002'::uuid, 'CAS_LIGHT_INJURY', 'Transportée', '2024-02-10 14:40:00'::timestamptz, 'Inhalation legere de fumee.'),
        ('24000000-0000-0000-0000-000000000002'::uuid, '21000000-0000-0000-0000-000000000004'::uuid, 'CAS_TRAUMA', 'Transportée', '2024-03-18 09:10:00'::timestamptz, 'Traumatisme membre inferieur.')
    ) AS v(casualty_id, incident_phase_id, casualty_code, status_label, reported_at, notes)
JOIN casualty_types ct ON ct.code = v.casualty_code
JOIN casualty_status cs ON cs.label = v.status_label
ON CONFLICT (casualty_id) DO NOTHING;

-- ---------- CASUALTY TRANSPORTS ----------
INSERT INTO casualty_transports (
    casualty_transport_id,
    casualty_id,
    vehicle_assignment_id,
    picked_up_at,
    dropped_off_at,
    picked_up_latitude,
    picked_up_longitude,
    dropped_off_latitude,
    dropped_off_longitude,
    notes
)
VALUES
    (
        '25000000-0000-0000-0000-000000000001'::uuid,
        '24000000-0000-0000-0000-000000000001'::uuid,
        '23000000-0000-0000-0000-000000000002'::uuid,
        '2024-02-10 15:00:00'::timestamptz,
        '2024-02-10 15:25:00'::timestamptz,
        45.758612,
        4.856321,
        45.743612,
        4.880319,
        'Transport vers Hopital Edouard-Herriot.'
    ),
    (
        '25000000-0000-0000-0000-000000000002'::uuid,
        '24000000-0000-0000-0000-000000000002'::uuid,
        '23000000-0000-0000-0000-000000000004'::uuid,
        '2024-03-18 09:40:00'::timestamptz,
        '2024-03-18 10:05:00'::timestamptz,
        45.739225,
        4.837912,
        45.749614,
        4.835851,
        'Transport vers Centre hospitalier Saint-Joseph - Saint-Luc.'
    )
ON CONFLICT (casualty_transport_id) DO NOTHING;

-- ---------- VEHICLE POSITION LOGS ----------
INSERT INTO vehicle_position_logs (
    vehicle_position_id,
    vehicle_id,
    latitude,
    longitude,
    timestamp
)
VALUES
    (
        '27000000-0000-0000-0000-000000000001'::uuid,
        '10000000-0000-0000-0000-000000000001'::uuid,
        45.758900,
        4.855900,
        '2024-02-10 14:45:00'::timestamptz
    ),
    (
        '27000000-0000-0000-0000-000000000002'::uuid,
        '10000000-0000-0000-0000-000000000002'::uuid,
        45.759400,
        4.857100,
        '2024-02-10 15:10:00'::timestamptz
    ),
    (
        '27000000-0000-0000-0000-000000000003'::uuid,
        '10000000-0000-0000-0000-000000000004'::uuid,
        45.739600,
        4.838300,
        '2024-03-18 09:15:00'::timestamptz
    )
ON CONFLICT (vehicle_position_id) DO NOTHING;
