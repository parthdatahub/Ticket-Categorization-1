import pandas as pd
from datetime import datetime

# ------------------------
# Threshold Config
# ------------------------
THRESHOLD = 0.75
OUTPUT_FILE = "model_analysis_report.xlsx"

def gen_report(response):
    """
    Generate analysis report from ML prediction response.

    Args:
        response (dict): The response object returned from send_updates(ml_response).
    """
    output_file = OUTPUT_FILE
    threshold = THRESHOLD

    print("DEBUG: Response received:", response)

    if not isinstance(response, dict) or "result" not in response:
        raise ValueError("❌ Invalid response format. 'result' key missing.")

    result_data = response["result"]

    # Handle single incident dict by wrapping it in a list
    if isinstance(result_data, dict):
        result_data = [result_data]

    rows = []

    for incident in result_data:
        opened_at = incident.get("opened_at")
        try:
            date_str = datetime.strptime(opened_at, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y") if opened_at else datetime.now().strftime("%d-%m-%Y")
        except ValueError:
            date_str = datetime.now().strftime("%d-%m-%Y")

        pri_conf = incident.get("Priority", {}).get("Confidence", 0)
        cat_conf = incident.get("Category", {}).get("Confidence", 0)
        sub_conf = incident.get("Subcategory", {}).get("Confidence", 0)
        ag_conf  = incident.get("Assignment_Group", {}).get("Confidence", 0)

        pri_change = 1 if pri_conf >= threshold else 0
        cat_change = 1 if cat_conf >= threshold else 0
        sub_change = 1 if sub_conf >= threshold else 0
        ag_change  = 1 if ag_conf  >= threshold else 0

        total_changes = pri_change + cat_change + sub_change + ag_change

        rows.append({
            "Date": date_str,
            "Priority": pri_change,
            "Category": cat_change,
            "Subcategory": sub_change,
            "Assignment Group": ag_change,
            "Total Changes": total_changes
        })

    df = pd.DataFrame(rows)
    report = df.groupby("Date").sum().reset_index()
    report.to_excel(output_file, index=False)

    print(f"✅ Analysis report saved as {output_file}")
    return report


def wrap_incident_for_report(raw_incident):
    """
    Wraps a raw ServiceNow incident dict into the format expected by gen_report().
    Adds dummy confidence values if missing.
    """
    wrapped = {
        "Incident_ID": raw_incident.get("number", "unknown"),
        "opened_at": raw_incident.get("opened_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "Priority": {"Confidence": raw_incident.get("priority_confidence", 0.8)},
        "Category": {"Confidence": raw_incident.get("category_confidence", 0.9)},
        "Subcategory": {"Confidence": raw_incident.get("subcategory_confidence", 0.85)},
        "Assignment_Group": {"Confidence": raw_incident.get("assignment_group_confidence", 0.95)}
    }
    return {"result": [wrapped]}
