"""
Test script to verify the prediction endpoint returns AI summary
"""
import requests
from datetime import datetime, timedelta

# API endpoint
BASE_URL = "http://localhost:8000/api/aqi/predict"

# Calculate time range (last 24 hours)
end_time = datetime.now()
start_time = end_time - timedelta(hours=24)

# Convert to Unix timestamps
start_ts = int(start_time.timestamp())
end_ts = int(end_time.timestamp())

# Test parameters
params = {
    'start': start_ts,
    'end': end_ts,
    'generate_summary': 'true',
    'lat': 13.0827,
    'lon': 80.2707
}

print(f"Testing prediction endpoint with summary generation...")
print(f"URL: {BASE_URL}")
print(f"Params: {params}")
print(f"\nTime range: {start_time} to {end_time}")
print("-" * 80)

try:
    response = requests.get(BASE_URL, params=params, timeout=30)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\nResponse keys: {data.keys()}")
        print(f"Results count: {data.get('count', 0)}")
        print(f"Model loaded: {data.get('model', {}).get('loaded', False)}")
        
        if 'ai_summary' in data:
            print("\n✅ AI Summary Present!")
            ai_summary = data['ai_summary']
            
            if 'error' in ai_summary:
                print(f"❌ Summary Generation Error: {ai_summary['error']}")
            else:
                print(f"\nPeriod: {ai_summary.get('period', 'N/A')}")
                print(f"Average Predicted AQI: {ai_summary.get('avg_predicted_aqi', 'N/A')}")
                print(f"\nSummary Text:")
                print(ai_summary.get('summary', 'N/A'))
                
                if 'avg_pollutants' in ai_summary:
                    print(f"\nAverage Pollutants:")
                    for pollutant, value in ai_summary['avg_pollutants'].items():
                        print(f"  {pollutant}: {value:.2f}")
        else:
            print("\n❌ No AI Summary in response!")
            print("\nFull response:")
            import json
            print(json.dumps(data, indent=2)[:1000])
    else:
        print(f"\n❌ Error response:")
        print(response.text)
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ Request failed: {e}")
    print("\nMake sure the Django server is running on http://localhost:8000")

print("\n" + "=" * 80)
