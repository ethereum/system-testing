#!/usr/bin/env python
import webbrowser
from base import Inventory
url = 'http://%s/' % Inventory().es
webbrowser.open(url)
