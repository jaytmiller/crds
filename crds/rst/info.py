"""This module is a command line script which lists the reference and/or
mapping files associated with the specified contexts by consulting the CRDS
server.   More generally it's for printing out information on CRDS files.
"""
import os.path
import sys
from collections import OrderedDict
import json
import pprint

# ============================================================================

from astropy.io import fits

# ============================================================================

import crds
from crds.core import config, log, python23, rmap, heavy_client, cmdline, utils
from crds.core import crds_cache_locking
from crds import data_file

from crds.client import api

from . import rstutils

# ============================================================================

class RstInfoScript(cmdline.ContextsScript):
    """Command line script for generating .rst output relevant to CRDS and CAL
    documentation, particularly matching criteria and array formats.
    """

    description = """
    """
        
    epilog = """
    """

    def __init__(self, *args, **keys):
        super(RstInfoScript, self).__init__(*args, **keys)
        self.show_context_resolution = False
        self._file_info = {}
        
    def add_args(self):
        """Add switches unique to crds.list."""

        self.add_argument(
            '--matching-criteria', nargs="+", dest="matching_criteria",
            default=None, metavar='REFTYPE',
            help='Print out the matching criteria associated with REFTYPE.')

        
        self.add_argument(
            '--datamodels-translations', nargs="+", dest="mathching_criteria",
            default=None, metavar='REFTYPE',
            help='Print out the matching criteria associated with REFTYPE.')

        super(RstInfoScript, self).add_args()
        
    def main(self):
        """Generate .rst as requested by parameters."""

        if self.args.matching_criteria:
            self.format_matching_criteria()

    def format_matching_criteria(self):
        title, colnames, data = self.get_matching_criteria()
        table = rstutils.CrdsTable(title, colnames, data)
        print(table.to_rst())


    def get_matching_criteria(self):
        colnames = ("Instrument", "Keywords")
        rows = []
        for context in self.contexts:
            assert context.endswith(".rmap"), \
                f"Context {context} is not an rmap."
            loaded = crds.get_symbolic_mapping(
                context, observatory=self.observatory)
            required = loaded.get_required_parkeys()
            required = self.to_fits_names(required)
            required = ["INSTRUME"] + required
            required = repr(required)[1:-1].replace("'","")  # drop [,],'
            criteria = (loaded.instrument.upper(),required)
            rows += [criteria]
        title = f"Reference Selection Keywords for {loaded.filekind.upper()}"
        return title, colnames, rows
    
    def to_fits_names(self, keywords):
        pairs = self.locator.get_fits_datamodel_pairs(keywords)
        return [pair[0] for pair in pairs
                if not pair[0].startswith("META.")]
                                                            
        
if __name__ == "__main__":
    sys.exit(RstInfoScript()())
