"""
random notes:
ansible --overwrite
http://docs.ansible.com/developing_inventory.html
http://docs.ansible.com/playbooks_variables.html#passing-variables-on-the-command-line
"""
from base import Inventory
import nodeid_tool
import json

inventory = Inventory()

conf = dict(mining_cpu_percentage=50,
            bootstrap_ip=inventory.boot,
            port=30303,
            req_num_peers=4)

docker_run_args = '--logging :debug --log_json 1 --remote {bootstrap_ip} --port 30303 ' \
                  '--mining {mining_cpu_percentage} --peers {req_num_peers}'
teees_args = '{elarch_ip} guid,{pubkey_hex}'

mining_cpu_percentage = 50
bootstrap_ip = inventory.boot
req_num_peers = 4

client_params = dict()
for client in inventory.clients:
    assert client
    assert inventory.es
    assert inventory.boot
    ext_id = str(client)
    pubkey = nodeid_tool.topub(ext_id)
    d = dict(hosts=inventory.inventory[client], vars=dict())
    dra = docker_run_args.format(bootstrap_ip=bootstrap_ip,
                                 mining_cpu_percentage=mining_cpu_percentage,
                                 req_num_peers=req_num_peers)
    d['vars']['docker_run_args'] = dra
    d['vars']['docker_tee_args'] = teees_args.format(elarch_ip=inventory.es, pubkey_hex=pubkey)
    inventory.inventory[client] = d

print json.dumps(inventory.inventory, indent=4)

"""
1) inventory schreiben
2) ansible-pb -i invent client-run (clients starten)

loop:
  random wait
  docker stop random client (ansible-playbook --extra-args pattern=tag_name
  random wait
  random start stoped client
until tired

start analytics





"""

