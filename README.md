# a10Bits
  
The goal here is to be able to create a load balanced VIP with minimal input from an end user.  We take a list of servers and names and then create an ansible playbook to push that to the ADC.  
  
inputs (addRequest.json):  
{  
    "userName": "apiuser",  
    "passWord": "abc123",  
    "serversList": [  
        {  
            "ip": "10.10.20.228",  
            "name": "web-228",  
            "port": "80"  
        }  
    ],  
    "sgName": "test_SG_automated",  
    "vipName": "test_VIP_automated",  
    "vipProto": "http",  
    "vipPort": "80",  
    "vipPortName": "test_Service_Automated",  
    "lbMethod": "round-robin"  
}  
    
Basic Flow:    
✅    Collect data for creation of new VIP  
✅    Check existing servers on SLB  
✅    Gather next available IP from SLB net  
✅    Check ARP on gateway to confirm IP does not exist on net  
✅    Add IP object to IPAM  
✅    Create playbooks from templates  
✅      If server IPs do not exist, create  
✅      If servers exist then add to new Service Group  
✅      Create SG  
✅      Create VIP  
✅    Get web page and confirm HTTP 200 and some content  
  
=====================================  
