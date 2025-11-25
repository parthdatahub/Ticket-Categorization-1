import json
import csv
from datetime import datetime
import logging,os
import pandas as pd
 
# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the lowest level of logging. It will capture all levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Logs will be displayed on the console
        logging.FileHandler('incident_comparison.log')  # Logs will be written to this file
    ]
)
 
 
# Function to compare the indicent changes
def compare_jsons(input_json, ml_model_response):
    changes = []
    current_date = datetime.now().strftime("%d-%m-%Y")
    logging.info(f"Started comparison process at {current_date}")
 
    # Loop through input data and corresponding ML model data
    for incident in input_json['result']:
        incident_id = incident['task_effective_number']
        logging.debug(f"Comparing incident {incident_id}...")
        ml_incident = next(item for item in ml_model_response if item['Incident_ID'] == incident_id)
 
        change_count = 0
 
        # Compare assignment group
        if incident['assignment_group']['value'] != ml_incident['assignment_Group']['Prediction']:
            change_count += 1
 
        # Compare category
        if incident['category'] != ml_incident['category']['Prediction']:
            change_count += 1
 
        # Compare subcategory
        if incident['subcategory'] != ml_incident['subcategory']['Prediction']:
            change_count += 1
 
        # Compare priority
        if incident['priority'] != ml_incident['Priority']['Prediction']:
            change_count += 1
 
        # Append results to changes list
        changes.append({
            'Date': current_date,  # Add date to the output
            'Incident': incident_id,
            'Priority': "Yes" if incident['priority'] != ml_incident['Priority']['Prediction'] else "No",
            'Category':"Yes" if incident['category'] != ml_incident['category']['Prediction'] else "No",
            'Subcategory': "Yes" if incident['subcategory'] != ml_incident['subcategory']['Prediction'] else "No",
            'Assignment_Group': "Yes" if incident['assignment_group']['value'] != ml_incident['assignment_Group'][
                'Prediction'] else "No",
            'Global Change': change_count
        })
    logging.info(f"Comparison process completed. Found {len(changes)} incidents with changes.")
    output_file = 'incident_changes.csv'
 
    # Check if the file exists
    if os.path.exists(output_file):
        # Load existing data
        existing_df = pd.read_csv(output_file)
        # Create a DataFrame from new changes
        new_df = pd.DataFrame(changes)
        # Append new data to existing data
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        # Create a new DataFrame if file doesn't exist
        updated_df = pd.DataFrame(changes)
 
    # Save the updated DataFrame to Excel
    updated_df.to_csv(output_file, index=False)
 
    print(f"The Excel file '{output_file}' has been updated or created successfully.")
 
# Compare the JSONs
# changes = compare_jsons(input_json, ml_model_response)
 
# Writing the output to CSV