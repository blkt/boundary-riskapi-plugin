import json
import socket
import sys
import time
import urllib

import logging
log = logging.getLogger(__name__)

HOSTNAME = socket.getfqdn()
POLL_INTERVAL = 1000

BASE_URL = "localhost"
PORT = "5565"
PATH1 = "_metrics"

def encoded_json_field(field):
    splitted = field.split("/")

    def inner(data):
        datum = data
        for step in splitted:
            datum = datum[step]
        return datum

    return inner

class UrlBasedCalculator(object):

    def __init__(self, base_url, port, path1):
        partial_url = "http://%s:%s/%s/" % (base_url, port, path1)
        self.pattern = partial_url + "%s"

    def get_url(self):
        raise NotImplementedError

class gen_identity_func(UrlBasedCalculator):

    def __init__(self, path, field, base_url, port, path1):
        super(gen_identity_func, self).__init__(base_url, port, path1)
        self.path = path
        self.field = field
        self.url = self.pattern % path
        self.extractorf = encoded_json_field(field)

    def __call__(self, data):
        return self.extractorf(data)

    def get_url(self):
        return self.url

class gen_delta_identity_func(UrlBasedCalculator):

    def __init__(self, path, field, base_url, port, path1):
        super(gen_delta_identity_func, self).__init__(base_url, port, path1)
        self.previous_value = 0
        self.path = path
        self.field = field
        self.url = self.pattern % path
        self.extractorf = encoded_json_field(field)

    def __call__(self, data):
        current_value = self.extractorf(data)
        res = current_value - self.previous_value
        self.previous_value = current_value
        return res

    def get_url(self):
        return self.url

def init_metrics(base_url="localhost", port="5565", path1="_metrics"):
    return {"STATPRO_RISKAPI_OVERALL_COMPUTE_ARITHMETIC_MEAN":
            gen_identity_func(path="overall.compute",
                              field="value/arithmetic_mean",
                              base_url=base_url, port=port, path1=path1),
            "STATPRO_RISKAPI_OVERALL_COMPUTE_PERCENTILE_50":
            gen_identity_func(path="overall.compute",
                              field="value/percentile/50",
                              base_url=base_url, port=port, path1=path1),
            "STATPRO_RISKAPI_OVERALL_COMPUTE_PERCENTILE_95":
            gen_identity_func(path="overall.compute",
                              field="value/percentile/95",
                              base_url=base_url, port=port, path1=path1),
            "STATPRO_RISKAPI_OVERALL_ERRORS_COUNT":
            gen_delta_identity_func(path="overall.errors",
                                    field="value/count",
                              base_url=base_url, port=port, path1=path1),
            "STATPRO_RISKAPI_OVERALL_ERRORS_ONE":
            gen_identity_func(path="overall.errors",
                              field="value/one",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_OVERALL_THROUGHPUT_COUNT":
            gen_delta_identity_func(path="overall.throughput",
                              field="value/count",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_OVERALL_THROUGHPUT_ONE":
            gen_identity_func(path="overall.throughput",
                              field="value/one",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_OVERALL_TIME_ARITHMETIC_MEAN":
            gen_identity_func(path="overall.time",
                              field="value/arithmetic_mean",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_OVERALL_TIME_PERCENTILE_50":
            gen_identity_func(path="overall.time",
                              field="value/percentile/50",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_OVERALL_TIME_PERCENTILE_95":
            gen_identity_func(path="overall.time",
                              field="value/percentile/95",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_QUEUE_LENGTH_RAPI":
            gen_identity_func(path="queue-length-rapi",
                              field="value",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_ARITHMETIC_MEAN":
            gen_identity_func(path="request_time-queue-rapi_poller",
                              field="value/arithmetic_mean",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_PERCENTILE_50":
            gen_identity_func(path="request_time-queue-rapi_poller",
                              field="value/percentile/50",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_PERCENTILE_95":
            gen_identity_func(path="request_time-queue-rapi_poller",
                              field="value/percentile/95",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_THROUGHPUT_RAPI_COUNT":
            gen_identity_func(path="throughput-rapi",
                              field="value/count",
                              base_url=base_url, port=port, path1=path1),
           "STATPRO_RISKAPI_THROUGHPUT_RAPI_ONE":
            gen_identity_func(path="throughput-rapi",
                              field="value/one",
                              base_url=base_url, port=port, path1=path1)}

def parse_params():
    """Parses and returns the contents of the plugin's "param.json" file.

    """
    plugin_params = dict()
    try:
        with open("param.json") as f:
            plugin_params = json.load(f)
    except IOError:
        pass
    return plugin_params

def get_metrics_data(metrics):
    """Retrieves the raw data from the Riskapi node reachable at the given
    base_url, via the given port.

    For earch path in paths, it executes an HTTP GET and converts the
    recieved data from JSON to a Python dictionary.

    """
    dicts = dict()
    fails = []
    urls = sorted({m.get_url() for k, m in metrics.iteritems()})

    for url in urls:
        try:
            f = urllib.urlopen(url)
            js = json.load(f)
            dicts[url] = js
        except IOError:
            fails.append(url)

    return (dicts, fails)

def boundarify_metrics(metrics, raw_data):
    """Converts the raw metric trees (dictionaries) into a sequence of
    pairs (metric, measure).

    While traversing, this routine also "boundarifies" the metric
    names, i.e. it substitutes every character that's not alphanumeric
    or underscore into underscore and converts to upper case the
    result.

    """
    (dicts, failures) = raw_data

    if failures:
        for failure in failures:
            log.warn("Failed getting metrics for %s" % failure)

    results = dict()
    for bdry_name, calculator in metrics.iteritems():
        key = calculator.get_url()
        if key in dicts:
            data = dicts[key]
            results.update({bdry_name: calculator(data)})

    return results

def report_metrics(metrics, hostname, timestamp=None):
    """Prints the given metrics (pairs of strings and numbers) to standard
    output appending the hostname and, optionally, the timestamp.

    """
    for metric, measure in metrics:
        msg = "%s %s %s%s" % (metric, measure, hostname, (" %d" % timestamp) if timestamp else "")
        print msg
        sys.stdout.flush()

def keep_looping_p():
    return True

def main():
    """Extracts raw metrics, flattens them, boundarifies their metrics
    name, and writes them to standard output once every
    POLL_INTERVAL milliseconds.

    """
    params = parse_params()
    base_url = params.get("riskapi_base_url", BASE_URL)
    port = params.get("riskapi_port", PORT)
    poll_interval = int(params.get("riskapi_poll_interval", POLL_INTERVAL) / 1000)

    path1 = PATH1
    hostname = HOSTNAME

    metrics = init_metrics(base_url, port, path1)

    while keep_looping_p():
        timestamp = time.time()
        raw_data = get_metrics_data(metrics)
        flatteneds = boundarify_metrics(metrics, raw_data)
        report_metrics(flatteneds.iteritems(), hostname, timestamp=timestamp)
        time.sleep(poll_interval)

if __name__ == '__main__':
    main()
