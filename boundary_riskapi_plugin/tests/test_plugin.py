from StringIO import StringIO
from mock import patch, call, mock_open, MagicMock
from nose.tools import (assert_true, assert_equal, assert_items_equal)
import time as time

import boundary_riskapi_plugin.plugin as plugin

PARAMS_JSON_1 = """
{
  "riskapi_base_url": "localhost",
  "riskapi_port": "5565",
  "riskapi_poll_interval": "5000"
}
"""
PARAMS_JSON_2 = """
{
  "riskapi_base_url": "localhost",
  "riskapi_port": 5565,
  "riskapi_poll_interval": 5000
}
"""

class TestUtils(object):

    def test_parse_params_1(self):
        with patch("boundary_riskapi_plugin.plugin.open",
                   mock_open(read_data=PARAMS_JSON_1),
                   create=True):
            params = plugin.parse_params()
        expected = dict(riskapi_base_url="localhost",
                        riskapi_port="5565",
                        riskapi_poll_interval="5000")

        assert_equal(params, expected)

    def test_parse_params_2(self):
        with patch("boundary_riskapi_plugin.plugin.open",
                   mock_open(read_data=PARAMS_JSON_2),
                   create=True):
            params = plugin.parse_params()
        expected = dict(riskapi_base_url="localhost",
                        riskapi_port=5565,
                        riskapi_poll_interval=5000)

        assert_equal(params, expected)

    def test_parse_params_3(self):
        with patch("boundary_riskapi_plugin.plugin.open", create=True) as m:
            m.side_effect = IOError()
            params = plugin.parse_params()
        expected = dict()

        assert_equal(params, expected)

    def test_keep_looping_p(self):
        assert_true(plugin.keep_looping_p())

class TestPlugin(object):

    def test_get_metrics_data_1(self):
        metrics = plugin.init_metrics()
        keys = ["STATPRO_RISKAPI_OVERALL_COMPUTE_ARITHMETIC_MEAN"]
        metric = {key: metrics[key] for key in keys}

        with patch("boundary_riskapi_plugin.plugin.urllib") as url_mock:
            m = MagicMock()
            m.read.side_effect = ["""{"value": {"arithetic_mean": 0}}"""]
            url_mock.urlopen.return_value = m
            expected = ({"http://localhost:5565/_metrics/overall.compute":
                         dict(value=dict(arithetic_mean=0))},
                        [])
            calls = [call("http://localhost:5565/_metrics/overall.compute"),
                     call().read()]

            ress = plugin.get_metrics_data(metric)

            assert_equal(ress, expected)
            url_mock.urlopen.assert_has_calls(calls)

    def test_get_metrics_data_2(self):
        metrics = plugin.init_metrics()
        keys = ["STATPRO_RISKAPI_OVERALL_COMPUTE_ARITHMETIC_MEAN",
                "STATPRO_RISKAPI_OVERALL_ERRORS_ONE"]
        metric = {key: metrics[key] for key in keys}

        with patch("boundary_riskapi_plugin.plugin.urllib") as url_mock:
            m = MagicMock()
            m.read.side_effect = ["""{"value": {"arithmetic_mean": 0}}""",
                                  """{"value": {"one": 0}}"""]
            url_mock.urlopen.return_value = m
            expected = ({"http://localhost:5565/_metrics/overall.compute":
                         dict(value=dict(arithmetic_mean=0)),
                         "http://localhost:5565/_metrics/overall.errors":
                         dict(value=dict(one=0))},
                        [])
            calls = [call("http://localhost:5565/_metrics/overall.compute"),
                     call().read(),
                     call("http://localhost:5565/_metrics/overall.errors"),
                     call().read()]

            ress = plugin.get_metrics_data(metric)

            assert_equal(ress, expected)
            url_mock.urlopen.assert_has_calls(calls)

    def test_get_metrics_data_3(self):
        metrics = plugin.init_metrics()
        keys = ["STATPRO_RISKAPI_OVERALL_COMPUTE_ARITHMETIC_MEAN",
                "STATPRO_RISKAPI_OVERALL_ERRORS_ONE"]
        metric = {key: metrics[key] for key in keys}

        with patch("boundary_riskapi_plugin.plugin.urllib") as url_mock:
            m = MagicMock()
            m.read.side_effect = ["""{"value": {"arithmetic_mean": 0}}""",
                                  IOError()]
            url_mock.urlopen.return_value = m
            expected = ({"http://localhost:5565/_metrics/overall.compute":
                          dict(value=dict(arithmetic_mean=0))},
                        ["http://localhost:5565/_metrics/overall.errors"])
            calls = [call("http://localhost:5565/_metrics/overall.compute"),
                     call().read(),
                     call("http://localhost:5565/_metrics/overall.errors"),
                     call().read()]

            ress = plugin.get_metrics_data(metric)

            assert_equal(ress, expected)
            url_mock.urlopen.assert_has_calls(calls)

    def test_get_metrics_data_4(self):
        metrics = plugin.init_metrics()
        keys = ["STATPRO_RISKAPI_OVERALL_COMPUTE_ARITHMETIC_MEAN",
                "STATPRO_RISKAPI_OVERALL_COMPUTE_PERCENTILE_50"]
        metric = {key: metrics[key] for key in keys}

        with patch("boundary_riskapi_plugin.plugin.urllib") as url_mock:
            m = MagicMock()
            m.read.side_effect = ["""{"value": {"percentile": {"50": 0}, "arithmetic_mean": 0}}"""]
            url_mock.urlopen.return_value = m
            expected = ({"http://localhost:5565/_metrics/overall.compute":
                          dict(value=dict(arithmetic_mean=0,
                                          percentile={"50": 0}))},
                        [])
            calls = [call("http://localhost:5565/_metrics/overall.compute"),
                     call().read()]

            ress = plugin.get_metrics_data(metric)

            assert_equal(ress, expected)
            url_mock.urlopen.assert_has_calls(calls)

    def test_boundarify_metrics_1(self):
        metrics = plugin.init_metrics()
        metrics_tree = ({}, [])
        ress = plugin.boundarify_metrics(metrics, metrics_tree)
        assert_equal(0, len(ress))

    def test_boundarify_metrics_2(self):
        metrics = plugin.init_metrics()
        metrics_tree = ({"http://localhost:5565/_metrics/queue-length-rapi":
                         {u'value': 0}},
                        [])
        ress = plugin.boundarify_metrics(metrics, metrics_tree)
        assert_equal(1, len(ress))
        assert_equal(dict(STATPRO_RISKAPI_QUEUE_LENGTH_RAPI=0), ress)

    def test_boundarify_metrics_3(self):
        metrics = plugin.init_metrics()
        metrics_tree = ({"http://localhost:5565/_metrics/queue-length-rapi":
                         {u'value': 0}},
                        ["http://localhost:5565/_metrics/bar"])
        ress = plugin.boundarify_metrics(metrics, metrics_tree)
        assert_equal(1, len(ress))
        assert_equal(dict(STATPRO_RISKAPI_QUEUE_LENGTH_RAPI=0), ress)

    def test_boundarify_metrics_4(self):
        metrics = plugin.init_metrics()
        metrics_tree = ({"http://localhost:5565/_metrics/throughput-rapi":
                         {u'value': {u'acceleration':
                                     {u'five_to_fifteen': -7.409488799339047e-06},
                                     u'count': 107,
                                     u'one': 0.0006665011787293809}}},
                        [])
        ress = plugin.boundarify_metrics(metrics, metrics_tree)
        assert_equal(2, len(ress))
        assert_equal(dict(STATPRO_RISKAPI_THROUGHPUT_RAPI_COUNT=107,
                          STATPRO_RISKAPI_THROUGHPUT_RAPI_ONE=0.0006665011787293809), ress)

    def test_boundarify_metrics_stateful(self):
        metrics = plugin.init_metrics()
        keys = ["STATPRO_RISKAPI_OVERALL_ERRORS_COUNT"]
        metric = {key: metrics[key] for key in keys}

        metrics_tree = ({"http://localhost:5565/_metrics/overall.errors":
                         {u'value': {u'count': 107}}},
                        [])
        ress = plugin.boundarify_metrics(metric, metrics_tree)
        assert_equal(1, len(ress))
        assert_equal(dict(STATPRO_RISKAPI_OVERALL_ERRORS_COUNT=107), ress)

        metrics_tree = ({"http://localhost:5565/_metrics/overall.errors":
                         {u'value': {u'count': 110}}},
                        [])
        ress = plugin.boundarify_metrics(metric, metrics_tree)
        assert_equal(1, len(ress))
        assert_equal(dict(STATPRO_RISKAPI_OVERALL_ERRORS_COUNT=3), ress)

    def test_report_metrics_1(self):
        metrics = [("metric_foo_bar", 3), ("metric_foo_baz", 4),
                   ("metric_quux_fubar", 5)]
        hostname = "hostname"
        expected = "metric_foo_bar 3 hostname\n"
        expected += "metric_foo_baz 4 hostname\n"
        expected += "metric_quux_fubar 5 hostname\n"

        with patch("sys.stdout", new=StringIO()) as fake_out:
            plugin.report_metrics(metrics, hostname)

        assert_equal(fake_out.getvalue(), expected)

    def test_report_metrics_2(self):
        metrics = [("metric_foo_bar", 3), ("metric_foo_baz", 4),
                   ("metric_quux_fubar", 5)]
        hostname = "hostname"
        timestamp = time.time()
        expected = "metric_foo_bar 3 hostname %d\n" % timestamp
        expected += "metric_foo_baz 4 hostname %d\n" % timestamp
        expected += "metric_quux_fubar 5 hostname %d\n" % timestamp

        with patch("sys.stdout", new=StringIO()) as fake_out:
            plugin.report_metrics(metrics, hostname, timestamp)

        assert_equal(fake_out.getvalue(), expected)

    def test_main(self):
        with patch("boundary_riskapi_plugin.plugin.urllib") as url_mock:
            m = MagicMock()
            m.read.side_effect = [
                """{"value": {"percentile": {"50": 0, "95": 0}, "arithmetic_mean": 0}}""",
                """{"value": {"count": 0, "one": 0}}""",
                """{"value": {"count": 0, "one": 0}}""",
                """{"value": {"percentile": {"50": 0, "95": 0}, "arithmetic_mean": 0}}""",
                """{"value": 0}""",
                """{"value": {"percentile": {"50": 0, "95": 0}, "arithmetic_mean": 0}}""",
                """{"value": {"count": 0, "one": 0}}"""]
            url_mock.urlopen.return_value = m
            expected = ({"http://localhost:5565/_metrics/overall.compute":
                          dict(value=dict(arithmetic_mean=0,
                                          percentile={"50": 0, "95": 0})),
                         "http://localhost:5565/_metrics/overall.errors":
                          dict(value=dict(count=0, one=0)),
                         "http://localhost:5565/_metrics/overall.throughput":
                          dict(value=dict(count=0, one=0)),
                         "http://localhost:5565/_metrics/overall.time":
                          dict(value=dict(arithmetic_mean=0,
                                          percentile={"50": 0, "95": 0})),
                         "http://localhost:5565/_metrics/queue-length-rapi":
                          dict(value=0),
                         "http://localhost:5565/_metrics/request_time-queue-rapi_poller":
                          dict(value=dict(arithmetic_mean=0,
                                          percentile={"50": 0, "95": 0})),
                         "http://localhost:5565/_metrics/throughput-rapi":
                          dict(value=dict(count=0, one=0))},
                        [])
            calls = [call("http://localhost:5565/_metrics/overall.compute"),
                     call().read(),
                     call("http://localhost:5565/_metrics/overall.errors"),
                     call().read(),
                     call("http://localhost:5565/_metrics/overall.time"),
                     call().read(),
                     call("http://localhost:5565/_metrics/queue-length-rapi"),
                     call().read(),
                     call("http://localhost:5565/_metrics/queue-length-rapi"),
                     call().read(),
                     call("http://localhost:5565/_metrics/request_time-queue-rapi_poller"),
                     call().read(),
                     call("http://localhost:5565/_metrics/throughput-rapi"),
                     call().read()]
            resulting_output = """\
STATPRO_RISKAPI_OVERALL_THROUGHPUT_COUNT 0 mmori 123456789
STATPRO_RISKAPI_OVERALL_COMPUTE_PERCENTILE_95 0 mmori 123456789
STATPRO_RISKAPI_OVERALL_TIME_ARITHMETIC_MEAN 0 mmori 123456789
STATPRO_RISKAPI_THROUGHPUT_RAPI_ONE 0 mmori 123456789
STATPRO_RISKAPI_OVERALL_TIME_PERCENTILE_95 0 mmori 123456789
STATPRO_RISKAPI_OVERALL_TIME_PERCENTILE_50 0 mmori 123456789
STATPRO_RISKAPI_OVERALL_COMPUTE_ARITHMETIC_MEAN 0 mmori 123456789
STATPRO_RISKAPI_THROUGHPUT_RAPI_COUNT 0 mmori 123456789
STATPRO_RISKAPI_OVERALL_THROUGHPUT_ONE 0 mmori 123456789
STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_ARITHMETIC_MEAN 0 mmori 123456789
STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_PERCENTILE_95 0 mmori 123456789
STATPRO_RISKAPI_OVERALL_COMPUTE_PERCENTILE_50 0 mmori 123456789
STATPRO_RISKAPI_OVERALL_ERRORS_ONE 0 mmori 123456789
STATPRO_RISKAPI_REQUEST_TIME_QUEUE_RAPI_PERCENTILE_50 0 mmori 123456789
STATPRO_RISKAPI_OVERALL_ERRORS_COUNT 0 mmori 123456789
STATPRO_RISKAPI_QUEUE_LENGTH_RAPI 0 mmori 123456789
"""
            with patch("boundary_riskapi_plugin.plugin.POLL_INTERVAL", 0):
                with patch("boundary_riskapi_plugin.plugin.keep_looping_p",
                           side_effect=[True, False]):
                    with patch("sys.stdout", new=StringIO()) as fake_out:
                        with patch("time.time", return_value=123456789):
                            plugin.main()
                            assert_equal(fake_out.getvalue(), resulting_output)
