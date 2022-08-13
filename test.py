import requests
from requests.auth import HTTPBasicAuth
import json

#config
ADRESS = 'http://127.0.0.1:5000/api/'
ADMIN_ID = 2220000000
ADMIN_PASSWORD_UNHASH = 'Project.4003'
ADMIN_PASSWORD = '7a2bcb91ae39d331dba2c0efb6a0ef56986e0e90e70de36b19c065472333c2e9'
headers = {'Content-type': 'application/json', 'Accept': '*/*'}

#config base data
payload = {'member_name':'Sara Borna', 'member_phone':'+989176963945', 'member_password':ADMIN_PASSWORD_UNHASH, 'member_type':'admin'}
response = requests.post(ADRESS+'admin/signup_admin', data = json.dumps(payload), headers = headers, auth=HTTPBasicAuth(ADMIN_ID, ADMIN_PASSWORD))
payload = {'member_name':'Jadi Mirmirani', 'member_phone':'+989176963945', 'member_password':ADMIN_PASSWORD_UNHASH, 'member_type':'admin'}
response = requests.post(ADRESS+'admin/signup_admin', data = json.dumps(payload), headers = headers, auth=HTTPBasicAuth(ADMIN_ID, ADMIN_PASSWORD))
payload = {'member_name':'Armin Naserian', 'member_phone':'+989176963945', 'member_password':ADMIN_PASSWORD_UNHASH, 'member_type':'operator'}
response = requests.post(ADRESS+'operator/signup', data = json.dumps(payload), headers = headers, auth=HTTPBasicAuth(ADMIN_ID, ADMIN_PASSWORD))
payload = {'member_name':'Amir Vaziri', 'member_phone':'+989176963945', 'member_password':ADMIN_PASSWORD_UNHASH}
response = requests.post(ADRESS+'operator/signup', data = json.dumps(payload), headers = headers, auth=HTTPBasicAuth(1220000004, "7a2bcb91ae39d331dba2c0efb6a0ef56986e0e90e70de36b19c065472333c2e9"))
payload = {'member_name':'Sina Vaziri', 'member_phone':'+989176963945', 'member_password':ADMIN_PASSWORD_UNHASH}
response = requests.post(ADRESS+'operator/signup', data = json.dumps(payload), headers = headers, auth=HTTPBasicAuth(1220000004, "7a2bcb91ae39d331dba2c0efb6a0ef56986e0e90e70de36b19c065472333c2e9"))
payload = {'member_name':'Sana Vaziri', 'member_phone':'+989176963945', 'member_password':ADMIN_PASSWORD_UNHASH}
response = requests.post(ADRESS+'operator/signup', data = json.dumps(payload), headers = headers, auth=HTTPBasicAuth(1220000003, "7a2bcb91ae39d331dba2c0efb6a0ef56986e0e90e70de36b19c065472333c2e9"))

