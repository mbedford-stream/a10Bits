from os import truncate
# ALl the supporting functions are in funcs.py and imported
from funcs import getToken, getServers, getNetboxIP, readJSON, checkARP, renderTemplate, validIP, createIP


if __name__ == "__main__":

    newItems, e = readJSON("addRequest.json")
    if e != "":
        print("There was a problem")
        print(e)

    # Test submitted new server IPs to makie sure they're valid IPs and quit if they're not
    ipFail = False
    for i in newItems["serversList"]:
        if validIP(i["ip"]) == False:
            print("%s is not a valid IPv4 address" % i["ip"])
            ipFail = True
    if ipFail:
        quit()

    # Ideally these would be prompted for but typing during testing is annoying
    a10URL = "https://172.17.0.100/"
    a10User = "apiUser"
    a10Pass = "abc123"

    # Request Token so we can make subsequesnt calls to the ADC
    authToken, err = getToken(a10URL, a10User, a10Pass)

    # SUPER basic error handling
    if err != "":
        print("There was a problem getting the token:\n%s\n" % err)
        quit()

    # Pull SLB config section from ADC so we can do things and validate inputs to reduce errors
    slbConfig, e = getServers(a10URL, authToken)
    if e != "":
        print(e)
        quit()

    # Separate ADC config sections to more specific variables for testing later.
    configServersList = slbConfig["slb"]["server-list"]
    configSGList = slbConfig["slb"]["service-group-list"]
    configVIPList = slbConfig["slb"]["virtual-server-list"]

    # Make a handy simple list of IPs used in already configured servers to check our new ones against
    serverIPs = []
    for s in configServersList:
        newServer = {}
        newServer["name"] = s["name"]
        newServer["ip"] = s["host"]
        serverIPs.append(newServer)

    # We liked the handy short list from the server IPs so let's make 2 more to check for existing Service Group and VIP names
    existingSGs = []
    existingVIPs = []
    # Check new item names against already configured to make sure we're not going to run into naming conflicts that will kill the playbook
    matchFail = False
    for sg in configSGList:
        if newItems["sgName"] == sg["name"]:
            print("Service Group name (%s) matches existing config" %
                  newItems["sgName"])
            matchFail = True

    for vip in configVIPList:
        if newItems["vipName"] == vip["name"]:
            print("Virtual Server name (%s) matches existing config" %
                  newItems["vipName"])
            matchFail = True
        for p in vip["port-list"]:
            if newItems["vipPortName"] == p["name"]:
                print("Virtual Server Port name (%s) matches existing config" %
                      newItems["vipPortName"])
                matchFail = True

    # Up to this point we will print any name matches so they can be addressed - this is where we quit so the silly
    # operator can go and fix their names
    if matchFail:
        quit()

    # Check for the same serer between new and existing items and if we find it already on the ADC, just add the existing to the new SG
    for i in newItems["serversList"]:
        for s in serverIPs:
            if "ip" in i:
                if i["ip"] == s["ip"]:
                    i["name"] = s["name"]
                    del i["ip"]

    # Setup basic netbox connectivity stuff
    netboxURL = "http://172.17.0.16:8000"
    netboxAuth = "de51613da4b614a5585599a4b7cf080e42c6262c"

    # Go get an avilable IP and check the ARP table on the DFG to make sure it is not present - just in case netbox wasnt updated.
    freeIPCheck = False
    while freeIPCheck == False:
        nextIP, remainIP, err = getNetboxIP(netboxURL, netboxAuth)
        freeIPCheck = checkARP({"host": "172.31.0.2", "port": 830, "user": "mark",
                               "password": "darkS!de", "interface": "ge-0/0/4"}, nextIP)
    if err != "":
        print("Problem getting available IP\n" + err)
        quit()

    # If new IP is not in ARP table on DFG then move on and do more things
    if freeIPCheck:
        print("IP not found in ARP table")
        print("IP Assigned from Netbox: " + nextIP)
        print("%d IPs left on network" % (remainIP))
        newItems["vipIP"] = nextIP.split("/")[0]
        newItems["vipMask"] = "/32"
        # newItems["vipMask"] = nextIP.split("/")[1]

    # Generate payload for creating a Netbox IP record
    ipData = {"ip": nextIP,
              "name": newItems["vipPortName"], "desc": "Automated ADC deploy"}

    ipSaved, e = createIP(ipData, netboxURL, netboxAuth)

    # Check to make sure the IP creation was successful
    if ipSaved == False:
        print(e)
    else:
        print("Check Netbox for %s" % nextIP)

    # Create playbook from template with all relevant inputs.
    # This could be run as part of the script or sent directly to the ADC API but for now
    # We'll just run the playbook seperately
    #
    # ansible-playbook -i tempWorking/inv tempWorking/playbooks/templateRender.yml
    #
    rednerWorked, e = renderTemplate(
        newItems, "createServer.j2", "templateRender.yml")
    if e != "":
        print("Playbook did not render")
        print(e)

    else:
        print("Playbook rendered successfully")
