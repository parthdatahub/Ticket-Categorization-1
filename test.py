import requests
import pandas as pd
import datetime
import numpy as np
import os
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# ==== CONFIGURATION ====
load_dotenv()
user =os.getenv("user")
pwd =os.getenv("pwd")
SN_INSTANCE="https://dev296254.service-now.com"
# API endpoint
INCIDENT_API = "https://dev296254.service-now.com/api/now/table/incident?sysparm_query=200&sysparm_limit=200"
SLA_API = f"{SN_INSTANCE}/api/now/table/task_sla"
AUDIT_API = f"{SN_INSTANCE}/api/now/table/sys_audit"

# ==== STEP 1: GET INCIDENTS ====
def get_closed_incidents():
    query = "state=6^ORstate=7"  # 6=Resolved, 7=Closed
    fields = "number,short_description,category,subcategory,priority,assignment_group,assigned_to,opened_by,opened_at,resolved_at,closed_at,close_code,close_notes,reassignment_count,sys_updated_on"
    url = f"{INCIDENT_API}"#sysparm_query={query}&sysparm_fields={fields}&sysparm_limit=200
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    r = requests.get(url, auth=HTTPBasicAuth(user, pwd),headers=headers )
    r.raise_for_status()
    return pd.DataFrame(r.json()["result"])

# ==== STEP 2: GET SLA INFO ====
def get_sla_for_ticket(ticket_number):
    url = f"{SLA_API}?sysparm_query=task.number={ticket_number}&sysparm_fields=has_breached"
    #url = f'https://dev296254.service-now.com/api/now/table/task_sla?sysparm_query=task.number%3DINC0000060&sysparm_limit=1&sysparm_fields=has_breached
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    r = requests.get(url, auth=HTTPBasicAuth(user, pwd), headers=headers)
    r.raise_for_status()
    records = r.json()["result"]
    return not any(rec["has_breached"] == "true" for rec in records)  # True if SLA met

# ==== STEP 3: GET REASSIGNMENT HISTORY ====
def get_reassignment_count(ticket_number):
    url = f"{AUDIT_API}?sysparm_query=documentkey={ticket_number}^fieldname=assignment_group"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    r = requests.get(url, auth=HTTPBasicAuth(user, pwd), headers=headers)
    r.raise_for_status()
    return len(r.json()["result"])

# ==== STEP 4: DERIVE EXTRA KPIs & SCORES ====
def compute_quality_scores(notes, category):
    length = len(notes) if notes else 0
    clarity = min(5, max(1, length // 50))
    completeness = 5 if ("steps" in (notes or "").lower()) else 3
    professionalism = 5 if notes and notes[0].isupper() else 3
    accuracy = 4 if category.lower() in (notes or "").lower() else 2
    actionability = 4 if "restarted" in (notes or "").lower() else 2
    tqi = int((clarity*0.2 + completeness*0.3 + professionalism*0.1 + accuracy*0.2 + actionability*0.2) * 20)
    
    if tqi < 40:
        recommendation = "Critical: Resolution notes incomplete. Add detailed steps."
    elif tqi < 70:
        recommendation = "Improve: Expand resolution notes and ensure closure code accuracy."
    else:
        recommendation = "Good: Meets quality standards."
    
    return clarity, completeness, professionalism, accuracy, actionability, tqi, recommendation

# ==== MAIN PIPELINE ====
def run_pipeline():
    incidents = get_closed_incidents()
    records = []
    
    for _, row in incidents.iterrows():
        ticket_number = row["number"]
        
        # SLA met
        sla_met = get_sla_for_ticket(ticket_number)
        
        # Reassignment count (override if available in sys_audit)
        reassignment_count = get_reassignment_count(ticket_number)# or int(row.get("reassignment_count", 0))
        
        # MTTR hours
        opened = pd.to_datetime(row["opened_at"])
        resolved = pd.to_datetime(row["resolved_at"]) if row["resolved_at"] else pd.to_datetime(row["closed_at"])
        mttr_hours = (resolved - opened).total_seconds() / 3600 if resolved and opened else None
        
        # KB linkage (dummy placeholder, depends on field in your instance)
        kb_linked = bool(np.random.choice([True, False], p=[0.7, 0.3]))
        
        # Quality Scores
        clarity, completeness, professionalism, accuracy, actionability, tqi, recommendation = compute_quality_scores(
            row.get("close_notes", ""), row.get("category", "")
        )
        
        records.append({
            "number": ticket_number,
            "short_description": row.get("short_description"),
            "category": row.get("category"),
            "subcategory": row.get("subcategory"),
            "priority": row.get("priority"),
            "assignment_group": row.get("assignment_group"),
            "assigned_to": row.get("assigned_to"),
            "opened_by": row.get("opened_by"),
            "opened_at": row.get("opened_at"),
            "resolved_at": row.get("resolved_at"),
            "closed_at": row.get("closed_at"),
            "close_code": row.get("close_code"),
            "resolution_notes": row.get("close_notes"),
            "reassignment_count": reassignment_count,
            "sla_met": sla_met,
            "mttr_hours": mttr_hours,
            "kb_linked": kb_linked,
            "clarity_score": clarity,
            "completeness_score": completeness,
            "professionalism_score": professionalism,
            "accuracy_score": accuracy,
            "actionability_score": actionability,
            "ticket_quality_index": tqi,
            "recommendation_text": recommendation
        })
    
    df_final = pd.DataFrame(records)
    df_final.to_excel("ticket_quality_dashboard_servicenow.xlsx", index=False)
    print("✅ Dataset saved as ticket_quality_dashboard_servicenow.xlsx")

# ==== RUN ====
if __name__ == "__main__":
    run_pipeline()
