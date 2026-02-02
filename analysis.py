from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime

# Open CSV file and load data into DataFrame
data = pd.read_csv('.\\benchmark_results\\local.CSV', encoding='latin-1', decimal='.', thousands=',')
# Remove leading/trailing whitespace and special characters (like BOM) from column names
data.columns = data.columns.str.strip().str.replace('\ufeff', '', regex=False)

# Show the first few rows of the DataFrame
print(data.head())
print(f"\nColumn names: {data.columns[:5].tolist()}")  # Print first 5 column names to verify

# Filter columns to keep only the relevant metrics
columns_to_keep = [
    'Potenza totale CPU [W]',
    "CPU Package Power [W]",
    'Potenza Core IA [W]',
    "IA Cores Power [W]",
    'VR VCC Corrente (SVID IOUT) [A]',
    "VR VCC Current (SVID IOUT) [A]"
    'GPU Potenza [W]',
    "GPU Power [W]",
    'IGPU Potenza [W]',
    "IGPU Power [W]"
    'Potenza DRAM totale [W]',
    'Consumo energetico resto del chip [W]',
    'Rest-of-Chip Power [W]'
]

# Keep only columns that exist in the DataFrame
existing_columns = [col for col in columns_to_keep if col in data.columns]
data_filtered = data[existing_columns]

# Convert all columns to numeric values, handling errors
for col in data_filtered.columns:
    data_filtered[col] = pd.to_numeric(data_filtered[col], errors='coerce')

# Replace NaN values with 0
data_filtered = data_filtered.fillna(0)

print(data_filtered.head())
print(data_filtered.dtypes)

# Plot each metric in a separate subplot for better readability
# Plot each metric in a separate figure
# for column in data_filtered.columns:
#     plt.figure(figsize=(12, 4))
#     plt.plot(data_filtered.index, data_filtered[column], label=column)
#     plt.ylabel('Power (W)')
#     plt.xlabel('Time (Index)')
#     plt.title(column)
#     plt.grid(True)
#     # Show only 10 evenly spaced x-axis labels
#     step = max(1, len(data_filtered) // 10)
#     plt.xticks(np.arange(0, len(data_filtered), step))
#     plt.tight_layout()

# plt.show()

import json

# Convert the first two time-related columns to datetime
# Combine Date and Time columns to create a datetime column
data_filtered['timestamp'] = pd.to_datetime(
    data['Date'] + ' ' + data['Time'],
    format='%d.%m.%Y %H:%M:%S.%f',
    errors='coerce'
)

print(f"\nCSV time range (corrected): {data_filtered['timestamp'].min()} to {data_filtered['timestamp'].max()}")

# Load JSON benchmark data
json_file = '.\\benchmark_results\\benchmark_qwen_qwen3-4b-thinking-2507_20260126_004413.json'
with open(json_file, 'r', encoding='utf-8') as f:
    benchmark_data = json.load(f)

# Extract request data and timestamps from JSON
request_events = []
if 'results' in benchmark_data:
    for entry in benchmark_data['results']:
        request_events.append({
            'timestamp_send': pd.to_datetime(entry['timestamp_send']),
            'timestamp_response': pd.to_datetime(entry['timestamp_response']),
            'total_tokens': entry.get('total_tokens', 0),
            'elapsed_time': entry.get('elapsed_time_seconds', 0),
            'size_category': entry.get('size_category', 'unknown')
        })

# Convert to DataFrame
request_df = pd.DataFrame(request_events)

if len(request_df) > 0:
    print(f"\nJSON time range: {request_df['timestamp_send'].min()} to {request_df['timestamp_send'].max()}")
    print(f"Total requests: {len(request_df)}")
    
    # Get the first timestamp_send and last timestamp_response from JSON
    first_json_timestamp = request_df['timestamp_send'].min()
    last_json_timestamp = request_df['timestamp_response'].max()
    print(f"\nFirst timestamp_send in JSON: {first_json_timestamp}")
    print(f"Last timestamp_response in JSON: {last_json_timestamp}")
    
    # Filter CSV data to show only from first request send to last response
    data_filtered = data_filtered[
        (data_filtered['timestamp'] >= first_json_timestamp) & 
        (data_filtered['timestamp'] <= last_json_timestamp)
    ].copy()
    print(f"CSV data filtered to {len(data_filtered)} rows (from first request to last response)")
    
    # For each request, find the closest CSV measurement
    request_df['csv_index'] = request_df['timestamp_send'].apply(
        lambda req_time: (data_filtered['timestamp'] - req_time).abs().idxmin() 
        if pd.notna(data_filtered['timestamp']).any() else None
    )
    
    # Get the closest timestamp for each request
    request_df['closest_csv_time'] = request_df['csv_index'].apply(
        lambda idx: data_filtered.loc[idx, 'timestamp'] if idx is not None else None
    )
    
    request_df['time_diff_seconds'] = (request_df['timestamp_send'] - request_df['closest_csv_time']).dt.total_seconds()
    
    print(f"\nTime difference statistics (seconds):")
    print(request_df['time_diff_seconds'].describe())

# Define colors for each category
category_colors = {
    'short': 'green',
    'medium': 'skyblue',
    'long': 'red',
}

# Plot power metrics with request time bands
for column in existing_columns:
    plt.figure(figsize=(14, 6))
    
    # Plot power data vs timestamp
    ax1 = plt.gca()
    ax1.plot(data_filtered['timestamp'], data_filtered[column], label=column, color='blue', linewidth=1.5)
    ax1.set_ylabel('Power (W)', color='blue', fontsize=12)
    ax1.set_xlabel('Time', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True, alpha=0.3)
    
    # Add time bands for each request
    if len(request_df) > 0:
        # Track which categories have been added to legend
        added_to_legend = set()
        
        for idx, row in request_df.iterrows():
            category = row['size_category']
            color = category_colors.get(category, 'lightgray')
            label = f'{category.capitalize()} Request' if category not in added_to_legend else None
            
            # Draw vertical span from timestamp_send to timestamp_response
            ax1.axvspan(row['timestamp_send'], row['timestamp_response'], 
                       alpha=0.3, color=color, label=label)
            
            if label:
                added_to_legend.add(category)
    
    plt.title(f'{column} with LLM Request Time Periods', fontsize=14, fontweight='bold')
    ax1.legend(loc='lower left')
    
    # Format x-axis for better readability
    plt.gcf().autofmt_xdate()
    plt.tight_layout()

plt.show()