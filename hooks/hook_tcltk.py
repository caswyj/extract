"""
PyInstaller runtime hook for Tcl/Tk on macOS.

This sets up the correct Tcl/Tk library paths when running from a bundled app.
"""

import os
import sys

# Only needed for macOS
if sys.platform == 'darwin':
    # When running from a bundled app
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS

        # Set Tcl/Tk library paths
        tcl_lib = os.path.join(bundle_dir, 'tcltk', 'tcl8.6')
        tk_lib = os.path.join(bundle_dir, 'tcltk', 'tk8.6')

        if os.path.exists(tcl_lib):
            os.environ['TCL_LIBRARY'] = tcl_lib
        if os.path.exists(tk_lib):
            os.environ['TK_LIBRARY'] = tk_lib
