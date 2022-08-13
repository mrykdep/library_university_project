import requests
import json

#config
ADRESS = 'http://127.0.0.1:5000/api/'
ADMIN_ID = 2220000000
ADMIN_PASSWORD = '7a2bcb91ae39d331dba2c0efb6a0ef56986e0e90e70de36b19c065472333c2e9'
headers = {'Content-type': 'application/json', 'Accept': '*/*'}
#auth=HTTPBasicAuth('username', 'password')

payload = {'member_id':ADMIN_ID, 'member_password':ADMIN_PASSWORD}
response = requests.post(ADRESS+'login', data = json.dumps(payload), headers = headers)
print(response.text)