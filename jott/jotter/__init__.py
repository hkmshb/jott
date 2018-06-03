"""
This module contains the main Jotter class and related classes.

The Jotter interface is the generic API for accessing and storing pages
and other data in the jotter. The interface uses Path objects to indicate 
a specific page. See Jotter.pages.lookup_from_user_input to obtain a Path
from a page name as string. Pages in the jotter are represented by the 
Page object, which allows to access the page contents.
"""
