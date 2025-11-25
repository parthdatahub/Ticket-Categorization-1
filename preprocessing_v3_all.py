import joblib
import pandas as pd
import json
from datetime import datetime

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
        (1, 1): "p1 - critical", (1, 2): "p2 - high", (1, 3): "p3 - medium", (1, 4): "p4 - low",
        (2, 1): "p2 - high",     (2, 2): "p2 - high", (2, 3): "p3 - medium", (2, 4): "p4 - low",
        (3, 1): "p3 - medium",   (3, 2): "p3 - medium", (3, 3): "p3 - medium", (3, 4): "p4 - low",
        (4, 1): "p4 - low",      (4, 2): "p4 - low", (4, 3): "p4 - low", (4, 4): "p4 - low"
    }

    if impact is None or urgency is None:
        return "p3 - medium", 0.50

    priority = priority_matrix.get((impact, urgency), "p3 - medium")
    return priority, 1.00

# ------------------------
# Read API Response
# ------------------------
with open("Incident_API response.txt", "r") as f:
    text_data = f.read()

start_idx = text_data.find("{")
try:
    api_data = json.loads(text_data[start_idx:])
except json.JSONDecodeError as e:
    raise ValueError("❌ Failed to parse Incident_API response.txt") from e

results = []

# ------------------------
# Helper: normalize safely
# ------------------------
def safe_val(v, default="unknown"):
    if v is None:
        return default
    if isinstance(v, str):
        v = v.strip()
        return v.lower() if v else default
    return str(v).lower() if v else default

# ------------------------
# Loop over incidents
# ------------------------
for incident in api_data.get("result", []):
    # Parse datetime
    opened_at = incident.get("opened_at")
    try:
        dt = datetime.strptime(opened_at, "%Y-%m-%d %H:%M:%S") if opened_at else datetime.now()
    except ValueError:
        dt = datetime.now()

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
    cat_pred = category_model.predict(df_ticket)[0]
    cat_conf = round(float(category_model.predict_proba(df_ticket).max()), 2)

    # ------------------------
    # 3) Subcategory
    # ------------------------
    subcat_pred = subcategory_model.predict(df_ticket)[0]
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
        "Assignment_Group": {"Prediction": ag_pred, "Confidence": ag_conf},
        "Category": {"Prediction": cat_pred, "Confidence": cat_conf},
        "Subcategory": {"Prediction": subcat_pred, "Confidence": subcat_conf},
        "Priority": {"Prediction": priority, "Confidence": priority_conf}
    })

# ------------------------
# Save Results
# ------------------------
output_file = "incidents_predictions_v3.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=4)

print(f"✅ Predictions for all 4 fields saved to {output_file}")
