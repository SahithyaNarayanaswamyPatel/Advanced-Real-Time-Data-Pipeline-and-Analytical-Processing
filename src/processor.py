import pandas as pd
import logging
import yaml
import os
from datetime import datetime

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_and_transform(df, config):
    field_rules = config['fields']
    transformations = config.get('transformations', {})
    required_fields = list(field_rules.keys())

    missing_fields = [field for field in required_fields if field not in df.columns]
    if missing_fields:
        logging.error(f"Missing required fields: {missing_fields}")  # <-- Added explicit logging here
        return [], pd.DataFrame(), [f"Missing required fields: {missing_fields}"]

    df = df.copy()
    quarantine_rows = []
    valid_rows = []

    # Build timestamp column from Date + Time or use DateTime directly
    datetime_format = config.get("datetime_format", "%d/%m/%Y %H.%M.%S")
    if 'Date' in df.columns and 'Time' in df.columns:
        # Additional check for null or invalid Date/Time strings
        null_date = df['Date'].isna().any() or (df['Date'].astype(str).str.strip() == '').any()
        null_time = df['Time'].isna().any() or (df['Time'].astype(str).str.strip() == '').any()
        if null_date or null_time:
            logging.warning("Null or empty values found in Date or Time columns")

        df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format=datetime_format, errors='coerce')
    elif 'DateTime' in df.columns:
        df['DateTime'] = pd.to_datetime(df['DateTime'], format=datetime_format, errors='coerce')
    else:
        # If no datetime info, fail all
        logging.error("Missing DateTime information in input data")  # <-- Added explicit logging here
        return [], pd.DataFrame(), ["Missing DateTime information"]

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_errors = []

        # Check DateTime parsing
        if pd.isna(row_dict['DateTime']):
            row_errors.append("Invalid or missing DateTime")

        # Validate all required fields
        for field, rules in field_rules.items():
            value = row_dict.get(field)
            if pd.isna(value):
                row_errors.append(f"{field} is null")
                continue

            # If field type is string, check non-empty string for Date and Time explicitly
            if rules.get('type') == 'string' and field in ['Date', 'Time']:
                if not isinstance(value, str) or not value.strip():
                    row_errors.append(f"{field} is empty or not a string")
                    continue

            expected_type = rules.get('type')
            try:
                if expected_type == 'float':
                    value = float(value)
                elif expected_type == 'int':
                    value = int(value)
                elif expected_type == 'datetime':
                    # Already converted, skip
                    pass
            except Exception:
                row_errors.append(f"{field} has invalid type")
                continue

            min_val = rules.get('min')
            max_val = rules.get('max')
            if isinstance(value, (int, float)):
                if min_val is not None and value < min_val:
                    row_errors.append(f"{field} below min ({min_val})")
                if max_val is not None and value > max_val:
                    row_errors.append(f"{field} above max ({max_val})")

        if row_errors:
            row_dict['error_reason'] = "; ".join(row_errors)
            quarantine_rows.append(row_dict)
        else:
            # Keep DateTime column name unchanged (no rename)
            clean_dict = {k: v for k, v in row_dict.items() if k in field_rules or k == 'DateTime'}
            valid_rows.append(clean_dict)

    valid_df = pd.DataFrame(valid_rows)

    # Apply transformations to valid_df
    rename_map = {}
    for field, trans in transformations.items():
        if field in valid_df.columns:
            if trans.get("normalize") and valid_df[field].std() > 0:
                valid_df[field] = (valid_df[field] - valid_df[field].mean()) / valid_df[field].std()
            if trans.get("multiply_by"):
                valid_df[field] = valid_df[field] * trans["multiply_by"]
            if trans.get("rename_to"):
                rename_map[field] = trans["rename_to"]

    if rename_map:
        valid_df.rename(columns=rename_map, inplace=True)

    # Convert pandas Timestamps to python datetime for insertion
    for rec in valid_rows:
        for k, v in rec.items():
            if isinstance(v, pd.Timestamp):
                rec[k] = v.to_pydatetime()

    return valid_rows, valid_df, quarantine_rows

def process_file(file_path, config):
    try:
        delimiter = config.get('delimiter', ',')
        encoding = config.get('encoding', 'utf-8')
        decimal = config.get('decimal', '.')

        df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding, decimal=decimal)
        df.replace(-200, pd.NA, inplace=True)

        raw_records, valid_df, quarantine_rows = validate_and_transform(df, config)

        if quarantine_rows:
            os.makedirs('quarantine', exist_ok=True)
            quarantine_file = os.path.join('quarantine', f'invalid_{os.path.basename(file_path)}')
            pd.DataFrame(quarantine_rows).to_csv(quarantine_file, index=False)
            logging.warning(f"Quarantined {len(quarantine_rows)} invalid rows to {quarantine_file}")

        if not raw_records:
            logging.warning(f"All rows in {file_path} are invalid.")
            return None, None

        return raw_records, valid_df

    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
        return None, None

