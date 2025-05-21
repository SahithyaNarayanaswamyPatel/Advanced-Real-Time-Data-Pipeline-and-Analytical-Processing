CREATE TABLE raw_data (
    id SERIAL PRIMARY KEY,
    file_name TEXT,
    data_source TEXT DEFAULT 'air_quality_sensor',

    sensor_id TEXT,  -- Optional, if not available, allow NULL
    timestamp TIMESTAMPTZ NOT NULL,  -- Use parsed "DateTime"

    -- Sensor readings
    "CO(GT)" REAL CHECK ("CO(GT)" >= 0),
    "PT08.S1(CO)" REAL CHECK ("PT08.S1(CO)" >= 0),
    "NMHC(GT)" REAL CHECK ("NMHC(GT)" >= 0),
    "C6H6(GT)" REAL CHECK ("C6H6(GT)" >= 0),
    "PT08.S2(NMHC)" REAL CHECK ("PT08.S2(NMHC)" >= 0),
    "NOx(GT)" REAL CHECK ("NOx(GT)" >= 0),
    "PT08.S3(NOx)" REAL CHECK ("PT08.S3(NOx)" >= 0),
    "NO2(GT)" REAL CHECK ("NO2(GT)" >= 0),
    "PT08.S4(NO2)" REAL CHECK ("PT08.S4(NO2)" >= 0),
    "PT08.S5(O3)" REAL CHECK ("PT08.S5(O3)" >= 0),
    "T" REAL,
    "RH" REAL,
    "AH" REAL,

    location TEXT,  -- Optional
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Optional indexes for performance
CREATE INDEX idx_raw_data_timestamp ON raw_data(timestamp);
CREATE INDEX idx_raw_data_sensor_id ON raw_data(sensor_id);

