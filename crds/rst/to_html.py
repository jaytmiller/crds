"""Simple utility to convert a .rst file to corresponding HTML."""
import sys
import os.path

from docutils.core import publish_string

from crds.core import pysh

HERE = os.path.dirname(__file__) or "."

CSS = open(f"{HERE}/to_html.css").read()

HEAD_ADDITIONS = f"""
<style>
{CSS}
</style>
"""
 
def rst_to_html(rst, include_css=True):
    """Given .rst text `rst`,  generate corresponding HTML."""
    html = publish_string(source=rst,
                          settings_overrides={
                              'file_insertion_enabled': 0, 'raw_enabled': 0},
                          writer_name='html')
    html = html.decode('utf-8')
    if include_css:
        html = html.replace("</head>", HEAD_ADDITIONS + "\n</head>")
    return html
 
def main(rst_file):
    """Given a .rst file,  print the corresponding HTML to stdout."""
    pysh.usage("<rst_file>", 1, 1, "Format a .rst file as .html to stdout.")
    rst = open(rst_file).read()
    html = rst_to_html(rst)
    print(html)

if __name__ == "__main__":
    main(sys.argv[1])
