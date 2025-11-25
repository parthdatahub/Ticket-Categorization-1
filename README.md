# 🛠️ Incident Assignment Group Predictor

This project automates the classification of IT incidents by predicting the appropriate assignment group using a machine learning model. It also updates the incident records via a REST API based on prediction confidence.

---

## 📌 Project Overview

- Loads incident data from a ServiceNow-like API response.
- Preprocesses and transforms the data into a model-ready format.
- Uses a trained classifier (`.pkl` model) to predict the assignment group.
- Sends updates to the incident management system via REST API if confidence exceeds a threshold.

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://your-repo-url.git
cd your-project-folder


###  2. Install Dependencies
pip install -r requirements.txt

3. Create a .env File
Change the details of the respective elements 
user=your_api_username
pwd=your_api_password
url=https://your-instance.service-now.com/api/now/table/incident
threshold=0.75

🧠 Usage
1. Fetch,Load and Predict Assignment Groups
execute the following function
python run.py 
