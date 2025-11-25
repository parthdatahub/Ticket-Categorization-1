import joblib
import pandas as pd
import json
from datetime import datetime

# Load model
model = joblib.load("assignment_group_classifier_model_P3_12.pkl")

# Priority mapping
PRIORITY_MAP = {
    "1": "p1 - critical",
    "2": "p2 - high",
    "3": "p3 - medium",
    "4": "p4 - low",
    "5": "p5 - planning"
}

# Read API response from .txt
with open("Incident_API response.txt", "r") as f:
    text_data = f.read()

# Extract JSON object (everything after "Response for incident API:")
start_idx = text_data.find("{")
try:
    api_data = json.loads(text_data[start_idx:])
except json.JSONDecodeError as e:
    raise ValueError("❌ Failed to parse Incident_API response.txt") from e

results = []

# Helper: normalize safely
def safe_val(v, default="unknown"):
    if v is None:
        return default
    if isinstance(v, str):
        v = v.strip()
        return v.lower() if v else default
    return str(v).lower() if v else default

for incident in api_data.get("result", []):
    # Parse opened_at
    opened_at = incident.get("opened_at")
    try:
        dt = datetime.strptime(opened_at, "%Y-%m-%d %H:%M:%S") if opened_at else datetime.now()
    except ValueError:
        dt = datetime.now()

    # Build model-ready dataframe (null-safe)
    new_ticket = pd.DataFrame([{
        "Subcategory": safe_val(incident.get("subcategory")),
        "Category": safe_val(incident.get("category")),
        "Priority": PRIORITY_MAP.get(str(incident.get("priority")), "p3 - medium"),
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
    }])

    # Predict
    predicted_group = model.predict(new_ticket)[0]
    predicted_proba = model.predict_proba(new_ticket)[0]
    confidence_score = round(float(predicted_proba.max()), 2)

    results.append({
        "Incident_ID": incident.get("number", "unknown"),
        "Assignment_Group": predicted_group,
        "Confidence_Score": confidence_score
    })

# Save results to JSON file
output_file = "incidents_predictions.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=4)

print(f"✅ Predictions saved to {output_file}")
