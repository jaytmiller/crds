"""This module is a command line script which lists the reference and/or
mapping files associated with the specified contexts by consulting the CRDS
server.   More generally it's for printing out information on CRDS files.
"""
import sys

# ============================================================================

from crds.core import cmdline

from . import rstutils

# ============================================================================

class RstInfoScript(cmdline.ContextsScript):
    """Command line script for generating .rst output relevant to CRDS and CAL
    documentation, particularly matching criteria and array formats.
    """

    description = """Utility for generating various kinds of CRDS reference
    file format and keyword documentation.
    """
        
    epilog = """
    1. Generate table of matching criteria:

    $ crds rstinfo --matching-criteria --contexts jwst-all-wfssbkg-edit
    Reference Selection Keywords for WFSSBKG
    ========================================
    ---------- ---------------------------------------------------------------
    Instrument Keywords                                              
    ---------- ---------------------------------------------------------------
    NIRCAM     INSTRUME, EXP_TYPE, DETECTOR, FILTER, PUPIL, DATE-OBS, TIME-OBS 
    NIRISS     INSTRUME, EXP_TYPE, DETECTOR, FILTER, PUPIL, DATE-OBS, TIME-OBS 
    ---------- ---------------------------------------------------------------
    
    2. crds rstinfo --datamodels-translations --
    FITS to Data Models Translations
    ================================
    -------- ---------------------------------
    FITS     Datamodels                        
    -------- ---------------------------------
    BAND     meta.instrument.band              
    CAL_VER  meta.calibration_software_version 
    CHANNEL  meta.instrument.channel           
    DATE-OBS meta.observation.date
    DETECTOR meta.instrument.detector          
    EXP_TYPE meta.exposure.type                
    FILTER   meta.instrument.filter            
    GRATING  meta.instrument.grating           
    INSTRUME meta.instrument.name              
    MODULE   meta.instrument.module            
    PUPIL    meta.instrument.pupil             
    READPATT meta.exposure.readpatt            
    SUBARRAY meta.subarray.name                
    SUBSIZE1 meta.subarray.xsize               
    SUBSIZE2 meta.subarray.ysize               
    SUBSTRT1 meta.subarray.xstart              
    SUBSTRT2 meta.subarray.ystart              
    TIME-OBS meta.observation.time             
    TSOVISIT meta.visit.tsovisit               
    -------- ---------------------------------
    """

    def __init__(self, *args, **keys):
        """Create a RstInfoScript instance."""
        super(RstInfoScript, self).__init__(*args, **keys)
        self.show_context_resolution = False
        self._file_info = {}
        
    def add_args(self):
        """Add switches unique to RstInfoScript."""
        self.add_argument(
            '--matching-criteria', action="store_true",
            help=('Print out the matching criteria associated with'
                  ' the specified contexts.'))
        self.add_argument(
            '--datamodels-translations', action="store_true",
            help='Print out FITS to datamodels translations.')
        super(RstInfoScript, self).add_args()
        
    def main(self):
        """Generate .rst as requested by parameters."""

        if self.args.matching_criteria:
            print(self.format_matching_criteria())

        if self.args.datamodels_translations:
            print(self.format_datamodels_translations())

    def format_datamodels_translations(self):
        """Return FITS to datamodels translations as a RST table."""
        title = "FITS to Data Models Translations"
        colnames = ("FITS", "Datamodels")
        translations = self.get_fits_translations()
        table = rstutils.CrdsTable(title, colnames, translations)
        return table.to_rst()
        
    def format_matching_criteria(self):
        """Return matching criteria associated with the specified contexts
        as a RST table.
        """
        title, colnames, data = self.get_matching_criteria()
        table = rstutils.CrdsTable(title, colnames, data)
        return table.to_rst()

    def get_matching_criteria(self):
        """Return a section title str, list of column names, and table rows
        defining the matching criteria associated with self.contexts.
        """
        colnames = ("Instrument", "Keywords")
        rows = []
        for context in self.contexts:
            assert context.endswith(".rmap"), \
                f"Context {context} is not an rmap."
            loaded = self.get_symbolic_mapping(context)
            required = loaded.get_required_parkeys()
            required = self.to_fits_names(required)
            required = ["INSTRUME"] + required
            required = repr(required)[1:-1].replace("'","")  # drop [,],'
            criteria = (loaded.instrument.upper(),required)
            rows += [criteria]
        title = f"Reference Selection Keywords for {loaded.filekind.upper()}"
        return title, colnames, rows

    def get_fits_translations(self):
        """Returns a sorted list of the form:

        [(FITS name, datamodels name), ...]

        associated with the specified contexts.
        """
        keywords = set()
        for context in self.contexts:
            loaded = self.get_symbolic_mapping(context)
            required = loaded.get_required_parkeys()
            if isinstance(required, dict):
                for _instr, reqs in required.items():
                    reqs = self.to_fits_datamodels(reqs)
                    keywords |= set(reqs)
            else:
                reqs = self.to_fits_datamodels(required)
                keywords |= set(reqs)
        return sorted(list(keywords))
                                               
    
    def to_fits_names(self, keywords):
        """Given a list of datamodels names,  return a list of
        the corresponding FITS keywords.
        """
        pairs = self.to_fits_datamodels(keywords)
        return [pair[0] for pair in pairs]
    
    def to_fits_datamodels(self, keywords):
        """Returns [(FITS name, datamodels name), ...] associated with
        list of `keywords` names.
        """
        pairs = self.locator.get_fits_datamodel_pairs(keywords)
        return [(pair[0],pair[1].lower()) for pair in pairs
                if (not pair[0].startswith("META.") and
                    pair[1].startswith("META."))]
        
if __name__ == "__main__":
    sys.exit(RstInfoScript()())
