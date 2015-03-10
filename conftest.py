import pytest

def pytest_addoption(parser):
    parser.addoption('--run', action='store_false',
                     help="if flag is set, clients are run")

@pytest.fixture(scope='module')
def run_clients(request):
    return not request.config.getoption('--run')
