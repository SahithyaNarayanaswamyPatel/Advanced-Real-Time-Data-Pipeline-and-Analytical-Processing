import psycopg2
import psycopg2.extras
import yaml
import logging
import time
from datetime import datetime

def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def get_connection(config):
    try:
        db_cfg = config.get('db', {})
        return psycopg2.connect(
            host=db_cfg.get("host", "localhost"),
            database=db_cfg.get("database", "dbname"),
            user=db_cfg.get("user", "username"),
            password=db_cfg.get("password", "password")
        )
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None

def insert_raw_data(conn, raw_records, file_name=None, data_source=None, max_retries=3):
    query = """
        INSERT INTO raw_data (
            file_name,
            data_source,
            sensor_id,
            timestamp,
            location,
            "CO(GT)",
            "PT08.S1(CO)",
            "NMHC(GT)",
            "C6H6(GT)",
            "PT08.S2(NMHC)",
            "NOx(GT)",
            "PT08.S3(NOx)",
            "NO2(GT)",
            "PT08.S4(NO2)",
            "PT08.S5(O3)",
            "T",
            "RH",
            "AH",
            created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    data_to_insert = []
    for rec in raw_records:
        sensor_id = rec.get('sensor_id')
        timestamp = rec.get('DateTime') or rec.get('timestamp')
        location = rec.get('location')

        co_gt = rec.get('CO(GT)')
        pt08_s1_co = rec.get('PT08.S1(CO)')
        nmhc_gt = rec.get('NMHC(GT)')
        c6h6_gt = rec.get('C6H6(GT)')
        pt08_s2_nmhc = rec.get('PT08.S2(NMHC)')
        nox_gt = rec.get('NOx(GT)')
        pt08_s3_nox = rec.get('PT08.S3(NOx)')
        no2_gt = rec.get('NO2(GT)')
        pt08_s4_no2 = rec.get('PT08.S4(NO2)')
        pt08_s5_o3 = rec.get('PT08.S5(O3)')
        t = rec.get('T')
        rh = rec.get('RH')
        ah = rec.get('AH')

        data_to_insert.append((
            file_name,
            data_source,
            sensor_id,
            timestamp,
            location,
            co_gt,
            pt08_s1_co,
            nmhc_gt,
            c6h6_gt,
            pt08_s2_nmhc,
            nox_gt,
            pt08_s3_nox,
            no2_gt,
            pt08_s4_no2,
            pt08_s5_o3,
            t,
            rh,
            ah,
            datetime.utcnow()
        ))

    attempt = 0
    while attempt < max_retries:
        try:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, query, data_to_insert)
                conn.commit()
                logging.info(f"Inserted {len(data_to_insert)} raw records into raw_data")
            break
        except Exception as e:
            conn.rollback()
            attempt += 1
            logging.error(f"Insert attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait = 2 ** attempt
                logging.info(f"Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                logging.error("Max retries reached. Failed to insert raw data.")

def insert_aggregated_data(conn, agg_df):
    table = "aggregated_data"
    try:
        with conn.cursor() as cur:
            cols = list(agg_df.columns)
            values = [tuple(row) for row in agg_df.to_numpy()]
            insert_query = f"""
                INSERT INTO {table} ({', '.join(cols)})
                VALUES ({', '.join(['%s'] * len(cols))})
            """
            psycopg2.extras.execute_batch(cur, insert_query, values)
            conn.commit()
            logging.info(f"Inserted {len(agg_df)} aggregated rows into {table}")
    except Exception as e:
        logging.error(f"Failed to insert aggregated data: {e}")
        conn.rollback()

