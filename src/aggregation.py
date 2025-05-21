from datetime import datetime
import pandas as pd

def aggregate_metrics(df, config, file_name):
    sensor_columns = config.get("sensor_columns", [])
    group_by = config.get("aggregation", {}).get("group_by", [])
    data_source = config.get("data_source", "air_quality_sensor")

    if not sensor_columns:
        raise ValueError("No sensor_columns specified in config.")

    if not group_by:
        raise ValueError("No group_by keys provided for aggregation.")

    if not set(group_by).issubset(df.columns):
        missing = set(group_by) - set(df.columns)
        raise ValueError(f"Missing group_by columns in data: {missing}")

    if not set(sensor_columns).issubset(df.columns):
        missing = set(sensor_columns) - set(df.columns)
        raise ValueError(f"Missing sensor columns in data: {missing}")

    agg_funcs = ['min', 'max', 'mean', 'std']
    grouped = df.groupby(group_by)[sensor_columns].agg(agg_funcs)

    # Flatten multi-index columns to single level with format "sensor_metric"
    grouped.columns = ['{}_{}'.format(sensor, metric) for sensor, metric in grouped.columns]
    grouped.reset_index(inplace=True)

    # Melt the dataframe to long format
    melted = grouped.melt(id_vars=group_by, var_name='sensor_metric', value_name='metric_value')

    # Split sensor_metric into sensor_name and metric_type
    melted[['sensor_name', 'metric_type']] = melted['sensor_metric'].str.rsplit('_', n=1, expand=True)

    # Add extra columns required by DB
    melted['data_source'] = data_source
    melted['file_name'] = file_name
    melted['aggregation_timestamp'] = datetime.utcnow()
    melted['created_at'] = datetime.utcnow()

    # Select and reorder columns to match DB schema
    final_df = melted[['data_source', 'file_name', 'sensor_name', 'metric_type', 'metric_value', 'aggregation_timestamp', 'created_at']]

    # Optional: Drop rows with NaN metric values (std could be NaN if only one record in group)
    final_df = final_df.dropna(subset=['metric_value'])

    return final_df

