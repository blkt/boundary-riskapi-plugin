"""Plugin for Boundary Meter for Riskapi.

This plugin reads Folsom data encoded as JSON from an URL, flattens
its structure, and writes it to standard output as

  metric measure host timestamp

By default, it fetches data from http://localhost:5565/_metrics/ every
5000 milliseconds, but it can be configured (at plugin installation
time) to fetch data from another host or via another port and more or
less frequently.

"""

__all__ = ["do_your_job", "report_metrics", "flatten_metrics",
           "flatten_folsom_metric", "get_metrics",
           "boundarify_metric_name", "parse_params"]
