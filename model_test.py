# ===== Example Usage (Quick Local Test) =====
import json
from ml_loader import model_loader  # make sure ml_loader.py is in the same directory

# Simulated ServiceNow-style API payload
sample_payload = {
    "result": [
        {
            "number": "INC100001",
            "short_description": "My email ID is not working, need password reset.",
            "description": "User unable to access Outlook and Teams after changing password.",
            "cmdb_ci": "Generic",
            "location": "IN.TN.Chennai.1.Zenith Building",
            "impact": 3,
            "urgency": 3,
            "caller_id": {"value": "user@example.com"},
            "opened_by": {"value": "user@example.com"},
            "opened_at": "2024-10-01 09:15:00"
        }
    ]
}

# Run model prediction
output = model_loader(sample_payload)

# Pretty print JSON result
print("\n🔍 Model Output:")
print(json.dumps(output, indent=2))
