#!/usr/bin/python

import json
import os
import requests
from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleParserError

# Default groups and hostvars if env:REMEDY_HOSTVARS and/or env:REMEDY_GROUPS doesn't exist
config_dict = {
    "groups": [
        "RebootLevel",
        "Project Number",
        "Project Code",
        "System Environment",
        "Expansion",
        "Expansion Interface",
        "AssetLifecycleStatus",
        "CityName"
    ],
    "host_vars": [
        "Name",
        "Domain",
        "System Role",
        "System Environment",
        "PrimaryIP",
        "RebootLevel",
        "AssetLifecycleStatus",
        "Item",
        "Department",
        "CityName",
        "DeviceRole",
        "Expansion Interface",
        "Expansion"
    ],
    "group_vars": {
        "Windows": {"ansible_connection": "winrm",
                    "ansible_port": 5985,
                    "ansible_winrm_transport": "kerberos",
                    "ansible_winrm_read_timeout_sec": 70,
                    "ansible_winrm_operation_timeout_sec": 60,
                    "ansible_winrm_message_encryption": "auto"},
        "Linux": {},
        "Solaris10": {"ansible_become_exe": "/usr/local/bin/sudo",
                      "ansible_shell_executable": "/bin/bash"},
        "Solaris11": {"ansible_python_interpreter": "/usr/bin/python2"},
        "AIX": {}
    }
}


# Empty inventory view.
class Inventory(object):
    def __init__(self):
        self.inventory = {'_meta': {'hostvars': {}},
                          'all': {'hosts': [], 'vars': {}, 'children': []}}

    def add_group(self, group_name):
        if group_name in self.inventory:
            return
        self.inventory[group_name] = {'hosts': [], 'vars': {}, 'children': []}
        if group_name in config_dict['group_vars']:
            self.inventory[group_name]['vars'] = config_dict['group_vars'][group_name]

    def add_host(self, host_name):
        self.inventory['all']['hosts'].append(host_name)

    def add_child(self, parent, child):
        self.inventory[parent]['children'].append(child)

    def add_host_to_group(self, group_name, host_name):
        self.inventory[group_name]['hosts'].append(host_name)

    def set_variable(self, host_name, host_var_key, host_var_value):
        if host_name not in self.inventory['_meta']['hostvars']:
            self.inventory['_meta']['hostvars'][host_name] = {}
        self.inventory['_meta']['hostvars'][host_name][host_var_key] = host_var_value

    def __str__(self):
        return json.dumps(self.inventory)


class RemedyConnection(object):
    def __init__(self):
        self.remedy_hostname = os.environ['REMEDY_INSTANCE']
        self.remedy_username = os.environ['REMEDY_USERNAME']
        self.remedy_password = os.environ['REMEDY_PASSWORD']
        self.protocol = "https"
        self.token = self.get_cmdb_token()
        if self.token is False:
            raise AnsibleParserError("Failed to Connect to Remedy Server: {0}"
                                     .format(AnsibleParserError.message))
        self.header = {'Authorization': 'AR-JWT ' + self.token}
        self.remedy_response = None
        try:
            self.config = config_dict  # array
            if ('REMEDY_GROUPS' in os.environ) and os.environ['REMEDY_GROUPS']:
                self.config['groups'] = [group_i.strip() for group_i in os.environ['REMEDY_GROUPS'].split(',')]
            if ('REMEDY_HOSTVARS' in os.environ) and os.environ['REMEDY_HOSTVARS']:
                self.config['host_vars'] = [group_i.strip() for group_i in os.environ['REMEDY_HOSTVARS'].split(',')]
            if 'Name' not in self.config['host_vars']:
                self.config['host_vars'].append('Name')
        except OSError:
            raise AnsibleParserError("unable to read ENV variables: {0}".format(OSError.strerror))

    def get_cmdb_token(self):
        url = self.protocol + '://' + self.remedy_hostname + '/api/jwt/login'
        payload = {'username': self.remedy_username, 'password': self.remedy_password}
        auth_header = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(url=url, data=payload, headers=auth_header, verify=False)
        if response.status_code != 200:
            return False
        return response.text

    def dispose_cmdb_token(self):
        url = self.protocol + '://' + self.remedy_hostname + '/api/jwt/logout'
        requests.post(url=url, headers=self.header, verify=False)
        return

    def __del__(self):
        self.dispose_cmdb_token()

    def get_cmdb_data(self):
        get_values = set(self.config['host_vars'] + self.config['groups'])
        url = self.protocol + '://' + self.remedy_hostname + "/api/arsys/v1.0/entry/AST:ComputerSystem" \
                                                             "?fields=values(" + ",".join(get_values) + ")"

        # print(url)
        if ('REMEDY_OS' in os.environ) and os.environ['REMEDY_OS']:
            query = "'Item' = \"Server\" AND 'Expansion' LIKE \"%" + os.environ['REMEDY_OS']
        else:
            query = "'Item' = \"Server\""
        # print(query)
        search_params = {'q': query}
        # Using a modified version of the URL + Fields restriction to pull data
        self.remedy_response = requests.get(url=url, headers=self.header, params=search_params, verify=False)
        # print(self.remedy_response.status_code)
        return self.remedy_response.json()


try:
    remedy_connection = RemedyConnection()
except ConnectionError:
    raise AnsibleConnectionFailure(ConnectionError.strerror)

inventory = Inventory()
raw_cmdb_data = remedy_connection.get_cmdb_data()
# loop through each "server" we got back from Remedy
for entry in raw_cmdb_data['entries']:
    # The CMDB Response is a single Dict of 'values': { all the datas } so just store that as a single var
    server = entry['values']
    inventory.add_host(server['Name'])  # Add the host to the base Ansible Inventory
    for group in remedy_connection.config['groups']:
        if server[group] is None:
            continue
        inventory.add_group(server[group])
        inventory.add_host_to_group(server[group], server['Name'])
    for host_var in remedy_connection.config['host_vars']:
        inventory.set_variable(server['Name'],          # sets host_var like IP:10.10.10.10
                               host_var,                # host_var == IP
                               server[host_var])        # server[host_var] == 10.10.10.10

print(inventory)
