"""This module computes CRDS cache size as a function of time."""
import sys
import datetime

# ============================================================================

import numpy as np
import matplotlib.dates as mdates
import pylab
import scipy.stats

# ============================================================================

from crds.core import log, utils, cmdline, timestamp
from crds.client import api

# ============================================================================

@utils.cached
def get_info_map(observatory):
    return api.get_file_info_map(
        observatory, fields=["size","delivery_date"])
    
class SizeScript(cmdline.ContextsScript):

    description = """
    Computes CRDS cache size as a function of the specified contexts.
    """
    
    epilog = """    
    """
    
    def main(self):
        """Compute size of specified contexts."""

        files = self.get_context_mappings() + self.get_context_references()

        infos = get_info_map(self.observatory)

        total_size = 0
        for file in files:
            total_size += int(infos[file]["size"])

        first, last = self.contexts[0], self.contexts[-1]
        first_date = infos[first]["delivery_date"].split()[0]
        last_date = infos[last]["delivery_date"].split()[0]
        size = utils.human_format_number(total_size)
        
        log.info(first, last, first_date, last_date, len(files), size)

        return (last_date, total_size)


class PlotSizeScript(cmdline.Script):

    description = """
    Trends CRDS cache growth and size as a function of specified start, end dates
    and days increment.   Plot size points and regression line.
    """
    
    epilog = """
    Run it something like this:

    $ source envs/jwst-crds-ops.sh
    $ crds sync --all
    $  crds misc.size --increment=90 --plot-file=jwst_sizes.png
    """
    
    def add_args(self):    

        super(PlotSizeScript, self).add_args()

        self.add_argument(
            "--start-date", metavar="DATE", type=str,
            help="", default="2014-01-01T00:00:00")
        self.add_argument(
            "--end-date", metavar="DATE", type=str,
            help="", default=timestamp.now())
        self.add_argument(
            "--increment-days", metavar="DAYS", type=str,
            help="", default="30")
        self.add_argument(
            "--plot-file", metavar=".PNG", type=str, default="sizes.png")
        
    def main(self):

        start = timestamp.parse_date(self.args.start_date)
        end = timestamp.parse_date(self.args.end_date)
        increment = datetime.timedelta(days=int(self.args.increment_days))

        current = start
        results = []
        while current < end:

            current_str = timestamp.format_date(current).split()[0]
            script = SizeScript(f"crds.misc.size --up-to-context {current_str}")
            results.append(script())
            current += increment

        self.plot(results)

    def plot(self, results):

        log.info(results)

        sizes = [r[1] for r in results]
        dates = mdates.date2num(
            [timestamp.parse_date(r[0]) for r in results])

        regression = scipy.stats.linregress(dates, sizes)
        rslope, rintercept = regression[0], regression[1]
        
        pylab.suptitle(f"CRDS Cache Growth for "
                       f"{self.observatory.upper()}")
        pylab.title(f"{utils.human_format_number(rslope*7)} bytes/week")
        pylab.xlabel("Date")
        pylab.ylabel("Bytes")
        pylab.plot_date(dates, sizes, "ob")

        """
        slope : float
        slope of the regression line
        intercept : float
        intercept of the regression line
        r-value : float
        correlation coefficient
        p-value : float
        two-sided p-value for a hypothesis test whose null hypothesis is that the slope is zero
        stderr : float
        Standard error of the estimate
        """
        
        date = np.linspace(dates[0], dates[-1], 1000)
        size = list(map(lambda x: rslope*x + rintercept, date))
        pylab.plot(date, size, "-r")
        
        pylab.savefig(self.args.plot_file)
        pylab.show()

        input()

# ==============================================================================================================

if __name__ == "__main__":
    sys.exit(PlotSizeScript()())

    
