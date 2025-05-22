# Bosch Data Pipeline

## Project Overview
This project implements a real-time data pipeline to ingest, validate, transform, and analyze Air Quality sensor data. It processes CSV files dropped into a monitored folder and stores the raw and aggregated data into a PostgreSQL database.

## Folder Structure
- `data/` - Folder to place incoming raw CSV files.
- `processed/` - Processed files are moved here.
- `quarantine/` - Invalid data files moved here for review.
- `configs/` - Define customizable parameters for how the pipeline should behave without hardcoding them in your Python code.
- `src/` - Python source code for the pipeline.
- `requirements.txt` - Python dependencies.
- `.env` - Environment variables for configuration.
- `sql/` - - SQL scripts for creating tables.

## Setup Instructions

1. Make sure you have Python 3.8 or higher installed.
2. Clone this repository or download the project files.
3. (Optional but recommended) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate
4. Install required dependencies:
   pip install -r requirements.txt
5. Set up a PostgreSQL database and create the necessary tables according to the schema.
6. Update the configuration file configs/air_quality.yaml with your database credentials.

## Usage Instructions

1. Place your new sensor CSV files into the data/ directory(Two csv files used are already in /data directory AirQualityUCI.csv, AirQualityUCI_cleaned.csv, you can pass them again /data by using copy 'cp' command).
2. Run the monitoring script:python src/monitor.py
3. The pipeline will automatically detect new files, process and validate the data, insert raw and aggregated results into the database, and move files to processed/ or quarantine/ accordingly.
4. Check quarantine logs for errors.

## Dataset

Air Quality dataset from UCI which contains the responses of a gas multisensor device deployed on the field in an Italian city
Link: https://archive.ics.uci.edu/dataset/360/air+quality

Note: 
-AirQualityUCI.csv: Original dataset with no changes.
-AirQualityUCI_cleaned.csv: Cleaned dataset with no null values used to run the pipeline end-to-end with no errors.


## Database Schema

This project uses PostgreSQL to store both raw sensor readings and aggregated metrics from the Air Quality UCI dataset.

### Tables

#### `raw_data`

Stores the original sensor data imported from CSV files. Each row corresponds to one timestamped sensor reading.

| Column Name      | Type              | Description                                                                 |
|------------------|-------------------|-----------------------------------------------------------------------------|
| `id`             | SERIAL PRIMARY KEY| Unique identifier for each record                                            |
| `file_name`      | TEXT              | Name of the CSV file source                                                  |
| `data_source`    | TEXT              | Source identifier, defaults to `'air_quality_sensor'`                        |
| `sensor_id`      | TEXT              | Optional sensor identifier, nullable                                         |
| `timestamp`      | TIMESTAMPTZ       | Timestamp of the reading (parsed from the original DateTime column)          |
| Sensor readings  | REAL              | Various air quality sensor values, each with a non-negative constraint       |
| `"CO(GT)"`       | REAL CHECK (`>=0`)| Carbon Monoxide concentration                                                |
| `"PT08.S1(CO)"`  | REAL CHECK (`>=0`)| Tin oxide sensor response for CO                                             |
| `"NMHC(GT)"`     | REAL CHECK (`>=0`)| Non-methane hydrocarbons                                                     |
| `"C6H6(GT)"`     | REAL CHECK (`>=0`)| Benzene concentration                                                        |
| `"PT08.S2(NMHC)"`| REAL CHECK (`>=0`)| Tin oxide sensor response for NMHC                                           |
| `"NOx(GT)"`      | REAL CHECK (`>=0`)| Nitrogen oxides concentration                                                |
| `"PT08.S3(NOx)"` | REAL CHECK (`>=0`)| Tin oxide sensor response for NOx                                            |
| `"NO2(GT)"`      | REAL CHECK (`>=0`)| Nitrogen dioxide concentration                                               |
| `"PT08.S4(NO2)"` | REAL CHECK (`>=0`)| Tin oxide sensor response for NO2                                            |
| `"PT08.S5(O3)"`  | REAL CHECK (`>=0`)| Tin oxide sensor response for Ozone                                          |
| `"T"`            | REAL              | Temperature (°C)                                                             |
| `"RH"`           | REAL              | Relative Humidity (%)                                                        |
| `"AH"`           | REAL              | Absolute Humidity                                                            |
| `location`       | TEXT              | Optional location metadata                                                   |
| `created_at`     | TIMESTAMPTZ       | Timestamp when the record was inserted, defaults to current time             |

##### Indexes for `raw_data`

- `idx_raw_data_timestamp` on `timestamp` to speed up time-based queries.
- `idx_raw_data_sensor_id` on `sensor_id` to speed up sensor-specific queries.

---

#### `aggregated_data`

Stores summary statistics computed over raw sensor data, facilitating efficient analysis and visualization.

| Column Name             | Type               | Description                                                           |
|-------------------------|--------------------|-----------------------------------------------------------------------|
| `id`                    | SERIAL PRIMARY KEY | Unique identifier for each aggregated record                         |
| `data_source`           | VARCHAR(255)       | Data source identifier (e.g., `'air_quality'`)                       |
| `file_name`             | VARCHAR(255)       | Source file name for traceability                                    |
| `sensor_name`           | VARCHAR(255)       | Name of the sensor/metric aggregated (e.g., `'CO(GT)'`)              |
| `metric_type`           | VARCHAR(50)        | Type of metric (e.g., `'min'`, `'max'`, `'avg'`, `'stddev'`)         |
| `metric_value`          | DOUBLE PRECISION   | Computed value of the aggregated metric                              |
| `aggregation_timestamp` | TIMESTAMP          | Timestamp when the aggregation was performed (could match file time) |
| `created_at`            | TIMESTAMP          | Timestamp when this record was inserted, defaults to current time    |

##### Indexes for `aggregated_data`

- `idx_agg_sensor_metric` on `(sensor_name, metric_type)` to speed up filtering by sensor and metric.
- `idx_agg_timestamp` on `aggregation_timestamp` for efficient time-range queries.



## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.




