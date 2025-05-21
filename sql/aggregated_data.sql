CREATE TABLE aggregated_data (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(255) NOT NULL,      -- e.g., 'air_quality'
    file_name VARCHAR(255) NOT NULL,
    sensor_name VARCHAR(255) NOT NULL,      -- e.g., 'CO(GT)'
    metric_type VARCHAR(50) NOT NULL,       -- e.g., 'min', 'max', 'avg', 'stddev'
    metric_value DOUBLE PRECISION NOT NULL,
    aggregation_timestamp TIMESTAMP NOT NULL, -- time when aggregation was computed 
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index to speed up queries by sensor and metric
CREATE INDEX idx_agg_sensor_metric ON aggregated_data(sensor_name, metric_type);
CREATE INDEX idx_agg_timestamp ON aggregated_data(aggregation_timestamp);


