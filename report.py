import json
import pandas as pd
from datetime import datetime

def gen_report(predictions):

    # ------------------------
    # Config
    # ------------------------
    # #INPUT_FILE = "incidents_predictions_v3.json"
    OUTPUT_FILE = "model_analysis_report.xlsx"
    THRESHOLD = 0.1  # confidence cutoff
    #
    # # ------------------------
    # # Load Predictions
    # # ------------------------
    # with open(INPUT_FILE, "r") as f:
    #     predictions = json.load(f)

    rows = []

    # ------------------------
    # Process Each Ticket
    # ------------------------

    for incident in predictions:
        incident_id = incident.get("Incident_ID", "unknown")

        # Example: assume sys_created_on / opened_at is in the incident (fake now as today's date)
        date_str = datetime.now().strftime("%d-%m-%Y")

        # Apply thresholds
        pri_change = 1 if incident["Priority"]["Confidence"] >= THRESHOLD else 0
        cat_change = 1 if incident["Category"]["Confidence"] >= THRESHOLD else 0
        sub_change = 1 if incident["Subcategory"]["Confidence"] >= THRESHOLD else 0
        ag_change = 1 if incident["Assignment_Group"]["Confidence"] >= THRESHOLD else 0

        total_changes = pri_change + cat_change + sub_change + ag_change

        rows.append({
            "Date": date_str,
            "Priority": pri_change,
            "Category": cat_change,
            "Subcategory": sub_change,
            "Assignment Group": ag_change,
            "Total Changes": total_changes
        })

    # ------------------------
    # Convert to DataFrame
    # ------------------------
    df = pd.DataFrame(rows)

    # Group by Date (aggregate counts)
    report = df.groupby("Date").sum().reset_index()

    # ------------------------
    # Save to Excel
    # ------------------------
    report.to_excel(OUTPUT_FILE, index=False)

    print(f"✅ Analysis report saved as {OUTPUT_FILE}")
