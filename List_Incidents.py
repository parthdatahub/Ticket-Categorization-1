from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timedelta

def get_incidents():
    load_dotenv()
    user = os.getenv("user")
    pwd = os.getenv("pwd")
    base_url = os.getenv("url")

    # Set the request parameters
    request_url = base_url + "incident"
    #request_url = "https://woodplcdev.service-now.com/api/now/table/incident?sysparm_query=active%3Dtrue%5Euniversal_requestISEMPTY"

    print("Request URL:", request_url)

    # Example: Get incidents created in the last 10 minutes
    time_window_minutes = 10
    time_filter = (datetime.utcnow() - timedelta(minutes=time_window_minutes)).strftime('%Y-%m-%d %H:%M:%S')

    # sys_created_on is the field that tracks when the record was created
    query_string = f"sys_created_on>={time_filter}^active=true"
    #query_string = 'active%3Dtrue%5Euniversal_requestISEMPTY'
    #query_string = 'active=true^state>=1'
    #query_string = 'active=true^stateIN1' # 24 uncomments 27 comments used for all incidents.

    params = {
        'sysparm_query': query_string,
        #'sysparm_limit': 1

    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.get(request_url, auth=(user, pwd), headers=headers, params=params, verify=False)
    #response = requests.get(request_url, auth=(user, pwd), headers=headers)
    print("URL:", response.url)
    print("Status Code:", response.status_code)
    print("Response text is :",response.text)
    print("Headers:", response.headers)

    if response.status_code != 200:
        print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:', response.json())
        exit()

    data = response.json()
    return data
