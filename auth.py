import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def confirm_status():
    base = "https://localhost:5050/v1/api/"
    end = "iserver/auth/status"

    auth_req = requests.post(url=base+end, verify=False)
    print(auth_req)
    print(auth_req.text)



if __name__ == "__main__":
    confirm_status()