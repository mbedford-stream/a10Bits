import requests
import json
import urllib3
import random
import ipaddress
from jnpr.junos import Device
from jnpr.junos.op.arp import ArpTable
from jinja2 import Template, Environment, FileSystemLoader


def getToken(a10URL, a10User, a10Pass):
    # A10 API requires an auth token so we go and get that to use for subsequent requests.
    # VERY basic input validation for URL formatting
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
    # Go and get the current SLB config from the ADC so we can perform validation against it
    if a10URL[-1] == "/":
        authURL = a10URL+"axapi/v3/slb/"
    else:
        authURL = a10URL+"/axapi/v3/slb/"

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

    # This part will print all existing servers and the ports configured on the ADC
    # for i in jsonResp["slb"]["server-list"]:
    #     print("%s : %s" % (i["name"], i["host"]))
    #     if "port-list" in i:
    #         for p in i["port-list"]:
    #             print("\tPort: %d/%s\n" %
    #                   (p["port-number"], p["protocol"]))

    return jsonResp, ""


def getNetboxIP(netboxURL, netboxAuth):
    # Request a list of available IPs on the VIP network from Netbox and return some stuff
    authHeaders = {
        "content-type": "application/json",
        'Connection': "close",
        "User-Agent": "Mark's API thing (python Requests)",
        "Authorization": "TOKEN " + netboxAuth
    }

    # Netbox has about 4 IPs on this network so I'm not worried about stressing anything
    # but thhis call could be adjusted to be a bit easier on Netbox
    netQueryURL = netboxURL + "/api/ipam/prefixes/4/available-ips/?limit=1000"

    # Send the request
    try:
        authResp = requests.get(
            netQueryURL, headers=authHeaders, verify=False)
    except Exception as e:
        return "", 0,  e

    # Handle cases where response is not 200 so we don't try to json an error message
    if authResp.status_code != 200:
        print(authResp.status_code, authResp.text)
        return "", 0, str(authResp.status_code)+"\n"+authResp.text
    else:
        jsonResp = json.loads(authResp.text)

    # Return the a random IP address from the list of available values
    # just because we can.
    # We also return the total number of available IPs on the subnet.... because we can
    return jsonResp[random.randrange(0, len(jsonResp))]["address"], len(jsonResp)-1,  ""


def createIP(newEntry, netboxURL, netboxAuth):
    # Create new IP object on Netbox with bare minimum information stuff
    authHeaders = {
        "content-type": "application/json",
        'Connection': "close",
        "User-Agent": "Mark's API thing (python Requests)",
        "Authorization": "TOKEN " + netboxAuth
    }

    netQueryURL = netboxURL + "/api/ipam/ip-addresses/"
    # Here we define the bare minimum informational stuff to attach to the IP
    # Easily updatable since we're passing a dict and just applying those values to the correct field
    createBody = json.dumps({
        "address": newEntry["ip"],
        "description": newEntry["desc"],
        "dns_name": newEntry["name"]
    })

    # Send the request
    try:
        httpResp = requests.post(
            netQueryURL, headers=authHeaders, data=createBody, verify=False)
    except Exception as e:
        return False, e

    # Handle cases where response is not 200 so we don't try to json an error message
    # If everyone is happy, just return True and assume all went well.
    if httpResp.status_code != 200:
        print(httpResp.status_code, httpResp.text)
        return False, str(httpResp.status_code)+"\n"+httpResp.text
    else:
        return True, ""


def readJSON(jsonFile):
    # Probably doesn't even need to be a function but we read the JSON file and return the contents
    returnDict = {}

    try:
        f = open(jsonFile)
    except Exception as e:
        return returnDict, e

    jsonContent = json.loads(f.read())

    f.close()

    return jsonContent, ""


def checkARP(routerInfo, ipCheck):
    # Because not everyone updates IPAM when they pull a new IP it's not always a reliable source
    # So we account for that by checking the ARP table on the default gateway of the network in question
    # If the passed IP is not in the ARP table we assume it's safe to use.
    rtr = Device(host=routerInfo["host"],
                 port=routerInfo["port"], user=routerInfo["user"], password=routerInfo["password"])
    try:
        rtr.open()
    except Exception as err:
        print('Error: ' + repr(err))

    # Use built-in table from jnpr.junos to pull the ARP table in an easily parsable format.
    arpTable = ArpTable(rtr)
    arpTable.get(interface=routerInfo["interface"])

    arpIPs = []
    # Incredibly inefficient way to look for a match
    for a in arpTable:
        arpIPs.append(a.ip_address)

    if ipCheck in arpIPs:
        return False
    else:
        return True


def renderTemplate(varsDict, templateFile, renderedFile):
    # Render the playbook from a provided jinja2 template.
    env = Environment(loader=FileSystemLoader('tempWorking/templates'))
    template = env.get_template(templateFile)

    templateOutput = template.render(varsDict)

    try:
        with open("tempWorking/playbooks/"+renderedFile, "w") as fileOut:
            fileOut.write(templateOutput)
            fileOut.close()
    except Exception as err:
        return False, err

    return True, ""


def validIP(ipAddress):
    # Is the IP passed a valid IPv4 address?
    # Not that anyone would try to enter a weird string of numbers and pass it off as an IP
    try:
        ipaddress.ip_address(ipAddress)
        return True
    except ValueError:
        return False


def readHTTP(checkURL):
    # SUPER simple test to see if the service is now responding to requests
    # Load the URL we just created and if it returns a 200 status code we're all good
    authHeaders = {
        'Connection': "close",
        "User-Agent": "Mark's API thing (python Requests)",
    }

    # Send the request
    try:
        httpResp = requests.get(
            checkURL, headers=authHeaders, verify=False)
    except Exception as e:
        return "", e

    if httpResp.status_code != 200:
        return "", str(httpResp.status_code)+"\n"+httpResp.text
    else:
        return httpResp.text, ""


if __name__ == "__main__":
    print("funcs.py cannot be run directly")
    quit()
