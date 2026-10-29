"""Setup places the Adzuna credentials from `.env` under NESSA_HOME for the acquisition
worker only (ruling R4; controller ruling for Task 7A): owner-only files, read in code,
never echoed; an absent name is reported, never guessed. The names are the product owner's,
`ADZUNA_APPLICATION_ID` and `ADZUNA_API_KEY` (controller ruling, fix round 5), with no
alias for the names Task 7A first used."""

import stat
from pathlib import Path

import pytest

from nessa.acquisition import load_adzuna_credentials
from tools.localenv import (
    adzuna_configured,
    ensure_local_home,
    place_adzuna_credentials,
)

APP_ID = "id-not-a-real-0001"
APP_KEY = "key-not-a-real-abcdefabcdef"


def env(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "dotenv"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.req("MODEL-06")
def test_both_credentials_are_placed_owner_only_and_never_returned(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "home"
    ensure_local_home(home)
    dotenv = env(
        tmp_path,
        f"META_API_KEY=x\nADZUNA_APPLICATION_ID={APP_ID}\nexport ADZUNA_API_KEY='{APP_KEY}'\n",
    )

    said = place_adzuna_credentials(home, dotenv)

    assert said == "placed in NESSA_HOME/adzuna"
    assert (home / "adzuna" / "adzuna_application_id").read_text() == APP_ID
    assert (home / "adzuna" / "adzuna_api_key").read_text() == APP_KEY
    for path in (home / "adzuna", *(home / "adzuna").iterdir()):
        assert path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO) == 0
    assert adzuna_configured(home)
    printed = capsys.readouterr()
    assert APP_KEY not in printed.out + printed.err
    assert APP_KEY not in said
    assert not (home / "adzuna" / "META_API_KEY").exists()  # only Adzuna's two names


@pytest.mark.req("MODEL-06")
def test_the_acquisition_worker_reads_the_files_setup_places(tmp_path: Path) -> None:
    # The two sides of one contract: what `make setup` writes is what the worker loads.
    home = tmp_path / "home"
    ensure_local_home(home)
    place_adzuna_credentials(
        home, env(tmp_path, f"ADZUNA_APPLICATION_ID={APP_ID}\nADZUNA_API_KEY={APP_KEY}\n")
    )

    loaded = load_adzuna_credentials(home / "adzuna")

    assert loaded is not None
    assert [secret.get_secret_value() for secret in loaded] == [APP_ID, APP_KEY]


@pytest.mark.req("MODEL-06")
def test_a_changed_credential_replaces_the_placed_one(tmp_path: Path) -> None:
    home = tmp_path / "home"
    ensure_local_home(home)
    place_adzuna_credentials(
        home, env(tmp_path, f"ADZUNA_APPLICATION_ID={APP_ID}\nADZUNA_API_KEY=old\n")
    )

    place_adzuna_credentials(
        home, env(tmp_path, f"ADZUNA_APPLICATION_ID={APP_ID}\nADZUNA_API_KEY={APP_KEY}\n")
    )

    assert (home / "adzuna" / "adzuna_api_key").read_text() == APP_KEY


@pytest.mark.parametrize(
    "text",
    [
        "",
        "ADZUNA_APPLICATION_ID=only-the-id\n",
        "ADZUNA_ID=x\nADZUNA_KEY=y\n",
        "ADZUNA_API_KEY=\n",
        "ADZUNA_APP_ID=x\nADZUNA_APP_KEY=y\n",  # the names Task 7A first used: no alias
    ],
)
def test_a_missing_name_is_reported_blocked_and_nothing_is_placed(
    tmp_path: Path, text: str
) -> None:
    home = tmp_path / "home"
    ensure_local_home(home)

    said = place_adzuna_credentials(home, env(tmp_path, text))

    assert said.startswith("blocked: Adzuna credentials not found")
    assert not adzuna_configured(home)
