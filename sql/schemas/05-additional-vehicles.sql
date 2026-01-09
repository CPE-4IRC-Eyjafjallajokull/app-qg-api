/* =========================================================
   05_additional_vehicles.sql — ADDITIONAL VEHICLES (100 vehicles)
   ========================================================= */

WITH vehicle_seed AS (
    SELECT * FROM (VALUES
        -- Lyon-Gerland (15 véhicules supplémentaires)
        ('10000000-0000-0000-0000-000000000071'::uuid, 'FPT', 'KL-128-NP', 'Gazole', 0.93, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-000000000072'::uuid, 'VSAV', 'KL-129-QR', 'Gazole', 0.81, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-000000000073'::uuid, 'EPA', 'KL-130-ST', 'Gazole', 0.87, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-000000000074'::uuid, 'VLM', 'KL-131-UV', 'Essence', 0.72, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-000000000075'::uuid, 'VSR', 'KL-132-WX', 'Gazole', 0.78, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-000000000076'::uuid, 'CCGC', 'KL-133-YZ', 'Gazole', 0.92, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-000000000077'::uuid, 'FPTSR', 'KL-134-AB', 'Gazole', 0.69, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-000000000078'::uuid, 'VPI', 'KL-135-CD', 'Essence', 0.74, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-000000000079'::uuid, 'BEA', 'KL-136-EF', 'Gazole', 0.83, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-00000000007a'::uuid, 'VTU', 'KL-137-GH', 'Gazole', 0.77, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-00000000007b'::uuid, 'VSAV', 'KL-138-JK', 'Gazole', 0.85, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-00000000007c'::uuid, 'FPT', 'KL-139-LM', 'Gazole', 0.90, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-00000000007d'::uuid, 'CCF', 'KL-140-NP', 'Gazole', 0.88, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-00000000007e'::uuid, 'VAR', 'KL-141-QR', 'Gazole', 0.66, 'Lyon-Gerland', 'Disponible'),
        ('10000000-0000-0000-0000-00000000007f'::uuid, 'VSAV', 'KL-142-ST', 'Gazole', 0.79, 'Lyon-Gerland', 'Disponible'),

        -- Lyon-Corneille (14 véhicules supplémentaires)
        ('10000000-0000-0000-0000-000000000080'::uuid, 'FPT', 'LM-227-UV', 'Gazole', 0.94, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000081'::uuid, 'VSAV', 'LM-228-WX', 'Gazole', 0.71, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000082'::uuid, 'EPA', 'LM-229-YZ', 'Gazole', 0.82, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000083'::uuid, 'VLM', 'LM-230-AB', 'Essence', 0.68, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000084'::uuid, 'VSR', 'LM-231-CD', 'Gazole', 0.84, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000085'::uuid, 'VPI', 'LM-232-EF', 'Essence', 0.75, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000086'::uuid, 'FPTSR', 'LM-233-GH', 'Gazole', 0.86, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000087'::uuid, 'VTU', 'LM-234-JK', 'Gazole', 0.73, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000088'::uuid, 'VSAV', 'LM-235-LM', 'Gazole', 0.88, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-000000000089'::uuid, 'FPT', 'LM-236-NP', 'Gazole', 0.91, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-00000000008a'::uuid, 'CCF', 'LM-237-QR', 'Gazole', 0.80, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-00000000008b'::uuid, 'BEA', 'LM-238-ST', 'Gazole', 0.89, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-00000000008c'::uuid, 'VSAV', 'LM-239-UV', 'Gazole', 0.76, 'Lyon-Corneille', 'Disponible'),
        ('10000000-0000-0000-0000-00000000008d'::uuid, 'VPI', 'LM-240-WX', 'Essence', 0.63, 'Lyon-Corneille', 'Disponible'),

        -- Lyon-Confluence (12 véhicules supplémentaires)
        ('10000000-0000-0000-0000-00000000008e'::uuid, 'FPT', 'MN-325-YZ', 'Gazole', 0.89, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-00000000008f'::uuid, 'VSAV', 'MN-326-AB', 'Gazole', 0.82, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000090'::uuid, 'EPA', 'MN-327-CD', 'Gazole', 0.85, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000091'::uuid, 'VLM', 'MN-328-EF', 'Essence', 0.59, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000092'::uuid, 'VSR', 'MN-329-GH', 'Gazole', 0.77, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000093'::uuid, 'CCGC', 'MN-330-JK', 'Gazole', 0.91, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000094'::uuid, 'VPI', 'MN-331-LM', 'Essence', 0.67, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000095'::uuid, 'VTU', 'MN-332-NP', 'Gazole', 0.83, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000096'::uuid, 'VSAV', 'MN-333-QR', 'Gazole', 0.78, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000097'::uuid, 'FPT', 'MN-334-ST', 'Gazole', 0.92, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000098'::uuid, 'VLR', 'MN-335-UV', 'Gazole', 0.71, 'Lyon-Confluence', 'Disponible'),
        ('10000000-0000-0000-0000-000000000099'::uuid, 'FPTSR', 'MN-336-WX', 'Gazole', 0.84, 'Lyon-Confluence', 'Disponible'),

        -- Lyon-Croix-Rousse (11 véhicules supplémentaires)
        ('10000000-0000-0000-0000-00000000009a'::uuid, 'FPT', 'NP-424-YZ', 'Gazole', 0.88, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-00000000009b'::uuid, 'VSAV', 'NP-425-AB', 'Gazole', 0.79, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-00000000009c'::uuid, 'EPA', 'NP-426-CD', 'Gazole', 0.93, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-00000000009d'::uuid, 'VLM', 'NP-427-EF', 'Essence', 0.61, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-00000000009e'::uuid, 'VSR', 'NP-428-GH', 'Gazole', 0.86, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-00000000009f'::uuid, 'VPI', 'NP-429-JK', 'Essence', 0.73, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000a0'::uuid, 'VTU', 'NP-430-LM', 'Gazole', 0.81, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000a1'::uuid, 'VSAV', 'NP-431-NP', 'Gazole', 0.87, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000a2'::uuid, 'FPT', 'NP-432-QR', 'Gazole', 0.90, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000a3'::uuid, 'CCF', 'NP-433-ST', 'Gazole', 0.82, 'Lyon-Croix-Rousse', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000a4'::uuid, 'VSAV', 'NP-434-UV', 'Gazole', 0.69, 'Lyon-Croix-Rousse', 'Disponible'),

        -- Lyon-Duchère (10 véhicules supplémentaires)
        ('10000000-0000-0000-0000-0000000000a5'::uuid, 'FPT', 'PQ-523-WX', 'Gazole', 0.91, 'Lyon-Duchère', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000a6'::uuid, 'VSAV', 'PQ-524-YZ', 'Gazole', 0.80, 'Lyon-Duchère', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000a7'::uuid, 'CCF', 'PQ-525-AB', 'Gazole', 0.94, 'Lyon-Duchère', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000a8'::uuid, 'VLM', 'PQ-526-CD', 'Essence', 0.70, 'Lyon-Duchère', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000a9'::uuid, 'VSR', 'PQ-527-EF', 'Gazole', 0.85, 'Lyon-Duchère', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000aa'::uuid, 'VPI', 'PQ-528-GH', 'Essence', 0.76, 'Lyon-Duchère', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000ab'::uuid, 'VTU', 'PQ-529-JK', 'Gazole', 0.83, 'Lyon-Duchère', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000ac'::uuid, 'VSAV', 'PQ-530-LM', 'Gazole', 0.88, 'Lyon-Duchère', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000ad'::uuid, 'FPT', 'PQ-531-NP', 'Gazole', 0.92, 'Lyon-Duchère', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000ae'::uuid, 'CCGC', 'PQ-532-QR', 'Gazole', 0.87, 'Lyon-Duchère', 'Disponible'),

        -- Lyon-Rochat (9 véhicules supplémentaires)
        ('10000000-0000-0000-0000-0000000000af'::uuid, 'FPT', 'QR-622-ST', 'Gazole', 0.89, 'Lyon-Rochat', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000b0'::uuid, 'VSAV', 'QR-623-UV', 'Gazole', 0.75, 'Lyon-Rochat', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000b1'::uuid, 'EPA', 'QR-624-WX', 'Gazole', 0.91, 'Lyon-Rochat', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000b2'::uuid, 'VLM', 'QR-625-YZ', 'Essence', 0.58, 'Lyon-Rochat', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000b3'::uuid, 'VSR', 'QR-626-AB', 'Gazole', 0.84, 'Lyon-Rochat', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000b4'::uuid, 'VPI', 'QR-627-CD', 'Essence', 0.72, 'Lyon-Rochat', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000b5'::uuid, 'VTU', 'QR-628-EF', 'Gazole', 0.78, 'Lyon-Rochat', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000b6'::uuid, 'VSAV', 'QR-629-GH', 'Gazole', 0.86, 'Lyon-Rochat', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000b7'::uuid, 'FPT', 'QR-630-JK', 'Gazole', 0.93, 'Lyon-Rochat', 'Disponible'),

        -- Villeurbanne-Cusset (8 véhicules supplémentaires)
        ('10000000-0000-0000-0000-0000000000b8'::uuid, 'FPT', 'RS-721-LM', 'Gazole', 0.95, 'Villeurbanne-Cusset', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000b9'::uuid, 'VSAV', 'RS-722-NP', 'Gazole', 0.74, 'Villeurbanne-Cusset', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000ba'::uuid, 'EPA', 'RS-723-QR', 'Gazole', 0.88, 'Villeurbanne-Cusset', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000bb'::uuid, 'VLM', 'RS-724-ST', 'Essence', 0.69, 'Villeurbanne-Cusset', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000bc'::uuid, 'VSR', 'RS-725-UV', 'Gazole', 0.87, 'Villeurbanne-Cusset', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000bd'::uuid, 'VPI', 'RS-726-WX', 'Essence', 0.75, 'Villeurbanne-Cusset', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000be'::uuid, 'VSAV', 'RS-727-YZ', 'Gazole', 0.82, 'Villeurbanne-Cusset', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000bf'::uuid, 'FPT', 'RS-728-AB', 'Gazole', 0.90, 'Villeurbanne-Cusset', 'Disponible'),

        -- Villeurbanne-La Doua (8 véhicules supplémentaires)
        ('10000000-0000-0000-0000-0000000000c0'::uuid, 'FPT', 'ST-821-CD', 'Gazole', 0.92, 'Villeurbanne-La Doua', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000c1'::uuid, 'VSAV', 'ST-822-EF', 'Gazole', 0.79, 'Villeurbanne-La Doua', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000c2'::uuid, 'VLM', 'ST-823-GH', 'Essence', 0.67, 'Villeurbanne-La Doua', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000c3'::uuid, 'VSR', 'ST-824-JK', 'Gazole', 0.85, 'Villeurbanne-La Doua', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000c4'::uuid, 'VPI', 'ST-825-LM', 'Essence', 0.73, 'Villeurbanne-La Doua', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000c5'::uuid, 'VTU', 'ST-826-NP', 'Gazole', 0.81, 'Villeurbanne-La Doua', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000c6'::uuid, 'VSAV', 'ST-827-QR', 'Gazole', 0.88, 'Villeurbanne-La Doua', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000c7'::uuid, 'FPT', 'ST-828-ST', 'Gazole', 0.89, 'Villeurbanne-La Doua', 'Disponible'),

        -- SDMIS Lyon (Direction) (13 véhicules supplémentaires)
        ('10000000-0000-0000-0000-0000000000c8'::uuid, 'VIRT', 'TU-926-UV', 'Gazole', 0.87, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000c9'::uuid, 'VLCG', 'TU-927-WX', 'Gazole', 0.83, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000ca'::uuid, 'PC Mobile', 'TU-928-YZ', 'Gazole', 0.91, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000cb'::uuid, 'VLR', 'TU-929-AB', 'Gazole', 0.78, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000cc'::uuid, 'CCGC', 'TU-930-CD', 'Gazole', 0.94, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000cd'::uuid, 'VIRT', 'TU-931-EF', 'Gazole', 0.80, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000ce'::uuid, 'VLCG', 'TU-932-GH', 'Gazole', 0.74, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000cf'::uuid, 'VTU', 'TU-933-JK', 'Gazole', 0.85, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000d0'::uuid, 'VLM', 'TU-934-LM', 'Essence', 0.71, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000d1'::uuid, 'VAR', 'TU-935-NP', 'Gazole', 0.77, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000d2'::uuid, 'CCGC', 'TU-936-QR', 'Gazole', 0.92, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000d3'::uuid, 'VLR', 'TU-937-ST', 'Gazole', 0.79, 'SDMIS Lyon (Direction)', 'Disponible'),
        ('10000000-0000-0000-0000-0000000000d4'::uuid, 'PC Mobile', 'TU-938-UV', 'Gazole', 0.88, 'SDMIS Lyon (Direction)', 'Disponible')

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

-- ---------- VEHICLE CONSUMABLE STOCK FOR NEW VEHICLES ----------
-- Ajout des stocks de consommables pour les nouveaux véhicules
INSERT INTO vehicle_consumables_stock (
    vehicle_id,
    consumable_type_id,
    current_quantity,
    last_update
)
SELECT DISTINCT
    v.vehicle_id,
    vtcs.consumable_type_id,
    vtcs.initial_quantity,
    now()
FROM vehicles v
JOIN vehicle_types vt ON v.vehicle_type_id = vt.vehicle_type_id
JOIN vehicle_type_consumable_specs vtcs ON vtcs.vehicle_type_id = vt.vehicle_type_id
WHERE vtcs.is_applicable = true
  AND v.immatriculation LIKE 'SD-1%'
ON CONFLICT (vehicle_id, consumable_type_id) DO NOTHING;
