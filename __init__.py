"""
This package contains the following sub-packages:

observer: API for retrieving performance and event data

context: API for retrieving environment and configuration information

The reason for the additional layer of packaging is so that private or
vendor-specific modules can be separated from generic/core functions.
"""
__all__ = ['observer', 'context']
