"""Write the API's OpenAPI document (the one `/openapi.json` serves) to standard output.

The web app generates its TypeScript client from this document and commits both
(`apps/web/src/generated/`); `make check` fails when either drifts. Run from `backend/`:
`uv run --locked python -m tools.openapi > ../apps/web/src/generated/openapi.json`.
"""

import json
import sys

from careerwright.api.app import openapi_document


def render() -> str:
    return json.dumps(openapi_document(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    sys.stdout.write(render())


if __name__ == "__main__":
    main()
