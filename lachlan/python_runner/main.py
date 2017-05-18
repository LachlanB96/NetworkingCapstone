"""
A lot of code taken from http://docs.ansible.com/ansible/dev_guide/developing_api.html
and also a bit taken from https://serversforhackers.com/running-ansible-programmatically
"""


from ansible.playbook.play import Play
from ansible.inventory import Inventory
#from callback_skeleton import CallbackModule
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.vars import VariableManager
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.callback import CallbackBase
from ansible import utils

import sys
import jinja2
import json
from tempfile import NamedTemporaryFile
import os
from collections import namedtuple

class ResultCallback(CallbackBase):

    def v2_runner_on_ok(self, result, **kwargs):
        host = result._host
        print json.dumps({host.name: result._result}, indent=4)


# Boilerplace callbacks for stdout/stderr and log output
############################################################
# TO WRITE OWN CALL BACKS, FROM LOCAL CALLBACK_SKELETON.PY #
############################################################
# verbosity = 0
# callback = CallbackModule()
# playbook_cb = callback.PlaybookCallbacks(verbosity)
# stats = callback.AggregateStats()
# runner_cb = callback.PlaybookRunnerCallbacks(stats, verbosity)

# First arg defines running mode
running_mode = sys.argv[1]
print("Currently running in %s mode." % running_mode)


Options = namedtuple('Options', [
    'connection', 
    'module_path', 
    'forks', 
    'become', 
    'become_method', 
    'become_user', 
    'check'
    ]
)

hosts = [
    '10.0.0.1',
    '10.0.1.2'
    ]

playbooks = [
    './show_clock.yml'
    ]



variable_manager = VariableManager()
loader = DataLoader()
options = Options(
    connection='local', 
    module_path='.', 
    forks=100, 
    become=None, 
    become_method=None, 
    become_user=None, 
    check=False)
passwords = dict(vault_pass='secret')
results_callback = ResultCallback()



inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=hosts)
variable_manager.set_inventory(inventory)



# Dynamic Inventory
####################################################################
# DIFFERENT WAY TO HAVE SCRIPT STORE INVENTORY, GOOD FOR DEBUGGING #
####################################################################

# inventory = """
# [ios_device]
# {{ ip_address }}
# """

# inventory_template = jinja2.Template(inventory)
# rendered_inventory = inventory_template.render({
#     'ip_address': '10.0.0.1'
# })

# # Create a temporary file and write the template string to it
# hosts = NamedTemporaryFile(delete=False)
# hosts.write(rendered_inventory)
# hosts.close()

if running_mode == "inbuilt" or running_mode == "managed":
    play_source =  dict(
        name = "Ansible Play",
        hosts = hosts,
        gather_facts = 'no',
        tasks = [
            #dict(action=dict(module='shell', args='ls'), register='shell_out'),
            #dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
            dict(action=dict(module='shell', args='show clock'))
         ]
    )

    pb = Play().load(play_source, variable_manager=variable_manager, loader=loader)

if running_mode == "managed":
    tqm = None
    try:
        tqm = TaskQueueManager(
                  inventory=inventory,
                  variable_manager=variable_manager,
                  loader=loader,
                  options=options,
                  passwords=passwords,
                  stdout_callback=results_callback,
              )
        result = tqm.run(pb)
        print result
    finally:
        if tqm is not None:
            tqm.cleanup()
            print("Cleaning up")
        print("EOF")
else:
    print("ERROR: Specify managed or inbuilt running method in args 'python run.py inbuilt'")

