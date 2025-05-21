import os
import time
import logging
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from shutil import move

from processor import process_file
from aggregation import aggregate_metrics
from database import get_connection, insert_raw_data, insert_aggregated_data

# --- Folder Config ---
DATA_FOLDER = "data"
PROCESSED_FOLDER = "processed"
QUARANTINE_FOLDER = "quarantine"
CONFIG_FOLDER = "configs"

# --- Setup ---
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(QUARANTINE_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
processed_files = set()

def load_config(config_name="air_quality.yaml"):
    config_path = os.path.join(CONFIG_FOLDER, config_name)
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def move_file(src_path, dest_folder):
    filename = os.path.basename(src_path)
    dest_path = os.path.join(dest_folder, filename)
    move(src_path, dest_path)
    logging.info(f"Moved file {filename} to {dest_folder}")

def log_quarantine(file_path, reason):
    try:
        move_file(file_path, QUARANTINE_FOLDER)
    except Exception as move_err:
        logging.error(f"Failed to move file to quarantine: {move_err}")
    with open(os.path.join(QUARANTINE_FOLDER, "error_log.txt"), "a") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp} - {file_path} - {reason}\n")

class NewCSVHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        self.data_source = config.get('data_source', 'air_quality_sensor')

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.csv'):
            return

        filename = os.path.basename(event.src_path)
        if filename in processed_files:
            return

        file_path = event.src_path

        # --- Ensure file is fully written ---
        stable = False
        last_size = -1
        max_tries = self.config.get('file_stability_tries', 10)
        sleep_sec = self.config.get('file_stability_sleep', 1)
        for _ in range(max_tries):
            try:
                current_size = os.path.getsize(file_path)
                if current_size == last_size:
                    stable = True
                    break
                last_size = current_size
                time.sleep(sleep_sec)
            except FileNotFoundError:
                time.sleep(5)

        if not stable:
            logging.warning(f"File {filename} not stable or disappeared. Skipping.")
            return

        processed_files.add(filename)
        logging.info(f"New file detected: {filename}")

        try:
            raw_records, valid_df = process_file(file_path, self.config)

            if not raw_records or valid_df is None or valid_df.empty:
                reason = "No valid data found after processing"
                logging.warning(f"{filename} - {reason}")
                log_quarantine(file_path, reason)
                return

            agg_df = aggregate_metrics(valid_df, self.config, filename)

            conn = get_connection(self.config)
            try:
                with conn:
                    insert_raw_data(conn, raw_records, file_name=filename, data_source=self.data_source)
                    insert_aggregated_data(conn, agg_df)
            except Exception as db_err:
                logging.error(f"DB insert failed: {db_err}")
                raise
            finally:
                conn.close()

            move_file(file_path, PROCESSED_FOLDER)
            logging.info(f"Successfully processed: {filename}")

        except Exception as e:
            logging.error(f"Error processing {filename}: {e}")
            log_quarantine(file_path, str(e))

def main():
    config = load_config("air_quality.yaml")  # Change config here if needed

    observer = Observer()
    event_handler = NewCSVHandler(config)
    observer.schedule(event_handler, DATA_FOLDER, recursive=False)
    observer.start()
    logging.info(f"Started monitoring folder: {DATA_FOLDER}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()

