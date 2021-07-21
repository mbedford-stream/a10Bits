from funcs import getToken, getServers, getNetboxIP

if __name__ == "__main__":
    # Ideally these would be prompted for but typing during testing is annoying
    a10URL = "https://172.17.0.100/"
    a10User = "apiUser"
    a10Pass = "abc123"

    # Request Token so we can make subsequesnt calls
    authToken, err = getToken(a10URL, a10User, a10Pass)

    # SUPER basic error handling
    if err != "":
        print("There was a problem getting the token:\n%s\n" % err)
    else:
        print("Your token is: %s\n" % authToken)

    #
    # Get list of configured Servers?
    #

    getServers(a10URL, authToken)

    netboxURL = "http://172.17.0.16:8000"
    netboxAuth = "de51613da4b614a5585599a4b7cf080e42c6262c"
    getNetboxIP(netboxURL, netboxAuth)
