import json
import joblib
import pandas as pd
from datetime import datetime,timedelta

import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the lowest level of logging. It will capture all levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Logs will be displayed on the console
        logging.FileHandler('ml_model.log')  # Logs will be written to this file
    ]
)

current_date = datetime.now().strftime("%d-%m-%Y")

# ------------------------
# Load Models
# ------------------------
assignment_group_model = joblib.load("assignment_group_model.pkl")
category_model = joblib.load("category_model.pkl")
subcategory_model = joblib.load("subcategory_model.pkl")


# ------------------------
# Priority Mapping Function
# ------------------------

def map_priority_with_confidence(impact: int = None, urgency: int = None):
    priority_matrix = {
        (1, 1): "1 - Critical", (1, 2): "2 - High", (1, 3): "3 - Moderate", (1, 4): "4 - Low",
        (2, 1): "2 - High", (2, 2): "2 - High", (2, 3): "3 - Moderate", (2, 4): "4 - Low",
        (3, 1): "3 - Moderate", (3, 2): "3 - Moderate", (3, 3): "3 - Moderate", (3, 4): "4 - Low",
        (4, 1): "4 - Low", (4, 2): "4 - Low", (4, 3): "4 - Low", (4, 4): "4 - Low"
    }

    if impact is None or urgency is None:
        return "p3 - medium", 0.50

    priority = priority_matrix.get((impact, urgency), "p3 - medium")
    return priority, 1.00

import pandas as pd

def search_and_map(excel_path, search_column, target_column, search_value):
    # Load the Excel file
    df = pd.read_excel(excel_path, engine='openpyxl')

    # Convert search column to lowercase for case-insensitive comparison
    df['__search_lower__'] = df[search_column].astype(str).str.lower()
    search_value_lower = search_value.lower()

    # Find matching row
    matched_row = df[df['__search_lower__'] == search_value_lower]


    if not matched_row.empty:
        # Get the corresponding value from the target column
        result = matched_row.iloc[0][target_column]
        return result
    else:
        return f"'{search_value}' not found in column '{search_column}'."

# Example usage
cat_excel_file = "Category.xlsx"  # Replace with your actual file path
subcat_excel_file = "Subcategory.xlsx"  # Replace with your actual file path
search_column = "Text"      # Column to search in
target_column = "Value"      # Column to retrieve value from
search_value = "VPN Issue"     # String to search





def get_incidents(incident_list):
    incident = []
    #print(type(incident_list))
    count = len(incident_list["result"])
    print("Number of incidents is ",count)
    for i in range(count):
        incident.append(incident_list["result"][i])
    return incident

def model_loader(incident_list):
    api_data = get_incidents(incident_list)
    logging.info(f"Ml loader started with incidents:{incident_list}")

    def safe_val(v, default="unknown"):
        if v is None:
            return default
        if isinstance(v, str):
            v = v.strip()
            return v.lower() if v else default
        return str(v).lower() if v else default

    results = []

    for incident in api_data:
        # Parse datetime
        opened_at = incident.get("opened_at")
        try:
            dt = datetime.strptime(opened_at, "%Y-%m-%d %H:%M:%S") if opened_at else datetime.now()
        except ValueError:
            dt = datetime.now()

            # Validate caller_id and opened_by
        caller_id = incident.get("caller_id")
        opened_by = incident.get("opened_by")

        if not isinstance(caller_id, dict) or "value" not in caller_id:
            logging.info(f"⚠️ Skipping incident due to malformed opened_by: {caller_id}")
            print(f"⚠️ Skipping incident due to malformed caller_id: {caller_id}")
            continue
        if not isinstance(opened_by, dict) or "value" not in opened_by:
            logging.info(f"⚠️ Skipping incident due to malformed opened_by: {opened_by}")
            print(f"⚠️ Skipping incident due to malformed opened_by: {opened_by}")
            continue

        # Build common feature row
        features = {
            "Subcategory": safe_val(incident.get("subcategory")),
            "Category": safe_val(incident.get("category")),
            "Priority": safe_val(incident.get("priority"), "p3 - medium"),
            "Configuration item": safe_val(incident.get("cmdb_ci"), "generic"),
            "Location": safe_val(incident.get("location")),
            "Business unit": safe_val(incident.get("business_unit"), "wood - operations"),
            "Legal Entity": safe_val(incident.get("company"), "wood group psn australia pty limited"),
            "Reported By": safe_val(incident.get("caller_id", {}).get("value")),
            "Opened by": safe_val(incident.get("opened_by", {}).get("value")),
            "Hour": dt.hour,
            "Week Day": dt.weekday(),
            "Opened Month": dt.month,
            "Opened Year": dt.year,
            "Team Classfication": safe_val(incident.get("team_classification"), "gsd")
        }
        df_ticket = pd.DataFrame([features])

        # ------------------------
        # 1) Assignment Group
        # ------------------------
        ag_pred = assignment_group_model.predict(df_ticket)[0]
        ag_conf = round(float(assignment_group_model.predict_proba(df_ticket).max()), 2)

        # ------------------------
        # 2) Category
        # ------------------------
        cat = category_model.predict(df_ticket)[0]
        cat_pred = search_and_map(cat_excel_file, search_column, target_column, cat)
        cat_conf = round(float(category_model.predict_proba(df_ticket).max()), 2)

        # ------------------------
        # 3) Subcategory
        # ------------------------
        subcat = subcategory_model.predict(df_ticket)[0]
        subcat_pred=search_and_map(subcat_excel_file, search_column, target_column, subcat)
        subcat_conf = round(float(subcategory_model.predict_proba(df_ticket).max()), 2)

        # ------------------------
        # 4) Priority (rule-based)
        # ------------------------
        impact = int(incident.get("impact", 3)) if incident.get("impact") else None
        urgency = int(incident.get("urgency", 3)) if incident.get("urgency") else None
        priority, priority_conf = map_priority_with_confidence(impact, urgency)

        # ------------------------
        # Collect Results
        # ------------------------
        results.append({
            "Incident_ID": incident.get("number", "unknown"),
            "assignment_Group": {"Prediction": ag_pred, "Confidence": ag_conf},
            "category": {"Prediction": cat_pred, "Confidence": cat_conf},
            "subcategory": {"Prediction": subcat_pred, "Confidence": subcat_conf},
            "Priority": {"Prediction": priority, "Confidence": priority_conf}
        })
    logging.info(f"⚠️ Results got are: {results}")
    return results

