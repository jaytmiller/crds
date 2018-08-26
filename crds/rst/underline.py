import sys

# ==================================================
from crds import pysh

from . import rstutils

# ==================================================

def main(title, underline_char="^"):
    print(rstutils.underline(title, underline_char))

# ==================================================

if __name__ == "__main__":
    pysh.usage("<line of text> [underline_char='^']", 1, 1,
               "Echo <line of text> followed by a second line underlining it with the specified char or '^' if none is specified.")
    main(*sys.argv[1:])




