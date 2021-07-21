from pprint import pprint
import pynetbox
import requests
import json
import urllib3


# r=requests.get("http://www.example.com/", headers={"content-type":"text"})

def getToken(a10URL, a10User, a10Pass):
    # VERY basic input validation
    if a10URL[-1] == "/":
        authURL = a10URL+"axapi/v3/auth"
    else:
        authURL = a10URL+"/axapi/v3/auth"

    authHeaders = {
        "content-type": "application/json",
        'Connection': "close",
        "User-Agent": "Mark's API thing (python Requests)"
    }
    # Create request body to send username/pass
    authBody = {
        "credentials": {
            "username": a10User,
            "password": a10Pass
        }
    }
    # Since we're playing with a lab box with a self signed cert, this disables an annoying warning.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Send the request
    try:
        authResp = requests.post(
            authURL, headers=authHeaders, json=authBody, verify=False)
    except Exception as e:
        return "", e

    # Handle cases where response is not 200 so we don't try to json an error message
    if authResp.status_code != 200:
        return "", str(authResp.status_code)+"\n"+authResp.text
    else:
        jsonResp = json.loads(authResp.text)

    # Extract token from body of page
    return jsonResp["authresponse"]["signature"], ""


def getServers(a10URL, authToken):
    # VERY basic input validation
    if a10URL[-1] == "/":
        authURL = a10URL+"axapi/v3/slb/server-list"
    else:
        authURL = a10URL+"/axapi/v3/slb/server-list"

    authHeaders = {
        "content-type": "application/json",
        'Connection': "close",
        "User-Agent": "Mark's API thing (python Requests)",
        "Authorization": "A10 " + authToken
    }

    # Send the request
    try:
        authResp = requests.get(
            authURL, headers=authHeaders, verify=False)
    except Exception as e:
        return "", e

    # Handle cases where response is not 200 so we don't try to json an error message
    if authResp.status_code != 200:
        return "", str(authResp.status_code)+"\n"+authResp.text
    else:
        jsonResp = json.loads(authResp.text)

    # Extract token from body of page

    for i in jsonResp["server-list"]:
        print("%s : %s" % (i["name"], i["host"]))
        for p in i["port-list"]:
            print("\tPort: %d/%s\n" %
                  (p["port-number"], p["protocol"]))

    return "something"


def getNetboxIP(netboxURL, netboxAuth):

    lbPrefix = "172.16.0.0/24"
    nbPull = pynetbox.api(url=netboxURL, token=netboxAuth)
    nbIPList = nbPull.ipam.ip_addresses.filter(address="172.16.0")

    # print(type(allPrefix))

    fmt = "{:<20}|{:<5}{:<50}"
    fmtHeader = ("IP", " ", "Description")

    print(fmt.format(*fmtHeader))
    print("======================================")
    for i in nbIPList:
        print(
            fmt.format(
                i.display,
                "",
                i.description
            )
        )


if __name__ == "__main__":
    print("funcs.py cannot be run directly")
    quit()
