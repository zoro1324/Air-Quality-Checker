"""
Test script for the generate_report API endpoint.
Run this after starting the Django server.

Usage:
    python test_generate_report.py
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/generate-report/"

# Sample request data
sample_data = {
    "categories": [
        {
            "category": "Agriculture Consultation",
            "parameters": ["PM2.5", "PM10", "O3", "NO2"],
            "values": {
                "PM2.5": 35.5,
                "PM10": 78.2,
                "O3": 45.1,
                "NO2": 22.3
            },
            "aqi": 85,
            "location": "Chennai, IN"
        },
        {
            "category": "Health Advisory",
            "parameters": ["PM2.5", "PM10", "O3"],
            "values": {
                "PM2.5": 35.5,
                "PM10": 78.2,
                "O3": 45.1
            },
            "aqi": 85,
            "location": "Chennai, IN"
        },
        {
            "category": "Air Quality Report",
            "parameters": ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"],
            "values": {
                "PM2.5": 35.5,
                "PM10": 78.2,
                "O3": 45.1,
                "NO2": 22.3,
                "SO2": 8.5,
                "CO": 450.0
            },
            "aqi": 85,
            "location": "Chennai, IN"
        },
        {
            "category": "Emergency Services",
            "parameters": ["PM2.5", "PM10"],
            "values": {
                "PM2.5": 35.5,
                "PM10": 78.2
            },
            "aqi": 85,
            "location": "Chennai, IN"
        }
    ]
}

def test_generate_report():
    """Test the generate_report endpoint"""
    print("=" * 80)
    print("Testing Generate Report API")
    print("=" * 80)
    print(f"\nEndpoint: {ENDPOINT}")
    print(f"\nRequest Data:")
    print(json.dumps(sample_data, indent=2))
    print("\n" + "-" * 80)
    
    try:
        # Make POST request
        response = requests.post(
            ENDPOINT,
            json=sample_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        print("-" * 80)
        
        # Parse response
        response_data = response.json()
        print(f"\nResponse Data:")
        print(json.dumps(response_data, indent=2))
        
        # Check if successful
        if response.status_code == 200 and response_data.get("success"):
            print("\n" + "=" * 80)
            print("✅ SUCCESS! Generated Summaries:")
            print("=" * 80)
            
            for category, summary in response_data.get("summaries", {}).items():
                print(f"\n📊 {category}:")
                print("-" * 80)
                print(summary)
                print()
        else:
            print("\n" + "=" * 80)
            print("❌ ERROR!")
            print("=" * 80)
            print(f"Error: {response_data.get('error', 'Unknown error')}")
            if 'details' in response_data:
                print(f"Details: {json.dumps(response_data['details'], indent=2)}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the server.")
        print("Make sure the Django server is running on http://localhost:8000")
        print("Run: python manage.py runserver")
    
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_generate_report()
