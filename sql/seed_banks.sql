-- Seed bank metadata (run after schema.sql on bank_reviews database)

INSERT INTO banks (bank_name, app_name) VALUES
    ('Commercial Bank of Ethiopia', 'Commercial Bank of Ethiopia Mobile'),
    ('Bank of Abyssinia', 'BoA Mobile'),
    ('Dashen Bank', 'Dashen Bank')
ON CONFLICT (bank_name) DO UPDATE SET app_name = EXCLUDED.app_name;
