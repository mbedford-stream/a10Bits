from funcs import readHTTP

# Get the page and print an error if not HTTP 200
addCheck, e = readHTTP("http://172.16.0.198")
if e != "":
    print(e)
else:
    print("Retrieved page successfully")
