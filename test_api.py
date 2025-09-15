import requests

try:
    response = requests.get('http://localhost:8000/api/cancellations?has_cancellation=true')
    print('Status:', response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print('Total cancellations:', len(data['data']))
        print('First few programs:')
        for i, p in enumerate(data['data'][:5]):
            print(f'{i+1}. {p["program"]} (ID: {p["program_id"]}) - {p["class_cancellation"]}')
    else:
        print('Error:', response.text)
        
except Exception as e:
    print('Error:', e)
