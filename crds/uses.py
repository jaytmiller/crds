"""uses.py defines functions which will list the files which use a given 
reference or mapping file.

>>> findall_mappings_using_reference("u451251ej_bpx.fits")
['hst.pmap', 'hst_acs.imap', 'hst_acs_bpixtab.rmap']

"""
from __future__ import print_function

import sys
import os.path

from . import rmap, pysh, config, cmdline, utils, log
from crds.client import api

def findall_rmaps_using_reference(filename, observatory="hst"):
    """Return the basename of all reference mappings which mention 
    `filename`.
    """
    mapping_path = config.get_path("test.pmap", observatory)
    rmaps = pysh.lines("find ${mapping_path} -name '*.rmap' |"
                       " xargs grep -l ${filename}")
    return [os.path.basename(r.strip()) for r in rmaps]

def findall_imaps_using_rmap(filename, observatory="hst"):
    """Return the basenames of all instrument contexts which mention 
    `filename`.
    """
    mapping_path = config.get_path("test.pmap", observatory)
    imaps = pysh.lines("find ${mapping_path} -name '*.imap' |"
                       " xargs grep -l ${filename}")
    return [os.path.basename(imap.strip()) for imap in imaps]

def findall_pmaps_using_imap(filename, observatory="hst"):
    """Return the basenames of all pipeline contexts which mention 
    `filename`.
    """
    mapping_path = config.get_path("test.pmap", observatory)
    pmaps = pysh.lines("find ${mapping_path} -name '*.pmap' |"
                       " xargs grep -l ${filename}")
    return [os.path.basename(pmap.strip()) for pmap in pmaps]

def findall_mappings_using_reference(reference, observatory="hst"):
    """Return the basenames of all mapping files in the hierarchy which
    mentions reference `reference`.
    """
    mappings = []
    for rmap in findall_rmaps_using_reference(reference, observatory):
        mappings.append(rmap)
        for imap in findall_imaps_using_rmap(rmap, observatory):
            mappings.append(imap)
            for pmap in findall_pmaps_using_imap(imap, observatory):
                mappings.append(pmap)
    return sorted(list(set(mappings)))

def findall_mappings_using_rmap(rmap, observatory="hst"):
    """Return the basenames of all mapping files in the hierarchy which
    mentions reference mapping `rmap`.
    """
    mappings = []
    for imap in findall_imaps_using_rmap(rmap, observatory):
        mappings.append(imap)
        for pmap in findall_pmaps_using_imap(imap, observatory):
            mappings.append(pmap)
    return sorted(list(set(mappings)))

def test():
    """Run the module doctest."""
    import doctest
    from . import uses
    return doctest.testmod(uses)

def uses(files, observatory="hst"):
    """Return the list of mappings which use any of `files`."""
    mappings = []
    for file_ in files:
        if file_.endswith(".rmap"):
            mappings.extend(
                findall_mappings_using_rmap(file_, observatory))
        elif file_.endswith(".imap"):
            mappings.extend(
                findall_pmaps_using_imap(file_, observatory))
        elif file_.endswith(".pmap"):
            pass  # nothing refers to a .pmap
        else:
            mappings.extend(
                findall_mappings_using_reference(file_, observatory))
    return sorted(list(set(mappings)))

def datasets_using(references, context):
    """Print out the DADSOPS dataset ids which historically used the specified reference files."""
    datasets = {}
    using = set()
    for reference in references:
        if config.is_mapping(reference):
            log.error("Used file", repr(reference), "is a mapping file.  Must be a reference file.")
            continue
        pmap = rmap.get_cached_mapping(context)
        instrument, filekind = utils.get_file_properties(pmap.observatory, reference)
        if instrument not in datasets:
            log.verbose("Dumping dataset info for", repr(instrument), "from", repr(api.get_crds_server()))
            datasets[instrument] = api.get_dataset_headers_by_instrument(context, instrument)
        for (dataset_id, pars) in datasets[instrument].items():
            if reference.upper() in pars[filekind.upper()]:  # handle things like iref$u451251ej_bpx.fits
                using.add(dataset_id)
    return sorted(list(using))

class UsesScript(cmdline.Script):
    """Command line script for printing rmaps using references,  or datasets using references."""

    description = """
Prints out the mappings which refer to the specified mappings or references.

Prints out the datasets which historically used a particular reference as defined by DADSOPS.
    """

    epilog = """
crds.uses can be invoked like this:

% python -m crds.uses --files n3o1022ij_drk.fits --hst
hst.pmap
hst_0001.pmap
hst_0002.pmap
hst_0003.pmap
...
hst_0041.pmap
hst_acs.imap
hst_acs_0001.imap
hst_acs_0002.imap
hst_acs_0003.imap
...
hst_acs_0008.imap
hst_acs_darkfile.rmap
hst_acs_darkfile_0001.rmap
hst_acs_darkfile_0002.rmap
hst_acs_darkfile_0003.rmap
...
hst_acs_darkfile_0005.rmap

% python -m crds.uses --files n3o1022ij_drk.fits --print-datasets --hst
"""
    def add_args(self):
        """Add command line parameters unique to this script."""
        super(UsesScript, self).add_args()
        self.add_argument("--files", nargs="+", 
            help="References for which to dump using mappings or datasets.")        
        self.add_argument("-d", "--print-datasets", action="store_true", dest="print_datasets",
            help="Print the ids of datasets last historically using a reference.")

    def main(self):
        """Process command line parameters in to a context and list of
        reference files.   Print out the match tuples within the context
        which contain the reference files.
        """
        if self.args.print_datasets:
            self.print_datasets_using_references()
        else:
            self.print_mappings_using_files()
            
    def locate_file(self, file_):
        """Just use basenames for identifying file references."""
        return os.path.basename(file_)
            
    def print_mappings_using_files(self):
        """Print out the mappings which refer to the specified mappings or references."""
        mappings = uses(self.files, self.observatory)
        for mapping in mappings:
            print(mapping)
            
    def print_datasets_using_references(self):
        """Print out the datasets which refer to the specified references."""
        dataset_ids = datasets_using(self.files, self.default_context)
        for dataset_id in dataset_ids:
            print(dataset_id)
        
if __name__ == "__main__":
    UsesScript()()
