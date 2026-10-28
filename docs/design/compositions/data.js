// Data for the Sprint 0 design compositions.
//
// FIXTURES holds values copied from fixtures/m0 (TRACE-01, P01, P02) and
// fixtures/reconstructed/directai.json. tools/check-fixture-data.mjs asserts that every
// copied value equals the fixture files; `pnpm run screenshots` runs it first.
//
// DESIGN_LISTINGS is invented for the design review only. The fixture pack has no job
// postings, so every employer, listing and salary below is synthetic and labelled so on
// the page. None is a real organisation, vacancy or pay figure.
window.NESSA = {
  FIXTURES: {
    trace01: {
      id: "TRACE-01",
      targetTitle: "Data quality analyst",
      region: "Manchester, England",
      planningStart: "2027-01-01",
      horizonMonths: 6,
      baselineIncomeByMonthMinor: [200000, 200000, 200000, 200000, 200000, 200000],
      livingByMonthMinor: [100000, 100000, 100000, 100000, 100000, 100000],
      openingCashMinor: 600000,
      reserveMinor: 50000,
      admissionCompletedOn: "2026-12-15",
      routes: [
        { id: "A", familyId: "fixture:family:A", timeMonths: 2, directMinor: 120000, economicMinor: 520000,
          paymentsMinor: [120000, 0, 0, 0, 0, 0], incomeMinor: [0, 0, 200000, 200000, 200000, 200000],
          start: "2027-01-01", finish: "2027-02-28", studyHours: 40, workHoursWhileActive: 0 },
        { id: "B", familyId: "fixture:family:B", timeMonths: 4, directMinor: 60000, economicMinor: 60000,
          paymentsMinor: [15000, 15000, 15000, 15000, 0, 0], incomeMinor: [200000, 200000, 200000, 200000, 200000, 200000],
          start: "2027-01-01", finish: "2027-04-30", studyHours: 6, workHoursWhileActive: 30 },
        { id: "C", familyId: "fixture:family:C", timeMonths: 3, directMinor: 70000, economicMinor: 220000,
          paymentsMinor: [30000, 20000, 20000, 0, 0, 0], incomeMinor: [150000, 150000, 150000, 200000, 200000, 200000],
          start: "2027-01-01", finish: "2027-03-31", studyHours: 16, workHoursWhileActive: 20 },
        { id: "D", familyId: "fixture:family:D", timeMonths: 4, directMinor: 110000, economicMinor: 110000,
          paymentsMinor: [27500, 27500, 27500, 27500, 0, 0], incomeMinor: [200000, 200000, 200000, 200000, 200000, 200000],
          start: "2027-01-01", finish: "2027-04-30", studyHours: 6, workHoursWhileActive: 30 },
        { id: "E", familyId: "fixture:family:E", timeMonths: 5, directMinor: 130000, economicMinor: 130000,
          paymentsMinor: [26000, 26000, 26000, 26000, 26000, 0], incomeMinor: [200000, 200000, 200000, 200000, 200000, 200000],
          start: "2027-01-01", finish: "2027-05-31", studyHours: 4, workHoursWhileActive: 30 },
      ],
      fronts: [["A", "B", "C"], ["D"], ["E"]],
      selectedRoute: "B",
      print: { timeMonths: 4, directMinor: 60000, economicMinor: 60000, peakPaymentMinor: 15000,
        minimumPrefundedCashMinor: 485000, horizonMonths: 6 },
      availableWeeklyHours: 40,
      weeklyWorkAfterCompletion: 30,
      aiScore: { range: [5, 8], minimumFilter: 6, lowerBoundFilterPasses: false, synthetic: true },
      syllabusText: "Learners independently query two related tables, validate keys and missing values, and submit an assessed report with reproducible checks.",
    },
    p01: {
      cities: ["Manchester"],
      targetTitles: ["Data quality analyst"],
      enjoyedTasks: ["finding inconsistencies", "explaining evidence"],
      preferredEnvironment: ["structured", "collaborative"],
      currentNetIncomeMinor: 200000,
      livingMinor: 100000,
      openingCashMinor: 600000,
      reserveMinor: 50000,
      directSpendCapMinor: 150000,
      monthlyPaymentCapMinor: 150000,
      weeklyTotalAvailabilityHours: 40,
    },
    p02: {
      cities: ["Leeds", "Manchester"],
      enjoyedTasks: ["repairing physical objects", "working outdoors"],
      preferredEnvironment: ["practical", "small team"],
      incomeBaselineStatus: "unconfirmed",
      weeklyStudyHours: 12,
    },
    directai: {
      id: "DIRECTAI",
      routes: [
        { id: "A", timeMonths: 6, directMinor: 480000, layer: 1 },
        { id: "B", timeMonths: 9, directMinor: 240000, layer: 1 },
        { id: "C", timeMonths: 12, directMinor: 90000, layer: 1 },
        { id: "D", timeMonths: 8, directMinor: 540000, layer: 2 },
        { id: "E", timeMonths: 11, directMinor: 300000, layer: 2 },
        { id: "F", timeMonths: 14, directMinor: 120000, layer: 2 },
        { id: "G", timeMonths: 10, directMinor: 620000, layer: 3 },
        { id: "H", timeMonths: 13, directMinor: 360000, layer: 3 },
        { id: "I", timeMonths: 16, directMinor: 160000, layer: 3 },
      ],
    },
  },

  // Synthetic, design-only. Industry keys map to tokens: finance=blue, health=coral,
  // retail=amber, technology=violet, public=olive, other=other.
  DESIGN_LISTINGS: {
    areas: [
      { id: "manchester", label: "Manchester", note: "Greater Manchester, England" },
      { id: "leeds", label: "Leeds", note: "West Yorkshire, England" },
      { id: "remote", label: "Remote", note: "Employed in England, UK hours" },
    ],
    companies: [
      { id: "kestrel", area: "manchester", name: "Kestrel Lane Insurance Services", industry: "finance" },
      { id: "northmoor", area: "manchester", name: "Northmoor Clinical Records Partnership", industry: "health" },
      { id: "copperfield", area: "manchester", name: "Copperfield & Vane Retail Group", industry: "retail" },
      { id: "ashgrove", area: "manchester", name: "Ashgrove Tenancy and Housing Association", industry: "public" },
      { id: "tessellate", area: "manchester", name: "Tessellate Data Engineering", industry: "technology" },
      { id: "hollinbrook", area: "leeds", name: "Hollin Brook Mutual Building Society", industry: "finance" },
      { id: "ridings", area: "leeds", name: "Three Ridings Freight and Fulfilment", industry: "other" },
      { id: "kirkgate", area: "leeds", name: "Kirkgate Community Health Services", industry: "health" },
      { id: "fenwick", area: "remote", name: "Fenwick Hart Recruitment", industry: "other", agency: true },
      { id: "lumen", area: "remote", name: "Lumen Ledger Software", industry: "technology" },
    ],
    // pay: { kind: "advertised" | "predicted" | "unknown", min, max } in whole pounds a year, gross.
    jobs: [
      { id: "j1", company: "kestrel", title: "Data quality analyst, customer and policy records", mode: "hybrid", pay: { kind: "advertised", min: 32000, max: 36000 }, ai: "range", postedDays: 6, copies: 2 },
      { id: "j2", company: "kestrel", title: "Senior data quality and governance analyst (financial crime and customer due diligence)", mode: "hybrid", pay: { kind: "advertised", min: 42000, max: 48000 }, ai: "range", postedDays: 2, copies: 1 },
      { id: "j3", company: "northmoor", title: "Data quality analyst, clinical records migration (12-month fixed term)", mode: "onsite", pay: { kind: "advertised", min: 30500, max: 33500 }, ai: "range", postedDays: 9, copies: 3 },
      { id: "j4", company: "northmoor", title: "Information and data quality officer", mode: "hybrid", pay: { kind: "unknown" }, ai: "range", postedDays: 4, copies: 1 },
      { id: "j5", company: "copperfield", title: "Master data analyst, product and supplier information", mode: "onsite", pay: { kind: "predicted", min: 29000, max: 34000 }, ai: "unscored", postedDays: 11, copies: 2 },
      { id: "j6", company: "copperfield", title: "Junior data analyst, reconciliation and stock reporting", mode: "onsite", pay: { kind: "advertised", min: 26000, max: 28500 }, ai: "range", postedDays: 1, copies: 1 },
      { id: "j7", company: "ashgrove", title: "Data quality officer (hybrid, two days a week in Salford)", mode: "hybrid", pay: { kind: "advertised", min: 31200, max: 31200 }, ai: "range", postedDays: 14, copies: 1 },
      { id: "j8", company: "tessellate", title: "Data quality engineer, pipeline testing and validation", mode: "hybrid", pay: { kind: "predicted", min: 38000, max: 45000 }, ai: "unscored", postedDays: 5, copies: 2 },
      { id: "j9", company: "hollinbrook", title: "Data quality analyst, mortgage and savings data", mode: "hybrid", pay: { kind: "advertised", min: 33000, max: 37000 }, ai: "range", postedDays: 3, copies: 2 },
      { id: "j10", company: "hollinbrook", title: "Regulatory reporting data analyst", mode: "onsite", pay: { kind: "unknown" }, ai: "unscored", postedDays: 8, copies: 1 },
      { id: "j11", company: "ridings", title: "Inventory data quality coordinator", mode: "onsite", pay: { kind: "advertised", min: 27000, max: 30000 }, ai: "range", postedDays: 12, copies: 1 },
      { id: "j12", company: "kirkgate", title: "Clinical coding and data quality analyst", mode: "hybrid", pay: { kind: "unknown" }, ai: "range", postedDays: 6, copies: 1 },
      { id: "j13", company: "fenwick", title: "Data quality analyst, 6-month contract", mode: "remote", pay: { kind: "unknown" }, ai: "range", postedDays: 2, copies: 4 },
      { id: "j14", company: "lumen", title: "Customer data quality specialist", mode: "remote", pay: { kind: "advertised", min: 35000, max: 40000 }, ai: "range", postedDays: 7, copies: 1 },
      { id: "j15", company: "lumen", title: "Data steward, accounting integrations", mode: "remote", pay: { kind: "predicted", min: 33000, max: 39000 }, ai: "unscored", postedDays: 10, copies: 1 },
    ],
    selectedJob: "j1",
    totals: { found: 24, afterDedupe: 15, duplicatesRemoved: 9, sourcesChecked: 4 },
  },
};
