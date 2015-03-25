import json
import re
import socket
import sys
import time
import urllib

import logging
log = logging.getLogger(__name__)

HOSTNAME = socket.gethostname()
POLL_INTERVAL = 5000

BASE_URL = "localhost"
PORT = "5565"
PATH1 = "_metrics"
PATHS = ["overall.compute", "overall.errors", "overall.throughput",
         "overall.time", "queue-length-rapi", "request_time-queue-rapi",
         "throughput-rapi"]
TO_SEND = ["STATPRO_RISKAPI_OVERALL_COMPUTE_ARITHMETIC_MEAN",
           "STATPRO_RISKAPI_OVERALL_COMPUTE_PERCENTILE_50",
           "STATPRO_RISKAPI_OVERALL_COMPUTE_PERCENTILE_95",
           "STATPRO_RISKAPI_OVERALL_ERRORS_COUNT",
           "STATPRO_RISKAPI_OVERALL_ERRORS_ONE",
           "STATPRO_RISKAPI_OVERALL_THROUGHPUT_COUNT",
           "STATPRO_RISKAPI_OVERALL_THROUGHPUT_ONE",
           "STATPRO_RISKAPI_OVERALL_TIME_ARITHMETIC_MEAN",
           "STATPRO_RISKAPI_OVERALL_TIME_PERCENTILE_50",
           "STATPRO_RISKAPI_OVERALL_TIME_PERCENTILE_95",
           "STATPRO_RISKAPI_QUEUE_LENGTH_RAPI",
           "STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_ARITHMETIC_MEAN",
           "STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_PERCENTILE_50",
           "STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_PERCENTILE_95",
           "STATPRO_RISKAPI_THROUGHPUT_RAPI_COUNT",
           "STATPRO_RISKAPI_THROUGHPUT_RAPI_ONE"]

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

def get_metric_urls(base_url, port, path1, paths):
    """Builds a list of URLs to visit to fetch metrics data.

    """
    urls = []

    for path in paths:
        url = "http://%s:%s/%s/%s" % (base_url, port, path1, path)
        urls.append(url)

    return urls

def boundarify_metric_name(name):
    (raw_name, substs) = re.subn(r"[\.-]", "_", name)
    metric_name = u"STATPRO_RISKAPI_" + raw_name

    return metric_name

def get_metrics(base_url, port, path1, paths):
    """Retrieves the raw data from the Riskapi node reachable at the given
    base_url, via the given port.

    For earch path in paths, it executes an HTTP GET and converts the
    recieved data from JSON to a Python dictionary.

    """
    dicts = []
    fails = []
    urls = get_metric_urls(base_url, port, path1, paths)
    pairs = zip(paths, urls)

    for path, url in pairs:
        try:
            f = urllib.urlopen(url)
            js = json.load(f)
            dicts.append([path, js])
        except IOError:
            fails.append(url)

    return (dicts, fails)

def recursive_flatten_folsom_metric(metric, tree):
    """Flattens the metric (a Python dictionary) attaching the names as it
    visits the tree.

    """
    if isinstance(tree, dict):
        res = []
        for key, subtree in tree.iteritems():
            partial = "_".join([metric, key])
            res.extend(recursive_flatten_folsom_metric(partial, subtree))
        return res
    else:
        return [(metric, tree)]

def flatten_folsom_metric(metric, tree):
    return dict(sorted(recursive_flatten_folsom_metric(metric, tree)))

def boundarify_metrics(metrics_tree):
    """Converts the raw metric trees (dictionaries) into a sequence of
    pairs (metric, measure).

    While traversing, this routine also "boundarifies" the metric
    names, i.e. it substitutes every character that's not alphanumeric
    or underscore into underscore and converts to upper case the
    result.

    """
    (metrics, failures) = metrics_tree

    if failures:
        for failure in failures:
            log.warn("Failed getting metrics for %s" % failure)

    flatteneds = dict()

    for metric in metrics:
        metric_name = boundarify_metric_name(metric[0])
        flatteneds.update(flatten_folsom_metric(metric_name, metric[1]["value"]))

    results = dict()
    for key, val in flatteneds.iteritems():
        bdry_name = key.upper()
        if bdry_name in TO_SEND:
            results.update({bdry_name: val})

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

def do_your_job():
    """Extracts raw metrics, flattens them, boundarifies their metrics
    name, and writes them to standard output once every
    POLL_INTERVAL milliseconds.

    """
    params = parse_params()
    base_url = params.get("riskapi_base_url", BASE_URL)
    port = params.get("riskapi_port", PORT)
    poll_interval = int(params.get("riskapi_poll_interval", POLL_INTERVAL) / 1000)

    path1 = PATH1
    paths = PATHS
    hostname = HOSTNAME

    while keep_looping_p():
        timestamp = time.time()
        raw_metrics = get_metrics(base_url, port, path1, paths)
        flatteneds = boundarify_metrics(raw_metrics)
        report_metrics(flatteneds.iteritems(), hostname, timestamp=timestamp)
        time.sleep(poll_interval)

if __name__ == '__main__':
    do_your_job()
