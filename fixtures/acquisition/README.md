# Acquisition fixtures (synthetic)

**Every file here is synthetic.** None is a real advert, employer, salary or Adzuna
response, and none is evidence (Global Constraint 5). They are the fixture contract the
acquisition adapters are tested against (plan section 3: "A fixture adapter must satisfy the
same failure and provenance contract as a live adapter, with its synthetic origin retained").

| File | What it stands for | Shape taken from |
|---|---|---|
| `adzuna-search-gb.json` | One page of an Adzuna `GET /v1/api/jobs/gb/search/{page}` response: an advertised salary (`salary_is_predicted` `"0"`), a predicted one (`"1"`), one with no flag, one with no salary, two agency adverts at different levels, and a snippet of the employer advert the page tests use (`backend/tests/domain/test_pages.py`); its `count` (128) exceeds the six results, so a search over it is a partial result | <https://developer.adzuna.com/docs/search>, read 2026-10-28 (`results[]` with `id`, `title`, `description`, `created`, `redirect_url`, `company.display_name`, `location.display_name` and `area`, `salary_min`, `salary_max`, `salary_is_predicted`, `contract_type`, `contract_time`; `count`) |

Employer names use reserved `.example` domains. Adzuna's documentation does not say
whether `salary_min` and `salary_max` are annual, so the adapter records no period for them.
