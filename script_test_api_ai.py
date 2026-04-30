import requests

API_URL = "http://localhost:8000/api/v1/triage/ai/"

def test_triage_ai():
    data = {
        "description": "45-year-old male presents with chest pain radiating to the left arm, sweating, and shortness of breath."
    }
    response = requests.post(API_URL, json=data)
    print("Status Code:", response.status_code)
    print("Response:", response.json())

if __name__ == "__main__":
    test_triage_ai()
