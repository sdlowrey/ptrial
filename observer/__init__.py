"""
The observer package provides a time-series sampling interface to various types of data sources.

Time series data consists of a time stamp and one or more metrics.  The combination of a time stamp
and a collection of metrics is referred to as a datapoint.

Datapoints can be retrieved in a variety of encodings including Python dictionary, JSON, or CSV.

Time resolution is rounded to the nearest second.  The time stamp is absolute and can be encoded as 
a text string or an integer (Unix time).
"""
