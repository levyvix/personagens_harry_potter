"""Scraper modules for Harry Potter Wiki."""

from .wiki_caller_async import WikiCaller as WikiCallerAsync
from .wiki_caller_multiprocessing import WikiCaller as WikiCallerMultiprocessing
from .wiki_caller_sync import WikiCaller as WikiCallerSync

__all__ = ["WikiCallerSync", "WikiCallerMultiprocessing", "WikiCallerAsync"]
