from base import Inventory
from clients import start_clients, stop_clients
from eshelper import consensus, log_scenario, check_connection
import random
import time
import sys

state_durations = dict(stopped=(1, 10), running=(10, 30))
test_time = 60
max_time_to_reach_consensus = 10
random.seed(42)
num_scheduled_clients=1
impls = ['go']
# 0 is go, 1 is cpp
boot = 0

def mkschedule(client):
    state = 'running'
    elapsed = random.randrange(*state_durations[state])  # let it run a bit
    events = []
    while elapsed < test_time:
        state = 'stopped' if state is 'running' else 'running'
        duration = random.randrange(*state_durations[state])
        if elapsed + duration < test_time:
            events.append(dict(state=state, time=elapsed, client=client))
            elapsed += duration
        else:
            break
    return events


def scenario(num_scheduled_clients=num_scheduled_clients):
    """
    starts all clients
    stops, restarts clients in a random pattern
    starts all clients
    waits a bit
    checks for consensus

    @return: bool(consensous of all)
    """
    inventory = Inventory()
    clients = inventory.clients

    log_scenario(name='chain_consensus', event='started')

    # create schedule
    events = []
    for c in list(clients)[:num_scheduled_clients]:
        events.extend(mkschedule(c))
    events = sorted(events, key=lambda x: x['time'])
    assert len(events)
    print '\n'.join(repr(e) for e in events)

    # reset client storage
    # use client-reset.yml playbook

    # start-up all clients
    log_scenario(name='p2p_connect', event='start_all_clients')
    start_clients(clients=clients, impls=impls, boot=boot)
    log_scenario(name='p2p_connect', event='start_all_clients.done')

    # run events
    log_scenario(name='p2p_connect', event='run_churn_schedule')
    elapsed = 0
    while events:
        e = events.pop(0)
        # sleep until time has come
        if elapsed < e['time']:
            time.sleep(e['time'] - elapsed)
            elapsed = e['time']
        cmd = dict(running=start_clients, stopped=stop_clients)[e['state']]
        client = e['client']
        print elapsed, cmd.__name__, client
        cmd(clients=[client], impls=impls, boot=boot)
    log_scenario(name='p2p_connect', event='run_churn_schedule.done')

    # start all clients
    log_scenario(name='p2p_connect', event='start_all_clients_again')
    start_clients(clients=clients, impls=impls, boot=boot)
    log_scenario(name='p2p_connect', event='start_all_clients_again.done')

    # let them agree on a block
    log_scenario(name='p2p_connect', event='wait_for_consensus')
    time.sleep(max_time_to_reach_consensus)
    log_scenario(name='p2p_connect', event='wait_for_consensus.done')
    return check_consensus(clients)


def check_consensus(clients):
    check_connection(minconnected=len(clients))
    num_agreeing_clients = consensus(offset=max_time_to_reach_consensus)
    print '%d out of %d clients are on the same chain' % (num_agreeing_clients, len(clients))
    return num_agreeing_clients == len(clients)


def check_consensus_only():
    inventory = Inventory()
    clients = inventory.clients
    return check_consensus(clients)

if __name__ == '__main__':
    # success = check_consensus_only()
    success = scenario()
    if not success:
        sys.exit(1)
