import pytest

def pytest_addoption(parser):
    # called by pytest to add command line options
    parser.addoption('--norun', action='store_false',
                     help="Do not start clients as they're already running")
    parser.addoption('--testnet', action='store_true',
                     help="Use live testnet for test run")

@pytest.fixture(scope='module')
def run_clients(request):
    """
    Fixture for the --norun command line option (false if --norun is set,
    true otherwise).
    """
    return request.config.getoption('--norun')

@pytest.fixture(scope='module')
def on_testnet(request):
    """
    Fixture for the --testnet command line option (true if --testnet is set,
    false otherwise).
    """
    return request.config.getoption('--testnet')
