"""Automated architecture checks (Global Constraint 3, ARC1-09, ARC1-01, BND1-13).

- No circular imports, between modules or between top-level packages.
- Vendor and SQL libraries are imported only by the adapter modules listed here. Every other
  module is domain or application code and may use only the standard library, pydantic and
  other Nessa modules. Adding an adapter means adding it to `ADAPTERS`, which a reviewer sees.
- The lockfile contains none of the excluded technologies.
- Compose publishes ports on 127.0.0.1 only.
"""

import ast
import re
import tomllib
from collections import defaultdict
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
BACKEND = SRC.parent
REPO = BACKEND.parent

VENDORS = frozenset(
    {
        "sqlalchemy",
        "psycopg",
        "alembic",
        "dbos",
        "pydantic_ai",
        "openai",
        "httpx",
        "httpx2",
        "httpcore",
        "httpcore2",
        "certifi",
        "scrapling",
        "lxml",
        "fastapi",
        "starlette",
        "uvicorn",
        "anyio",
        "firebase_admin",
        "google",
        "cryptography",
    }
)
# Module (or package prefix ending in ".") -> the vendor packages it may import.
ADAPTERS: dict[str, frozenset[str]] = {
    "nessa.db": frozenset({"sqlalchemy"}),
    "nessa.cli": frozenset({"sqlalchemy", "alembic", "dbos"}),
    "nessa.migrations.": frozenset({"alembic"}),
    "nessa.identity.store": frozenset({"sqlalchemy"}),
    "nessa.identity.credential_store": frozenset({"sqlalchemy"}),
    "nessa.identity.run_store": frozenset({"sqlalchemy"}),
    "nessa.profile.store": frozenset({"sqlalchemy"}),
    "nessa.profile.interview_store": frozenset({"sqlalchemy"}),
    "nessa.profile.explanation_store": frozenset({"sqlalchemy"}),
    "nessa.catalogue.taxonomy_store": frozenset({"sqlalchemy"}),
    "nessa.catalogue.reference_store": frozenset({"sqlalchemy"}),  # Task 7 slice B, ADR 0010
    "nessa.capability.store": frozenset({"sqlalchemy"}),  # Task 9, ADR 0012
    "nessa.identity.keyring": frozenset({"cryptography"}),
    "nessa.identity.firebase": frozenset({"firebase_admin"}),
    "nessa.identity.meta": frozenset({"httpx2", "openai", "pydantic_ai"}),
    "nessa.identity.failures": frozenset({"pydantic_ai"}),
    "nessa.identity.activity": frozenset({"pydantic_ai"}),
    "nessa.identity.workflow": frozenset({"dbos"}),
    "nessa.identity.worker": frozenset({"dbos"}),
    "nessa.profile.interview_agent": frozenset({"pydantic_ai"}),
    "nessa.profile.discovery_agent": frozenset({"pydantic_ai"}),
    "nessa.profile.slate_explanation_agent": frozenset({"pydantic_ai"}),
    "nessa.worker": frozenset({"pydantic_ai"}),
    # Evidence and acquisition (Task 7, ADR 0009): the guarded HTTP client and the parser.
    "nessa.evidence.fetcher": frozenset({"httpcore2", "certifi"}),
    "nessa.evidence.pages": frozenset({"scrapling"}),
    "nessa.evidence.store": frozenset({"sqlalchemy"}),
    "nessa.evidence.workflow": frozenset({"dbos"}),
    "nessa.evidence.search_agent": frozenset({"pydantic_ai"}),
    "nessa.evidence.extraction_agent": frozenset({"pydantic_ai"}),  # fix round 2, ruling 10
    "nessa.api.": frozenset({"fastapi", "starlette", "anyio"}),
}
EXCLUDED_PACKAGES = frozenset(
    {
        "ortools",  # CP-SAT
        "pyo3",
        "maturin",
        "temporalio",
        "redis",
        "geoalchemy2",
        "pgvector",
        "chromadb",
        "qdrant-client",
        "pinecone",
        "pinecone-client",
        "weaviate-client",
        "faiss-cpu",
        "sentence-transformers",
        "lancedb",
        "celery",
        "playwright",  # no browser automation in the backend (spec section 6)
    }
)


def modules() -> dict[str, Path]:
    found = {}
    for path in SRC.rglob("*.py"):
        parts = list(path.relative_to(SRC).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        found[".".join(parts)] = path
    return found


def imports(name: str, path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package = name if path.name == "__init__.py" else name.rpartition(".")[0]
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.rsplit(".", node.level - 1)[0] if node.level > 1 else package
                module = f"{base}.{node.module}" if node.module else base
            else:
                module = node.module or ""
            names.add(module)
            names.update(f"{module}.{alias.name}" for alias in node.names)
    return names


def nessa_graph() -> dict[str, set[str]]:
    known = modules()
    return {
        name: {target for target in imports(name, path) if target in known and target != name}
        for name, path in known.items()
    }


def cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    found: list[list[str]] = []

    def visit(node: str) -> None:
        index[node] = low[node] = len(index)
        stack.append(node)
        on_stack.add(node)
        for target in graph.get(node, ()):
            if target not in index:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in on_stack:
                low[node] = min(low[node], index[target])
        if low[node] == index[node]:
            component = []
            while True:
                member = stack.pop()
                on_stack.discard(member)
                component.append(member)
                if member == node:
                    break
            if len(component) > 1:
                found.append(sorted(component))

    for node in sorted(graph):
        if node not in index:
            visit(node)
    return found


def package_of(module: str) -> str:
    parts = module.split(".")
    return ".".join(parts[:2])


def test_the_cycle_detector_finds_direct_and_indirect_cycles() -> None:
    graph = {"a": {"b"}, "b": {"c"}, "c": {"a"}, "d": {"a"}, "e": {"e2"}, "e2": {"e"}}

    assert sorted(cycles(graph)) == [["a", "b", "c"], ["e", "e2"]]


@pytest.mark.req("ARC1-09")
def test_no_module_imports_form_a_cycle() -> None:
    assert cycles(nessa_graph()) == []


@pytest.mark.req("ARC1-09")
def test_no_top_level_packages_import_each_other_in_a_cycle() -> None:
    packages: dict[str, set[str]] = defaultdict(set)
    for source, targets in nessa_graph().items():
        packages[package_of(source)].update(
            package_of(t) for t in targets if package_of(t) != package_of(source)
        )

    assert cycles(dict(packages)) == []


def allowed_vendors(module: str) -> frozenset[str]:
    for prefix, vendors in ADAPTERS.items():
        if module == prefix or (prefix.endswith(".") and module.startswith(prefix)):
            return vendors
    return frozenset()


@pytest.mark.req("ARC1-09")
def test_vendor_and_sql_libraries_appear_only_in_listed_adapters() -> None:
    violations = []
    for name, path in modules().items():
        used = {target.split(".")[0] for target in imports(name, path)} & VENDORS
        extra = used - allowed_vendors(name)
        if extra:
            violations.append(f"{name} imports {sorted(extra)}")

    assert violations == []


def test_the_adapter_list_names_only_modules_that_exist() -> None:
    known = modules()
    for prefix in ADAPTERS:
        assert any(name == prefix or name.startswith(prefix) for name in known), prefix


@pytest.mark.req("ARC1-01")
def test_the_lockfile_holds_none_of_the_excluded_technologies() -> None:
    lock = tomllib.loads((BACKEND / "uv.lock").read_text(encoding="utf-8"))
    locked = {package["name"] for package in lock["package"]}

    assert locked & EXCLUDED_PACKAGES == set()


# The same exclusions for JavaScript (spec ARC-1, GC2): no other renderer (PixiJS, three.js),
# workflow engine, Redis, vector database, embedding model, agent platform or scraping
# browser. Playwright stays allowed: it is the plan's browser-test tool, never product code.
EXCLUDED_JS_PACKAGES = frozenset(
    {
        "pixi.js",
        "three",
        "redis",
        "ioredis",
        "pgvector",
        "chromadb",
        "weaviate-client",
        "weaviate-ts-client",
        "faiss-node",
        "langchain",
        "llamaindex",
        "puppeteer",
        "puppeteer-core",
        "or-tools",
    }
)
EXCLUDED_JS_SCOPES = (
    "@pixi/",
    "@temporalio/",
    "@redis/",
    "@qdrant/",
    "@pinecone-database/",
    "@langchain/",
    "@xenova/",
    "@huggingface/",
)
PNPM_LOCKS = ("apps/web/pnpm-lock.yaml", "docs/design/pnpm-lock.yaml", "docker/auth/pnpm-lock.yaml")


def pnpm_locked_names(path: Path) -> set[str]:
    """Package names under `packages:` in a pnpm v9 lockfile (`  name@version:` keys)."""
    names: set[str] = set()
    in_packages = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if not line.startswith(" "):
            in_packages = line.rstrip() == "packages:"
            continue
        key = re.match(r"^  '?(@?[^@\s']+)@", line)
        if in_packages and key:
            names.add(key.group(1))
    return names


@pytest.mark.req("ARC1-01")
def test_the_pnpm_lock_reader_finds_scoped_and_plain_names(tmp_path: Path) -> None:
    lock = tmp_path / "pnpm-lock.yaml"
    lock.write_text(
        "lockfileVersion: '9.0'\nimporters:\n  .:\n    dependencies:\n      x: 1\n"
        "packages:\n\n  '@pixi/core@8.0.0':\n    resolution: {}\n\n  react@19.3.0:\n"
        "    resolution: {}\nsnapshots:\n  three@1.0.0: {}\n",
        encoding="utf-8",
    )

    assert pnpm_locked_names(lock) == {"@pixi/core", "react"}


@pytest.mark.req("ARC1-01", "ARC1-03")
@pytest.mark.parametrize("lock", PNPM_LOCKS)
def test_the_javascript_lockfiles_hold_none_of_the_excluded_technologies(lock: str) -> None:
    names = pnpm_locked_names(REPO / lock)
    excluded = {n for n in names if n in EXCLUDED_JS_PACKAGES or n.startswith(EXCLUDED_JS_SCOPES)}

    assert len(names) > 0, f"{lock} has no packages: the reader is broken"
    assert excluded == set()


def import_closure(root: str) -> tuple[set[str], set[str]]:
    """(Nessa modules, vendor packages) that `root` imports, transitively."""
    known = modules()
    seen: set[str] = set()
    vendors: set[str] = set()
    pending = [root]
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        found = imports(name, known[name])
        vendors |= {target.split(".")[0] for target in found} & VENDORS
        pending.extend(t for t in found if t in known and t not in seen)
    return seen, vendors


@pytest.mark.req("ACQ-05")
def test_the_acquisition_worker_cannot_reach_a_database_key_model_or_profile() -> None:
    # Global Constraint 8: the restricted acquisition worker holds no user secret, model key,
    # master key or private profile store. Its code cannot even reach one.
    reached, vendors = import_closure("nessa.acquisition")

    assert vendors <= {"httpcore2", "certifi", "scrapling"}
    forbidden = [
        m
        for m in reached
        if m in ("nessa.db", "nessa.identity.keyring", "nessa.identity.meta", "nessa.worker")
        or m.startswith(("nessa.profile", "nessa.identity.credential", "nessa.api"))
        or m.endswith("store")
    ]
    assert forbidden == []


@pytest.mark.req("ACQ-05")
def test_the_acquisition_worker_has_no_setting_for_a_database_key_or_model() -> None:
    from nessa.acquisition import AcquisitionSettings

    assert set(AcquisitionSettings.model_fields) == {
        "environment",
        "port",
        "adzuna_credentials_dir",
    }


def published_ports(path: Path) -> list[str]:
    """Every list item under a `ports:` key (block style, as our compose files use)."""
    entries: list[str] = []
    ports_indent: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if ports_indent is not None and indent > ports_indent and stripped.startswith("- "):
            entries.append(stripped[2:].strip().strip("\"'"))
            continue
        ports_indent = indent if re.match(r"^ports:\s*$", stripped) else None
        if re.match(r"^ports:\s*\S", stripped):
            raise AssertionError(f"{path.name}: write ports as a block list so they are checked")
    return entries


@pytest.mark.req("BND1-13")
def test_compose_publishes_ports_on_loopback_only() -> None:
    published = [
        port for path in sorted(REPO.glob("compose*.yaml")) for port in published_ports(path)
    ]

    assert len(published) == 4, published  # the edge's four relays
    assert [p for p in published if not p.startswith("127.0.0.1:")] == []
