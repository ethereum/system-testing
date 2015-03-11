import pytest

def pytest_addoption(parser):
    # called by pytest to add command line options
    parser.addoption('--norun', action='store_false',
                     help="if flag is set clients are not run")

@pytest.fixture(scope='module')
def run_clients(request):
    """Fixture for the --norun command line option (false if --norun is set,
    true otherwise).
    """
    return request.config.getoption('--norun')
