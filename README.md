# Bosch Data Pipeline

## Project Overview
This project implements a real-time data pipeline to ingest, validate, transform, and analyze IoT sensor data. It processes CSV files dropped into a monitored folder and stores the raw and aggregated data into a PostgreSQL database.

## Folder Structure
- `data/` - Folder to place incoming raw CSV files.
- `logs/` - Logs generated during pipeline execution.
- `quarantine/` - Invalid data files moved here for review.
- `src/` - Python source code for the pipeline.
- `requirements.txt` - Python dependencies.
- `.env` - Environment variables for configuration.

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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

