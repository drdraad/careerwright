"""The committed ESCO sample (`fixtures/esco-sample/`), pinned like the real release.

Tests import this reduced subset of ESCO v1.2.1, so they need no network. It is labelled a
sample in its pin and in the database (`taxonomy_releases.sample`); the product imports
only `nessa.catalogue.esco.ESCO_RELEASE`.
"""

import dataclasses

from nessa.catalogue.esco import ESCO_RELEASE
from nessa.catalogue.releases import ReleasePin
from tools.localenv import REPO_ROOT

SAMPLE_DIR = REPO_ROOT / "fixtures" / "esco-sample"
SAMPLE_RELEASE: ReleasePin = dataclasses.replace(
    ESCO_RELEASE,
    dataset_id="esco-v1.2.1-en-csv-sample",
    url="fixtures/esco-sample/esco-v1.2.1-en-csv-sample.zip",
    file_name="esco-v1.2.1-en-csv-sample.zip",
    sha256="747c5638653e0594c0ae4210db1ee0c90eccb5c872f356fdfa36116bb56f955d",
    size_bytes=76_049,
    native_code_version="ESCO v1.2.1 (occupations grouped by ISCO-08); test sample subset",
    sample=True,
)
SAMPLE_PATH = SAMPLE_DIR / SAMPLE_RELEASE.file_name
