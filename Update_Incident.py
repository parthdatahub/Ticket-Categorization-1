import requests
from dotenv import load_dotenv
import os
from requests.auth import HTTPBasicAuth

def get_sys_id(incident_number, base_url, user, pwd, headers):
    query_url = f"{base_url}incident"
    params = {
        "sysparm_query": f"number={incident_number}",
        "sysparm_fields": "sys_id"
    }

    response = requests.get(query_url, auth=HTTPBasicAuth(user, pwd), headers=headers, params=params)
    if response.status_code == 200:
        result = response.json().get("result", [])
        if result:
            return result[0].get("sys_id")
    print(f" Failed to fetch sys_id for {incident_number}")
    return None
def send_updates(ml_response):
    print("ml response is ", ml_response)

    load_dotenv()
    user = os.getenv("user")
    pwd = os.getenv("pwd")
    base_url = os.getenv("url")
    threshold = float(os.getenv("threshold"))

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    for item in ml_response:
        incident_number = item.get("Incident_ID")
        if not incident_number:
            print(" Incident_ID missing, skipping item.")
            continue

        sys_id = get_sys_id(incident_number, base_url, user, pwd, headers)
        if not sys_id:
            continue

        url = f"{base_url}incident/{sys_id}"
        print(f" URL: {url}")

        payload = {
            "sys_updated_by": "AI_OPS DEV"
        }

        # Assignment Group
        assignment_data = item.get("assignment_Group")
        if assignment_data:
            assignment_conf = float(assignment_data.get("Confidence", 0))
            assignment_pred = assignment_data.get("Prediction")
            if assignment_conf >= threshold and assignment_pred:
                payload["assignment_group"] = assignment_pred
            else:
                print(f" Skipping assignment group due to low confidence ({assignment_conf})")
        else:
            print("Assignment_Group missing.")

        # Category
        category_data = item.get("category")
        if category_data:
            category_conf = float(category_data.get("Confidence", 0))
            category_pred = category_data.get("Prediction")
            if category_conf >= threshold and category_pred:
                payload["category"] = category_pred
            else:
                print(f" Skipping category due to low confidence ({category_conf})")
        else:
            print("Category missing.")

        # Subcategory
        subcategory_data = item.get("subcategory")
        if subcategory_data:
            subcategory_conf = float(subcategory_data.get("Confidence", 0))
            subcategory_pred = subcategory_data.get("Prediction")
            if subcategory_conf >= threshold and subcategory_pred:
                payload["subcategory"] = subcategory_pred
            else:
                print(f"Skipping subcategory due to low confidence ({subcategory_conf})")
        else:
            print("️ Subcategory missing.")

        # Priority
        priority_data = item.get("priority")
        if priority_data:
            priority_conf = float(priority_data.get("Confidence", 0))
            priority_pred = priority_data.get("Prediction")
            if priority_conf >= threshold and priority_pred:
                payload["priority"] = priority_pred
            else:
                print(f" Skipping priority due to low confidence ({priority_conf})")
        else:
            print(" Priority missing.")

        # Only update if assignment group confidence is above threshold
        print("Payload is ", payload)
        if "assignment_group" in payload:
            try:
                response = requests.put(
                    url,
                    auth=HTTPBasicAuth(user, pwd),
                    headers=headers,
                    json=payload
                )

                if response.status_code != 200:
                    print(f" Failed to update incident {incident_number}")
                    print('Status:', response.status_code)
                    print('Headers:', response.headers)
                    print('Error Response:', response.json())
                    continue

                print(f" Successfully updated incident {incident_number}")
                #print("Response:", response.json())

            except Exception as e:
                print(f" Exception occurred while updating incident {incident_number}: {e}")
                continue
        else:
            print(f"Skipped incident {incident_number} due to missing or low-confidence assignment group.")

    return response.json()
