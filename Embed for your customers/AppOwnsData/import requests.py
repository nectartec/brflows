import requests

# Workspace Id in which the report is present
workspace_id = '017CDE99-646A-4FD2-8C54-17E2E33A8BC9'

# Report Id for which Embed token needs to be generated
report_id = '1a8338f0-8a78-4d27-be71-82a121a784cc'

# Id of the Azure tenant in which AAD app and Power BI report is hosted. Required only for ServicePrincipal authentication mode.
tenant_id = '71029506-45c7-4577-b71e-19beb180170f'

# Client Id (Application Id) of the AAD app
client_id = 'ec07d040-09ee-48e6-8604-3c23787e27cf'

access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6ImltaTBZMnowZFlLeEJ0dEFxS19UdDVoWUJUayIsImtpZCI6ImltaTBZMnowZFlLeEJ0dEFxS19UdDVoWUJUayJ9.eyJhdWQiOiJodHRwczovL2FuYWx5c2lzLndpbmRvd3MubmV0L3Bvd2VyYmkvYXBpIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvNzEwMjk1MDYtNDVjNy00NTc3LWI3MWUtMTliZWIxODAxNzBmLyIsImlhdCI6MTc0MDQzMzE5MiwibmJmIjoxNzQwNDMzMTkyLCJleHAiOjE3NDA0MzcwOTIsImFpbyI6ImsyUmdZT0QrWVJwWnVLZEFWVWZnN0paMko5RzlBQT09IiwiYXBwaWQiOiJlYzA3ZDA0MC0wOWVlLTQ4ZTYtODYwNC0zYzIzNzg3ZTI3Y2YiLCJhcHBpZGFjciI6IjEiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC83MTAyOTUwNi00NWM3LTQ1NzctYjcxZS0xOWJlYjE4MDE3MGYvIiwiaWR0eXAiOiJhcHAiLCJvaWQiOiJjOGM2YjgyMC00MDc1LTRhYjUtYjU3Yi02NGY0MTE4NTQzNWQiLCJyaCI6IjEuQVVZQUJwVUNjY2RGZDBXM0hobS1zWUFYRHdrQUFBQUFBQUFBd0FBQUFBQUFBQUNBQUFCR0FBLiIsInN1YiI6ImM4YzZiODIwLTQwNzUtNGFiNS1iNTdiLTY0ZjQxMTg1NDM1ZCIsInRpZCI6IjcxMDI5NTA2LTQ1YzctNDU3Ny1iNzFlLTE5YmViMTgwMTcwZiIsInV0aSI6IlJIY0FBZVh6eWttUDktSFpOTDlGQUEiLCJ2ZXIiOiIxLjAiLCJ4bXNfaWRyZWwiOiIyMiA3In0.JY8DrvZKqOMjQngu7eBb1tHyBkgMuU6utThFLgEPw7ReHVKdqXFnu7_N4cBwEv0PsC_uQraRweN2xSDlul58yRxgK_CjsWz8Ez2Zp4ysX3nUaYKa0bkRlLKxoFy1mawRqiyzruhBc9mtFm3Yyf_vtPyyZrVsePW3xJ5n1p_Os9kh_JMb4Fe1oaHzUjQysDOrbOJRN_K4QURSDthMG2s92mV14OS5gBr86CldlzRiHE_XGwqkM-u_BuQ0pM1LU8PDFHavmQKxJyQJC8Ou9MhJ10XdHRXxV-LdoMNcRG_zw-ZuBByNa5qBQL_kRbQE8-Rb5WghdoWdDHA93NpWDeHgTA'

url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/GenerateToken"
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
data = {"accessLevel": "View"}

response = requests.post(url, headers=headers, json=data)
 
print("aqui:", response.text)

if response.status_code != 200:
    print("Erro ao obter Embed Token:", response.text)
