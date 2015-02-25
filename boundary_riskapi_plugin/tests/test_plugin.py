from StringIO import StringIO
from mock import patch, call, sentinel, mock_open, MagicMock
from nose.tools import (assert_true, assert_false, assert_equal,
                        assert_is_instance, assert_is_none,
                        assert_is_not_none, assert_items_equal)
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
                   create=True) as m:
            params = plugin.parse_params()
        expected = dict(riskapi_base_url="localhost",
                        riskapi_port="5565",
                        riskapi_poll_interval="5000")

        assert_equal(params, expected)

    def test_parse_params_2(self):
        with patch("boundary_riskapi_plugin.plugin.open",
                   mock_open(read_data=PARAMS_JSON_2),
                   create=True) as m:
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

    def test_get_metric_urls_1(self):
        base_url = "localhost"
        port = "5565"
        path1 = "_metrics"
        paths = ["foo", "bar", "baz"]
        urls = plugin.get_metric_urls(base_url, port, path1, paths)
        expected = ["http://localhost:5565/_metrics/foo",
                    "http://localhost:5565/_metrics/bar",
                    "http://localhost:5565/_metrics/baz"]

        assert_items_equal(urls, expected)

    def test_get_metric_urls_2(self):
        base_url = "localhost"
        port = 5565
        path1 = "_metrics"
        paths = ["foo", "bar", "baz"]
        urls = plugin.get_metric_urls(base_url, port, path1, paths)
        expected = ["http://localhost:5565/_metrics/foo",
                    "http://localhost:5565/_metrics/bar",
                    "http://localhost:5565/_metrics/baz"]

        assert_items_equal(urls, expected)

    def test_boundarify_name_1(self):
        raw_name = "FOO"
        name = plugin.boundarify_metric_name(raw_name)

        assert_equal(name, u"STATPRO_RISKAPI_FOO")

    def test_boundarify_name_2(self):
        raw_name = "FOO.BAR"
        name = plugin.boundarify_metric_name(raw_name)

        assert_equal(name, u"STATPRO_RISKAPI_FOO_BAR")

    def test_boundarify_name_3(self):
        raw_name = "FOO-BAR"
        name = plugin.boundarify_metric_name(raw_name)

        assert_equal(name, u"STATPRO_RISKAPI_FOO_BAR")

    def test_boundarify_name_4(self):
        raw_name = "FOO.BAR-BAZ"
        name = plugin.boundarify_metric_name(raw_name)

        assert_equal(name, u"STATPRO_RISKAPI_FOO_BAR_BAZ")

    def test_flatten_folsom_metric_1(self):
        metric = "metric"
        tree = {"foo": 1}
        flattened = plugin.flatten_folsom_metric(metric, tree)

        assert_equal(flattened, {"metric_foo": 1})

    def test_flatten_folsom_metric_2(self):
        metric = "metric"
        tree = {"foo": {"bar": 2}}
        flattened = plugin.flatten_folsom_metric(metric, tree)

        assert_equal(flattened, {"metric_foo_bar": 2})

    def test_flatten_folsom_metric_3(self):
        metric = "metric"
        tree = {"foo": {"bar": 3, "baz": 4}}
        flattened = plugin.flatten_folsom_metric(metric, tree)

        assert_equal(flattened, {"metric_foo_bar": 3,
                                 "metric_foo_baz": 4})

    def test_flatten_folsom_metric_4(self):
        metric = "metric"
        tree = {"foo": {"bar": 3, "baz": 4}, "quux": {"fubar": 5}}
        flattened = plugin.flatten_folsom_metric(metric, tree)

        assert_equal(flattened, {"metric_foo_bar": 3,
                                 "metric_foo_baz": 4,
                                 "metric_quux_fubar": 5})

    def test_keep_looping_p(self):
        assert_true(plugin.keep_looping_p())

class TestPlugin(object):

    def test_get_metrics_1(self):
        base_url = "localhost"
        port = "5565"
        path1 = "_metrics"
        paths = ["foo"]

        with patch("boundary_riskapi_plugin.plugin.urllib") as url_mock:
            m = MagicMock()
            m.read.side_effect = ["""{"foo": 0}"""]
            url_mock.urlopen.return_value = m
            expected = ([["foo", dict(foo=0)]], [])
            calls = [call("http://localhost:5565/_metrics/foo"),
                     call().read()]

            ress = plugin.get_metrics(base_url, port, path1, paths)

            assert_equal(ress, expected)
            url_mock.urlopen.assert_has_calls(calls)

    def test_get_metrics_2(self):
        base_url = "localhost"
        port = "5565"
        path1 = "_metrics"
        paths = ["foo", "bar"]

        with patch("boundary_riskapi_plugin.plugin.urllib") as url_mock:
            m = MagicMock()
            m.read.side_effect = ["""{"foo": 0}""", """{"bar": 0}"""]
            url_mock.urlopen.return_value = m
            expected = ([["foo", dict(foo=0)], ["bar", dict(bar=0)]], [])
            calls = [call("http://localhost:5565/_metrics/foo"),
                     call().read(),
                     call("http://localhost:5565/_metrics/bar"),
                     call().read()]

            ress = plugin.get_metrics(base_url, port, path1, paths)

            assert_equal(ress, expected)
            url_mock.urlopen.assert_has_calls(calls)

    def test_get_metrics_3(self):
        base_url = "localhost"
        port = "5565"
        path1 = "_metrics"
        paths = ["foo", "bar"]

        with patch("boundary_riskapi_plugin.plugin.urllib") as url_mock:
            m = MagicMock()
            m.read.side_effect = ["""{"foo": 0}""", IOError()]
            url_mock.urlopen.return_value = m
            expected = ([["foo", dict(foo=0)]], ["http://localhost:5565/_metrics/bar"])
            calls = [call("http://localhost:5565/_metrics/foo"),
                     call().read(),
                     call("http://localhost:5565/_metrics/bar"),
                     call().read()]

            ress = plugin.get_metrics(base_url, port, path1, paths)

            assert_equal(ress, expected)
            url_mock.urlopen.assert_has_calls(calls)

    def test_boundarify_metrics_1(self):
        metrics_tree = ([], [])
        ress = plugin.boundarify_metrics(metrics_tree)
        assert_equal(0, len(ress))

    def test_boundarify_metrics_2(self):
        metrics_tree = ([['queue-length-rapi', {u'value': 0}]], [])
        ress = plugin.boundarify_metrics(metrics_tree)
        assert_equal(1, len(ress))
        assert_equal(dict(STATPRO_RISKAPI_QUEUE_LENGTH_RAPI=0), ress)

    def test_boundarify_metrics_3(self):
        metrics_tree = ([['queue-length-rapi', {u'value': 0}]],
                        ["http://localhost:5565/_metrics/bar"])
        ress = plugin.boundarify_metrics(metrics_tree)
        assert_equal(1, len(ress))
        assert_equal(dict(STATPRO_RISKAPI_QUEUE_LENGTH_RAPI=0), ress)

    def test_boundarify_metrics_4(self):
        metrics_tree = ([['throughput-rapi',
                          {u'value': {u'acceleration':
                                      {u'five_to_fifteen': -7.409488799339047e-06},
                                      u'count': 107,
                                      u'one': 0.0006665011787293809}}]], [])
        ress = plugin.boundarify_metrics(metrics_tree)
        assert_equal(2, len(ress))
        assert_equal(dict(STATPRO_RISKAPI_THROUGHPUT_RAPI_COUNT=107,
                          STATPRO_RISKAPI_THROUGHPUT_RAPI_ONE=0.0006665011787293809), ress)

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

    def test_do_your_job(self):
        with patch("boundary_riskapi_plugin.plugin.POLL_INTERVAL", 0):
            with patch("boundary_riskapi_plugin.plugin.keep_looping_p", side_effect=[True, False]):
                plugin.do_your_job()
