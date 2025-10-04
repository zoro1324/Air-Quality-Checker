"""
Test script for the new prediction_followup endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/prediction-followup/"

# Sample prediction context (as would come from a prediction summary)
prediction_context = {
    "period": "next 7 days",
    "avg_predicted_aqi": 85,
    "avg_pollutants": {
        "pm2_5": 35.5,
        "pm10": 78.2,
        "o3": 45.1,
        "no2": 28.3,
        "so2": 12.1,
        "co": 450.2
    },
    "summary": "Over the next 7 days, air quality is expected to remain at moderate levels with an average AQI of 85. PM2.5 and PM10 levels are the primary concerns. Outdoor activities should be planned carefully, especially for sensitive groups. Farmers should consider the timing of field operations to minimize exposure to higher pollution periods."
}

# Test different types of questions
test_questions = [
    {
        "title": "Farmer Question - Crop Recommendations",
        "question": "What specific crops would you recommend planting during this period?"
    },
    {
        "title": "Activity Question - Outdoor Events",
        "question": "What are the best times for outdoor sports activities during these 7 days?"
    },
    {
        "title": "Health Question - Vulnerable Groups",
        "question": "What precautions should elderly people and children take during this period?"
    },
    {
        "title": "General Follow-up",
        "question": "Will the air quality improve or worsen over this period?"
    }
]

print("=" * 80)
print("TESTING PREDICTION FOLLOW-UP ENDPOINT")
print("=" * 80)

for test in test_questions:
    print(f"\n{'─' * 80}")
    print(f"📝 TEST: {test['title']}")
    print(f"{'─' * 80}")
    print(f"❓ Question: {test['question']}")
    
    payload = {
        "question": test['question'],
        "prediction_context": prediction_context
    }
    
    try:
        response = requests.post(BASE_URL, json=payload, timeout=30)
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print(f"\n🤖 AI Response:")
                print(f"{'-' * 80}")
                print(data.get('answer', 'No answer'))
                print(f"{'-' * 80}")
            else:
                print(f"\n❌ Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ HTTP Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
    
    print()

print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80)

# Test error handling
print("\n\n" + "=" * 80)
print("ERROR HANDLING TESTS")
print("=" * 80)

error_tests = [
    {
        "title": "Missing Question",
        "payload": {"prediction_context": prediction_context}
    },
    {
        "title": "Missing Context",
        "payload": {"question": "What should I do?"}
    },
    {
        "title": "Empty Question",
        "payload": {"question": "", "prediction_context": prediction_context}
    }
]

for test in error_tests:
    print(f"\n{'─' * 80}")
    print(f"🧪 ERROR TEST: {test['title']}")
    print(f"{'─' * 80}")
    
    try:
        response = requests.post(BASE_URL, json=test['payload'], timeout=10)
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Success: {data.get('success', False)}")
        if not data.get('success'):
            print(f"Error Message: {data.get('error', 'No error message')}")
            
    except Exception as e:
        print(f"Exception: {e}")

print("\n" + "=" * 80)
