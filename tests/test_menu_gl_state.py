# The real-driver test supersedes the old call-recording-only blit test.
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('test_menu_copy_ec.py')),run_name='__main__')
