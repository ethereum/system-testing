import time
import pytest
import random
from testing.testing import Inventory
from testing.clients import start_clients, stop_clients
from logutils.eshelper import consensus, log_scenario  # , assert_connected

impls = ['go']  # enabled implementations, currently not being used
test_time = 90
random.seed(42)
churn_ratio = 0.75
min_consensus_ratio = 0.90
max_time_to_reach_consensus = 15
state_durations = dict(stopped=(10, 15), running=(20, 30))
offset = 30  # buffer value, total runtime gets added to this
# num_scheduled_clients = 2

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

    start = time.time()

    # create schedule
    events = []
    num_clients = len(inventory.clients)
    num_scheduled_clients = int(num_clients * churn_ratio) if num_clients > 4 else num_clients
    for c in list(clients)[:num_scheduled_clients]:
        events.extend(mkschedule(c))
    events = sorted(events, key=lambda x: x['time'])
    assert len(events)
    print '\n'.join(repr(e) for e in events)

    # reset client storage
    # use client-reset.yml playbook

    # start-up all clients
    log_event('start_all_clients')
    start_clients(clients=clients, impls=impls)
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
        cmd(clients=[client], impls=impls)
    log_event('run_churn_schedule.done')

    # start all clients without mining
    log_event('start_all_clients_again')
    start_clients(clients=clients, impls=impls, enable_mining=False)
    log_event('start_all_clients_again.done')

    # let them agree on a block
    log_event('wait_for_consensus')
    time.sleep(max_time_to_reach_consensus)
    log_event('wait_for_consensus.done')

    # stop all clients
    log_event('stop_all_clients')
    stop_clients(clients=clients, impls=impls)
    log_event('stop_all_clients.done')

    global offset
    offset += time.time() - start
    print "Total offset: %s" % offset

@pytest.fixture(scope='module')
def client_count():
    """py.test passes this fixture to every test function expecting an argument
    called ``client_count``.
    """
    inventory = Inventory()
    return len(inventory.clients)

def test_consensus(client_count):
    # assert_connected(minconnected=client_count, minpeers=client_count, offset=test_time * 2)
    num_agreeing_clients = consensus(offset=offset)
    print '%d out of %d clients are on the same chain' % (num_agreeing_clients,
                                                          client_count)
    assert num_agreeing_clients >= int(client_count * min_consensus_ratio)
