
# CMDB Remedy Inventory For Ansible Automation Platform

## Input 

> **REMEDY_INSTANCE**: https://remedy_server_here.edc.ds1.usda.gov:8118 
>
> Use this to define what host (such as CMDB preprod or prod, etc) to connect to 

> **REMEDY_USERNAME**: {{ remedy_username }}
>
> Use this to pass the username for the CMDB instance you're connecting to

>**REMEDY_PASSWORD**: {{ remedy_password }}
>
> Use this to pass the password for the CMDB instance you're connecting to 

>**REMEDY_GROUPS**:  "AssetLifecycleStatus,RebootLevel, etc etc etc "
>
> Use this to ***override*** the default groups which get created at execution

>**REMEDY_HOSTVARS**: "AssetLifecycleStatus,RebootLevel, etc etc etc "
>
> Use this to ***override*** the default hostvars which get created at execution

>**REMEDY_OS**: Windows
>
> Use this to retrieve only a specific operating system from CMDB


## Defaults

    "groups": [
        "RebootLevel",
        "Project Number",
        "Project Code",
        "System Environment",
        "Expansion",
        "Expansion Interface",
        "AssetLifecycleStatus",
        "CityName"
    ]

    "host_vars": [
        "Name",
        "Domain",
        "System Role",
        "System Environment",
        "PrimaryIP",
        "RebootLevel",
        "AssetLifecycleStatus",
        "Item",
        "Submitter",
        "Department",
        "CityName"
    ]

    "group_vars": {
        "Windows": { "ansible_connection": "winrm",
                     "ansible_port": 5985,
                     "ansible_winrm_transport": "kerberos",
                     "ansible_winrm_read_timeout_sec": 70,
                     "ansible_winrm_operation_timeout_sec": 60,
                     "ansible_winrm_message_encryption": "auto" },
        "Linux": {},
        "Solaris10": { "ansible_become_exe": "/usr/local/bin/sudo",
                       "ansible_shell_executable": "/bin/bash" },
        "Solaris11": { "ansible_python_interpreter": "/usr/bin/python2" },
        "AIX": {}
    }

## Output
    { 
        "_meta": {
            "hostvars": {} },
            "all": {
                "hosts": {
                    "infrasdb": {
                        "Name": "secretdb",
                        "Domain": "ds.contoso.com",
                        "System Role": "Server (Solaris)",
                        "System Environment": "Development/Sandbox",
                    },
                    ... snip ...
                }
            }
        }
    }
                    