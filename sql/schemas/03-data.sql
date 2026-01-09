/* =========================================================
   03_data.sql — BASE DATA (REFERENTIALS)
   ========================================================= */

-- ---------- VEHICLES ----------
INSERT INTO vehicle_types (vehicle_type_id, code, label) VALUES
    (uuid_generate_v4(), 'FPT', 'Fourgon Pompe Tonne'),
    (uuid_generate_v4(), 'FPTSR', 'Fourgon Pompe Tonne avec Secours Routier'),
    (uuid_generate_v4(), 'CCF', 'Camion Citerne Feux de Forêts'),
    (uuid_generate_v4(), 'CCGC', 'Camion Citerne Grande Capacité'),
    (uuid_generate_v4(), 'EPA', 'Échelle Pivotante Automatique'),
    (uuid_generate_v4(), 'BEA', 'Bras Élévateur Articulé'),
    (uuid_generate_v4(), 'VSAV', 'Véhicule de Secours et d''Assistance aux Victimes'),
    (uuid_generate_v4(), 'VLM', 'Véhicule Léger Médicalisé'),
    (uuid_generate_v4(), 'VSR', 'Véhicule de Secours Routier'),
    (uuid_generate_v4(), 'VAR', 'Véhicule d''Assistance Routière'),
    (uuid_generate_v4(), 'VIRT', 'Véhicule d''Intervention Risques Technologiques'),
    (uuid_generate_v4(), 'VPI', 'Véhicule Première Intervention'),
    (uuid_generate_v4(), 'VLCG', 'Véhicule de Commandement'),
    (uuid_generate_v4(), 'PC Mobile', 'Poste de Commandement Mobile'),
    (uuid_generate_v4(), 'VLR', 'Véhicule Logistique'),
    (uuid_generate_v4(), 'VTU', 'Véhicule Tout Usage')
ON CONFLICT (code) DO NOTHING;

INSERT INTO vehicle_status (vehicle_status_id, label) VALUES
    (uuid_generate_v4(), 'Disponible'),
    (uuid_generate_v4(), 'Engagé'),
    (uuid_generate_v4(), 'Sur intervention'),
    (uuid_generate_v4(), 'Transport'),
    (uuid_generate_v4(), 'Retour'),
    (uuid_generate_v4(), 'Indisponible'),
    (uuid_generate_v4(), 'Hors service')
ON CONFLICT (label) DO NOTHING;

INSERT INTO energies (energy_id, label) VALUES
    (uuid_generate_v4(), 'Essence'),
    (uuid_generate_v4(), 'Batterie'),
    (uuid_generate_v4(), 'Gazole')
ON CONFLICT (label) DO NOTHING;

INSERT INTO vehicle_consumable_types (vehicle_consumable_type_id, label, unit) VALUES
    (uuid_generate_v4(), 'Eau', 'L'),
    (uuid_generate_v4(), 'Mousse', 'L'),
    (uuid_generate_v4(), 'Bouteille oxygène', 'unité'),
    (uuid_generate_v4(), 'Oxygène médical', 'L'),
    (uuid_generate_v4(), 'Masque oxygène', 'unité'),
    (uuid_generate_v4(), 'Compresse', 'unité'),
    (uuid_generate_v4(), 'Pansement', 'unité'),
    (uuid_generate_v4(), 'Couverture de survie', 'unité'),
    (uuid_generate_v4(), 'Lit', 'unité'),
    (uuid_generate_v4(), 'Désinfectant', 'L'),
    (uuid_generate_v4(), 'Groupe électrogène', 'unité'),
    (uuid_generate_v4(), 'Masque chirurgical', 'unité')
ON CONFLICT (label) DO NOTHING;

-- ---------- INCIDENTS ----------
INSERT INTO phase_categories (phase_category_id, code, label) VALUES
    (uuid_generate_v4(), 'FIRE', 'Incendies'),
    (uuid_generate_v4(), 'SAP', 'Secours à personne'),
    (uuid_generate_v4(), 'HAZMAT', 'Risques technologiques et matières dangereuses'),
    (uuid_generate_v4(), 'ACCIDENT', 'Accidents'),
    (uuid_generate_v4(), 'MISC_RESCUE', 'Secours divers')
ON CONFLICT (code) DO NOTHING;

INSERT INTO phase_types (phase_type_id, phase_category_id, code, label, default_criticity)
SELECT
    uuid_generate_v4(),
    pc.phase_category_id,
    v.code,
    v.label,
    v.default_criticity
FROM (
    VALUES
        ('FIRE', 'FIRE_HABITATION', 'Feu d''habitation', 0),
        ('FIRE', 'FIRE_APARTMENT', 'Feu d''appartement', 0),
        ('FIRE', 'FIRE_INDUSTRIAL', 'Feu industriel', 1),
        ('FIRE', 'FIRE_PUBLIC_SPACE', 'Feu sur la voie publique', 3),
        ('FIRE', 'FIRE_WILDLAND', 'Feu de forêt / végétation', 2),
        ('FIRE', 'FIRE_BASEMENT', 'Feu de sous-sol / local technique', 1),
        ('FIRE', 'FIRE_CHIMNEY', 'Feu de cheminée', 4),
        ('FIRE', 'FIRE_EXPLOSION_RISK', 'Explosion / risque d''explosion', 0),
        ('HAZMAT', 'HAZ_GAS_LEAK', 'Odeur suspecte / fuite de gaz', 2),
        ('SAP', 'SAP_MALAISE', 'Malaise', 3),
        ('SAP', 'SAP_CARDIAC_ARREST', 'Arrêt cardiaque', 0),
        ('SAP', 'SAP_TRAUMA', 'Traumatisme', 3),
        ('SAP', 'SAP_HEMORRHAGE', 'Hémorragie', 1),
        ('SAP', 'SAP_CHILDBIRTH', 'Accouchement inopiné', 1),
        ('SAP', 'RESC_PERSON_TRAPPED', 'Personne coincée / relevage', 2),
        ('SAP', 'SAP_INTOXICATION', 'Intoxication (fumées, CO, chimiques)', 1),
        ('HAZMAT', 'HAZ_CHEMICAL_LEAK', 'Fuite de produit chimique', 2),
        ('HAZMAT', 'HAZ_FUEL_LEAK', 'Fuite de carburant', 4),
        ('HAZMAT', 'ENV_WATER_POLLUTION', 'Pollution de cours d''eau', 5),
        ('ACCIDENT', 'ACC_HAZMAT', 'Accident avec matières dangereuses', 1),
        ('ACCIDENT', 'ACC_ROAD', 'Accident de la circulation', 2),
        ('ACCIDENT', 'ACC_TRAIN_COLLISION', 'Collision train / véhicule', 1),
        ('ACCIDENT', 'ACC_RAIL_INCIDENT', 'Déraillement / incident ferroviaire', 1),
        ('ACCIDENT', 'ACC_AIRCRAFT', 'Accident aérien (léger, drone)', 2),
        ('ACCIDENT', 'ACC_INDUSTRIAL', 'Accident industriel', 1),
        ('MISC_RESCUE', 'ENV_FLOODING', 'Inondation', 4),
        ('MISC_RESCUE', 'ENV_WATER_DAMAGE', 'Dégâts des eaux', 6),
        ('MISC_RESCUE', 'RESC_ANIMAL', 'Sauvetage d''animaux', 6),
        ('MISC_RESCUE', 'TECH_INSECTS', 'Nids de guêpes / frelons', 7),
        ('MISC_RESCUE', 'RESC_WATER', 'Sauvetage aquatique', 1),
        ('MISC_RESCUE', 'TECH_ELEVATOR', 'Personne bloquée dans un ascenseur', 4),
        ('MISC_RESCUE', 'ENV_POST_STORM', 'Déblai / bâchage après intempéries', 5)
) AS v(phase_category_code, code, label, default_criticity)
JOIN phase_categories pc ON pc.code = v.phase_category_code
ON CONFLICT (code) DO NOTHING;

-- ---------- INTEREST POINTS ----------
INSERT INTO interest_point_kinds (interest_point_kind_id, label) VALUES
    (uuid_generate_v4(), 'Centre de secours'),
    (uuid_generate_v4(), 'Hôpital'),
    (uuid_generate_v4(), 'Commissariat de police'),
    (uuid_generate_v4(), 'Centre de maintenance véhicules'),
    (uuid_generate_v4(), 'Clinique privée')
ON CONFLICT (label) DO NOTHING;

INSERT INTO interest_points (
    interest_point_id,
    name,
    address,
    zipcode,
    city,
    latitude,
    longitude,
    interest_point_kind_id
)
SELECT
    uuid_generate_v4(),
    v.name,
    v.address,
    v.zipcode,
    v.city,
    v.latitude,
    v.longitude,
    ipk.interest_point_kind_id
FROM (
    VALUES
        ('Lyon-Confluence', '10 rue Smith', '69002', 'Lyon', 45.74653546, 4.825207281, 'Centre de secours'),
        ('Lyon-Corneille', '78 rue Pierre Corneille', '69003', 'Lyon', 45.76271578, 4.843600664, 'Centre de secours'),
        ('Lyon-Croix-Rousse', '120 rue Philippe de Lasalle', '69004', 'Lyon', 45.78398, 4.82135, 'Centre de secours'),
        ('Lyon-Gerland', '17-19 avenue Debourg', '69007', 'Lyon', 45.73182606, 4.828499108, 'Centre de secours'),
        ('Lyon-Rochat', '3 rue de la Madeleine', '69007', 'Lyon', 45.75009, 4.84808, 'Centre de secours'),
        ('Lyon-Duchère', '357 avenue de Champagne', '69009', 'Lyon', 45.79072, 4.79794, 'Centre de secours'),
        ('Villeurbanne-Cusset', '11 rue Baudin', '69100', 'Villeurbanne', 45.76800, 4.88400, 'Centre de secours'),
        ('Villeurbanne-La Doua', '35 rue Georges Courteline', '69100', 'Villeurbanne', 45.77899, 4.87800, 'Centre de secours'),
        ('SDMIS Lyon (Direction)', '17 rue Rabelais', '69003', 'Lyon', 45.7593, 4.8460, 'Centre de secours'),
        ('Hôpital Édouard-Herriot', '5 place d''Arsonval', '69003', 'Lyon', 45.743612, 4.880319, 'Hôpital'),
        ('Hôpital de la Croix-Rousse', '103 Grande Rue de la Croix-Rousse', '69004', 'Lyon', 45.780833, 4.830833, 'Hôpital'),
        ('Centre hospitalier Saint-Joseph - Saint-Luc', '20 quai Claude Bernard', '69007', 'Lyon', 45.749614, 4.835851, 'Hôpital'),
        ('Hôpital des Charpennes', '27 rue Gabriel Péri', '69100', 'Villeurbanne', 45.771890, 4.864170, 'Hôpital'),
        ('Médipôle Lyon-Villeurbanne', '158 rue Léon Blum', '69100', 'Villeurbanne', 45.759722, 4.907778, 'Hôpital')
) AS v(name, address, zipcode, city, latitude, longitude, kind_label)
JOIN interest_point_kinds ipk ON ipk.label = v.kind_label
ON CONFLICT (name) DO NOTHING;

INSERT INTO interest_point_consumable_types (interest_point_consumable_type_id, label) VALUES
    (uuid_generate_v4(), 'Ressource humaine'),
    (uuid_generate_v4(), 'Places véhicules'),
    (uuid_generate_v4(), 'Lits'),
    (uuid_generate_v4(), 'Matériel médical'),
    (uuid_generate_v4(), 'Carburant')
ON CONFLICT (label) DO NOTHING;

-- ---------- CASUALTIES ----------
INSERT INTO casualty_types (casualty_type_id, code, label) VALUES
    (uuid_generate_v4(), 'CAS_UNINJURED', 'Aucune blessure'),
    (uuid_generate_v4(), 'CAS_LIGHT_INJURY', 'Blessure légère'),
    (uuid_generate_v4(), 'CAS_MODERATE_INJURY', 'Blessure modérée'),
    (uuid_generate_v4(), 'CAS_SEVERE_INJURY', 'Blessure sévère'),
    (uuid_generate_v4(), 'CAS_CRITICAL', 'État critique'),
    (uuid_generate_v4(), 'CAS_DECEASED', 'Décédée'),
    (uuid_generate_v4(), 'CAS_BURN_MINOR', 'Brûlure mineure'),
    (uuid_generate_v4(), 'CAS_BURN_MODERATE', 'Brûlure modérée'),
    (uuid_generate_v4(), 'CAS_BURN_SEVERE', 'Brûlure sévère'),
    (uuid_generate_v4(), 'CAS_TRAUMA', 'Traumatisme'),
    (uuid_generate_v4(), 'CAS_PSYCHOLOGICAL', 'Détresse psychologique')
ON CONFLICT (code) DO NOTHING;

INSERT INTO casualty_status (casualty_status_id, label) VALUES
    (uuid_generate_v4(), 'Déclarée'),
    (uuid_generate_v4(), 'Localisée'),
    (uuid_generate_v4(), 'Évaluée'),
    (uuid_generate_v4(), 'Prise en charge'),
    (uuid_generate_v4(), 'Transportée'),
    (uuid_generate_v4(), 'Transmise')
ON CONFLICT (label) DO NOTHING;
