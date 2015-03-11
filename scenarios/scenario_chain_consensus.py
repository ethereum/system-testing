import random
import time
import pytest
from base import Inventory
from clients import start_clients, stop_clients
from eshelper import consensus, log_scenario

state_durations = dict(stopped=(1, 10), running=(10, 30))
test_time = 60
max_time_to_reach_consensus = 10
random.seed(42)
num_scheduled_clients = 2

def log_event(event, **kwargs):
    log_scenario(name='chain_consensus', event=event, **kwargs)


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

@pytest.fixture(scope='module', autouse=True)
def run(run_clients):
    """Run the clients.
    
    Because of ``autouse=True`` this method is executed before everything else
    in this module.

    The `run_clients` fixture is defined in ``conftest.py``. It is true by
    default but false if the --norun command line flag is set.
    """
    log_event('started')
    if not run_clients:
        return

    inventory = Inventory()
    clients = inventory.clients

    # create schedule
    events = []
    for c in list(clients)[:num_scheduled_clients]:
        events.extend(mkschedule(c))
    events = sorted(events, key=lambda x: x['time'])
    assert len(events)
    print '\n'.join(repr(e) for e in events)

    # FIXME, reset client storage
    # use client-reset.yml playbook, needs to set docker_container_id in inventory

    # start-up all clients
    log_event('start_all_clients')
    start_clients(clients=clients)
    log_event('start_all_clients.done')

    # run events
    log_event('run_churn_schedule')
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
    log_event('run_churn_schedule.done')

    # start all clients
    log_event('start_all_clients_again')
    start_clients(clients=clients)
    log_event('start_all_clients_again.done')

    # let them agree on a block
    log_event('wait_for_consensus')
    time.sleep(max_time_to_reach_consensus)
    log_event('wait_for_consensus.done')


@pytest.fixture(scope='module')
def client_count():
    """py.test passes this fixture to every test function expecting an argument
    called ``client_count``.
    """
    inventory = Inventory()
    return len(inventory.clients)


def test_consensus(client_count):
    num_agreeing_clients = consensus(offset=max_time_to_reach_consensus)
    print '%d out of %d clients are on the same chain' % (num_agreeing_clients,
                                                          client_count)
    assert num_agreeing_clients == client_count


def test_consensus_only():
    inventory = Inventory()
    clients = inventory.clients
    return test_consensus(len(clients))
