import pytest

def pytest_addoption(parser):
    parser.addoption('--norun', action='store_false',
                     help="if flag is set, clients are not run")

@pytest.fixture(scope='module')
def run_clients(request):
    return request.config.getoption('--norun')
