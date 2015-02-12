from base import Inventory
from clients import start_clients, stop_clients
from eshelper import consensus
import random
import time
import sys

state_durations = dict(stopped=(1, 20), running=(5, 30))
test_time = 60
max_time_to_reach_consensus = 10
random.seed(42)


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


def scenario():
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

    # create schedule
    events = []
    for c in clients:
        events.extend(mkschedule(c))
    events = sorted(events, key=lambda x: x['time'])

    # FIXME, reset client storage
    # use client-reset.yml playbook, needs to set docker_container_id in inventory

    # start-up all clients
    start_clients(clients=clients)

    # run events
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
        cmd(clients=[client])

    # start all clients
    start_clients(clients=clients)

    # let them agree on a block
    time.sleep(max_time_to_reach_consensus)
    num_agreeing_clients = consensus(offset=max_time_to_reach_consensus)
    print '%d out of %d clients are on the same chain' % (num_agreeing_clients, len(clients))
    return num_agreeing_clients == len(clients)


if __name__ == '__main__':
    success = scenario()
    if not success:
        sys.exit(1)
