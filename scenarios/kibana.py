#!/usr/bin/env python
import webbrowser
from base import Inventory
url = 'http://%s/index.html#/dashboard/file/guided.json' % Inventory().es
webbrowser.open(url)
