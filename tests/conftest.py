"""
Shared pytest setup: point StudyVault at a throwaway database so tests never touch studyvault.db.
"""

import os
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="studyvault-tests-")
os.environ["STUDYVAULT_DB"] = os.path.join(_tmp_dir, "test.db")
