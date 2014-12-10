'''
based on
https://github.com/exoscale/python-logstash-formatter
'''
import socket
import datetime
import json

def _default_json_default(obj):
    """
    Coerce everything to strings.
    All objects representing time get output as ISO8601.
    """
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    else:
        return str(obj)

class LogstashFormatter(object):
    """
    A custom formatter to prepare logs to be
    shipped out to logstash.
    """

    def __init__(self, defaults=dict(), source_host=None, json_default=_default_json_default):
        """
        :param defaults:       extra fields available in all logs
        :param source_host: the source host
        :param json_default: Default JSON representation for unknown types,
                             by default coerce everything to a string
        """
        self.defaults = defaults
        self.source_host = source_host
        self.json_default = json_default
        if not source_host:
            try:
                self.source_host = socket.gethostname()
            except:
                self.source_host = ""

    def format(self, fields):
        """
        Format a log record to JSON
        """
        assert 'msg' in fields
        msg = fields.pop('msg')

        logr = self.defaults.copy()

        logr.update({'@message': msg,
                     '@timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                     '@source_host': self.source_host,
                     '@fields': self._build_fields(logr, fields)})

        return json.dumps(logr, default=self.json_default)

    def _build_fields(self, defaults, fields):
        """
        Return provided fields including any in defaults
        """
        return dict(defaults.get('@fields', {}).items() + fields.items())
