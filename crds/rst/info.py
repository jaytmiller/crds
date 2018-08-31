"""This module is a command line script which lists the reference and/or
mapping files associated with the specified contexts by consulting the CRDS
server.   More generally it's for printing out information on CRDS files.
"""
import sys
import os.path
import re
import pprint

# ============================================================================

from crds.core import cmdline
from crds import data_file
from crds import matches

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

    $ crds rstinfo --selection-criteria --contexts jwst-all-wfssbkg-edit
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
            '--selection-criteria', action="store_true",
            help=('Print out the matching criteria associated with'
                  ' the specified contexts.'))
        self.add_argument(
            '--datamodels-translations', action="store_true",
            help='Print out FITS to datamodels translations.')
        self.add_argument(
            '--array-names', action="store_true",
            help='Print out names of arrays contained by the specified reference files.')
        self.add_argument(
            '--array-formats', action="store_true",
            help='Print array formats as .rst for references associated with contexts or --files.')
        self.add_argument(
            '--files', nargs="*", default=[],
            help='Print out names of arrays contained by the specified reference files.')
        super(RstInfoScript, self).add_args()
        
    def main(self):
        """Generate .rst as requested by parameters."""
        if self.args.selection_criteria:
            print(self.format_selection_criteria())

        if self.args.datamodels_translations:
            print(self.format_datamodels_translations())

        if self.args.array_names:
            self.print_array_names()

        if self.args.array_formats:
            for refrst in self.array_formats():
                print(refrst)

    def array_formats(self):
        references = self.files or self.get_context_references()
        rst = ""
        for reffile in references:
            refpath = self.locate_file(reffile)
            yield self.reference_formats(refpath)
    
    def reference_formats(self, refpath):
        # title = "Array Formats for " + repr(os.path.basename(refpath))
        title = "Array Formats for " + self.characterize_refpath(refpath)
        colnames = ("Array Name", "Kind", "Shape", "Data Type")
        rows = self.get_array_formats(refpath)
        table = rstutils.CrdsTable(title, colnames, rows)
        return table.to_rst()

    def characterize_refpath(self, refpath):
        ref = os.path.basename(refpath)
        lookups = matches.find_full_match_paths(self.default_context, ref)
        lookup = lookups[0][1]
        lookup = [(self.locator.dm_to_fits(par[0]),repr(par[1]))
                   for par in lookup ]
        selection = " ".join("=".join(par) for par in lookup)
        date_time = "USEAFTER=" + repr(lookups[0][2][0][1])
        return repr(ref) + " : " + selection + " " + date_time

    def get_array_formats(self, refpath):
        formats = []
        for array_name in data_file.get_array_names(refpath):
            props = data_file.get_array_properties(refpath, array_name, "A")
            row = self.massage_array_props(array_name, props)
            formats.append(row)
        return formats[1:]  # skip PRIMARY HDU

    def massage_array_props(self, array_name, props):
        """Given the `array_name` and it's corresponding properties
        dictionary `props`, massage the field strings for readability
        in the .rst or HTML output table.
        return (array_name, kind, shape, data_type)
        """
        kind, shape, column_names, data_type = \
            props["KIND"], props["SHAPE"], props["COLUMN_NAMES"], \
            props["DATA_TYPE"]
        shape = str(shape).replace(" ","")
        if re.match(r"^.*__\d+$", array_name):
            name, ver = array_name.split("__")
            array_name = f"({name},{ver})"
        return (array_name, kind, shape, data_type)
    
    def print_array_names(self):
        """Print out the array names associated with the references from
        the specified contexts or --files.
        """
        references = self.get_context_references() + self.files
        for reffile in references:
            refpath = self.locate_file(reffile)
            for array in data_file.get_array_names(refpath):
                print(os.path.basename(reffile)+":", array)

    def format_datamodels_translations(self):
        """Return FITS to datamodels translations as a RST table."""
        title = "FITS to Data Models Translations"
        colnames = ("FITS", "Datamodels")
        translations = self.get_fits_translations()
        table = rstutils.CrdsTable(title, colnames, translations)
        return table.to_rst()
        
    def format_selection_criteria(self):
        """Return matching criteria associated with the specified contexts
        as a RST table.
        """
        title, description, colnames, data = self.get_selection_criteria()
        table = rstutils.CrdsTable(title, colnames, data,
                                   description=description)
        return table.to_rst()

    def get_selection_criteria(self):
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
        reftype = loaded.filekind.upper()
        title = f"Reference Selection Keywords for {reftype}"
        description = f"CRDS selects appropriate {reftype} references based on the following keywords.\n{reftype} is not applicable for instruments not in the table.\n"
        return title, description, colnames, rows

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
        return [self.locator.dm_to_fits(key) for key in keywords]

    def to_fits_datamodels(self, keywords):
        """Returns [(FITS name, datamodels name), ...] associated with
        list of `keywords` names.
        """
        return zip([self.locator.dm_to_fits(key) for key in keywords],
                   [self.locator.fits_to_dm(key) for key in keywords])

#         print((array_name, kind, shape, column_names, data_type))
#         if kind == "TABLE":
#             data_type = dict(data_type)
#             for colname in column_names:
#                 data_type[colname] = self.simplify_col_format(data_type[colname])
#         return (array_name, kind, shape, data_type)

# #    def simplify_col_format(self, coltype):
# #        return re.sub(r"[\"\']([^ ]+[\',",

# # ============================================================================

# def simplify_type(raw_match):
#     label = raw_match.group(1)
#     repeat = raw_match.group(2)
#     atype = raw_match.group(3)
#     digits = raw_match.group(4)
#     trail = raw_match.group(5)
#     pprint.pprint((label, repeat, atype, digits, trail))
#     long_atype = {
#         "b" : "bytes",
#         "i" : "int",
#         "u" : "uint",
#         "f" : "float",
#         "c" : "complex",
#         "S" : "string",
#     }[atype]
#     if repeat == None:
#         repeat = ""
#     else:
#         repeat = f"[{repeat}]"
#     if long_atype != "string":
#         bits = str(2**int(digits))
#     else:
#         bits = str(digits) # actually bytes
#     field = label + long_atype + bits + repeat
#     if field.endswith(tuple("0123456789")):
#         field = field + ", "
#     return field

# ============================================================================

if __name__ == "__main__":
    sys.exit(RstInfoScript()())
