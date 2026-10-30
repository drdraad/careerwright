// MADE-UP EXAMPLE DATA for the spike only. These roles and skills are a small invented list for
// trying out the look of the world. They are not ESCO, not advice and not the product's catalogue.
// Every screen that uses them says so in plain words.

export type Skill = { readonly id: string; readonly label: string };

export type Role = {
  readonly id: string;
  readonly title: string;
  /** Plural used in the revelation sentence ("Chefs and firefighters share ..."). */
  readonly plural: string;
  readonly field: string;
  /** Essential skills, in the list's order. */
  readonly skills: readonly string[];
};

export const DATA_LABEL = "Made-up example data: a small invented list of jobs and skills.";

export const SKILLS: readonly Skill[] = [
  { id: "records", label: "Keep accurate records" },
  { id: "explain", label: "Explain things clearly" },
  { id: "calm", label: "Stay calm under pressure" },
  { id: "risks", label: "Spot risks to safety" },
  { id: "safety", label: "Follow safety rules" },
  { id: "wellbeing", label: "Look after people's wellbeing" },
  { id: "schedule", label: "Juggle a busy schedule" },
  { id: "budget", label: "Work out costs" },
  { id: "money", label: "Handle money" },
  { id: "spreadsheets", label: "Use spreadsheets" },
  { id: "patterns", label: "Find patterns in numbers" },
  { id: "reports", label: "Write clear reports" },
  { id: "lead", label: "Lead a small team" },
  { id: "coach", label: "Train new people" },
  { id: "customers", label: "Solve customers' problems" },
  { id: "complaints", label: "Handle complaints" },
  { id: "stock", label: "Plan stock and supplies" },
  { id: "driving", label: "Drive safely on busy roads" },
  { id: "routes", label: "Plan routes" },
  { id: "lifting", label: "Lift and move loads safely" },
  { id: "tools", label: "Use hand and power tools" },
  { id: "drawings", label: "Read technical drawings" },
  { id: "wiring", label: "Install and test wiring" },
  { id: "faults", label: "Track down faults" },
  { id: "measure", label: "Measure accurately" },
  { id: "hygiene", label: "Prepare food hygienically" },
  { id: "deadlines", label: "Work fast to tight deadlines" },
  { id: "firstaid", label: "Give first aid" },
  { id: "needs", label: "Work out what people need" },
  { id: "safeguarding", label: "Protect vulnerable people" },
  { id: "confidential", label: "Keep information private" },
  { id: "systems", label: "Use booking and records systems" },
  { id: "code", label: "Write software" },
  { id: "testing", label: "Test that things work" },
  { id: "visuals", label: "Design clear visuals" },
  { id: "present", label: "Present to a group" },
  { id: "negotiate", label: "Negotiate" },
  { id: "events", label: "Organise events" },
  { id: "lessons", label: "Plan lessons" },
  { id: "progress", label: "Check people's progress" },
  { id: "groups", label: "Keep a group on track" },
  { id: "coordinate", label: "Work with other teams" },
  { id: "quality", label: "Check work against standards" },
  { id: "equipment", label: "Look after equipment" },
  { id: "data", label: "Query data in databases" },
  { id: "interview", label: "Ask questions to find the facts" },
  { id: "requirements", label: "Turn needs into a clear plan" },
  { id: "emergency", label: "Follow emergency procedures" },
  { id: "sterile", label: "Keep things clean and sterile" },
  { id: "listen", label: "Listen carefully" },
  { id: "persuade", label: "Persuade people" },
];

const role = (
  id: string,
  title: string,
  plural: string,
  field: string,
  skills: readonly string[],
): Role => ({ id, title, plural, field, skills });

const HEALTH = "Health and care";
const EDUCATION = "Education";
const COMPUTING = "Data and computing";
const TRADES = "Building trades";
const TRANSPORT = "Transport and logistics";
const HOSPITALITY = "Food and hospitality";
const SHOPS = "Shops and customer service";
const OFFICE = "Office and finance";
const EMERGENCY = "Emergency services";
const CREATIVE = "Creative work";

export const ROLES: readonly Role[] = [
  role("care-worker", "Care worker", "Care workers", HEALTH, [
    "wellbeing", "safeguarding", "needs", "records", "explain", "calm", "firstaid", "confidential",
  ]),
  role("nurse", "Nurse", "Nurses", HEALTH, [
    "wellbeing", "firstaid", "needs", "records", "calm", "safeguarding", "confidential", "coordinate",
  ]),
  role("paramedic", "Paramedic", "Paramedics", HEALTH, [
    "driving", "calm", "firstaid", "needs", "risks", "safety", "records", "emergency",
  ]),
  role("pharmacy-assistant", "Pharmacy assistant", "Pharmacy assistants", HEALTH, [
    "customers", "records", "confidential", "stock", "money", "explain", "quality", "systems",
  ]),
  role("dental-nurse", "Dental nurse", "Dental nurses", HEALTH, [
    "sterile", "records", "confidential", "explain", "wellbeing", "equipment", "systems", "calm",
  ]),
  role("teaching-assistant", "Teaching assistant", "Teaching assistants", EDUCATION, [
    "wellbeing", "safeguarding", "needs", "explain", "groups", "progress", "records", "calm",
  ]),
  role("secondary-teacher", "Secondary school teacher", "Secondary school teachers", EDUCATION, [
    "lessons", "progress", "groups", "explain", "present", "safeguarding", "records", "reports",
  ]),
  role("nursery-worker", "Nursery worker", "Nursery workers", EDUCATION, [
    "wellbeing", "safeguarding", "groups", "firstaid", "needs", "explain", "hygiene", "progress",
  ]),
  role("data-analyst", "Data analyst", "Data analysts", COMPUTING, [
    "patterns", "spreadsheets", "data", "reports", "present", "requirements", "quality", "coordinate",
  ]),
  role("software-developer", "Software developer", "Software developers", COMPUTING, [
    "code", "testing", "faults", "requirements", "coordinate", "data", "quality", "present",
  ]),
  role("it-support", "IT support technician", "IT support technicians", COMPUTING, [
    "faults", "testing", "explain", "customers", "systems", "records", "safety", "equipment",
  ]),
  role("electrician", "Electrician", "Electricians", TRADES, [
    "wiring", "faults", "testing", "drawings", "safety", "risks", "tools", "equipment",
  ]),
  role("plumber", "Plumber", "Plumbers", TRADES, [
    "tools", "faults", "measure", "safety", "drawings", "customers", "risks", "testing",
  ]),
  role("carpenter", "Carpenter", "Carpenters", TRADES, [
    "tools", "measure", "drawings", "safety", "quality", "lifting", "risks", "stock",
  ]),
  role("bus-driver", "Bus driver", "Bus drivers", TRANSPORT, [
    "driving", "routes", "calm", "customers", "safety", "risks", "firstaid", "schedule",
  ]),
  role("delivery-driver", "Delivery driver", "Delivery drivers", TRANSPORT, [
    "driving", "routes", "lifting", "customers", "schedule", "deadlines", "safety", "calm",
  ]),
  role("warehouse-supervisor", "Warehouse supervisor", "Warehouse supervisors", TRANSPORT, [
    "lead", "stock", "safety", "lifting", "quality", "schedule", "coordinate", "records",
  ]),
  role("logistics-planner", "Logistics planner", "Logistics planners", TRANSPORT, [
    "routes", "schedule", "spreadsheets", "patterns", "coordinate", "budget", "reports", "requirements",
  ]),
  role("chef", "Chef", "Chefs", HOSPITALITY, [
    "hygiene", "deadlines", "calm", "lead", "stock", "safety", "equipment", "quality",
  ]),
  role("barista", "Barista", "Baristas", HOSPITALITY, [
    "hygiene", "customers", "money", "deadlines", "calm", "equipment", "listen", "complaints",
  ]),
  role("hotel-receptionist", "Hotel receptionist", "Hotel receptionists", HOSPITALITY, [
    "customers", "complaints", "systems", "money", "explain", "schedule", "confidential", "calm",
  ]),
  role("events-coordinator", "Events coordinator", "Events coordinators", HOSPITALITY, [
    "events", "budget", "schedule", "negotiate", "coordinate", "customers", "deadlines", "calm",
  ]),
  role("shop-supervisor", "Shop supervisor", "Shop supervisors", SHOPS, [
    "lead", "stock", "money", "customers", "complaints", "coach", "safety", "schedule",
  ]),
  role("customer-service-adviser", "Customer service adviser", "Customer service advisers", SHOPS, [
    "customers", "complaints", "systems", "explain", "calm", "records", "confidential", "listen",
  ]),
  role("sales-assistant", "Sales assistant", "Sales assistants", SHOPS, [
    "customers", "money", "stock", "explain", "persuade", "complaints", "systems", "listen",
  ]),
  role("bookkeeper", "Bookkeeper", "Bookkeepers", OFFICE, [
    "records", "spreadsheets", "money", "budget", "patterns", "confidential", "quality", "reports",
  ]),
  role("office-administrator", "Office administrator", "Office administrators", OFFICE, [
    "records", "systems", "schedule", "spreadsheets", "explain", "confidential", "coordinate", "reports",
  ]),
  role("hr-adviser", "HR adviser", "HR advisers", OFFICE, [
    "confidential", "interview", "explain", "records", "coach", "listen", "reports", "present",
  ]),
  role("firefighter", "Firefighter", "Firefighters", EMERGENCY, [
    "calm", "deadlines", "lead", "safety", "equipment", "firstaid", "emergency", "risks",
  ]),
  role("emergency-call-handler", "Emergency call handler", "Emergency call handlers", EMERGENCY, [
    "calm", "explain", "records", "systems", "confidential", "emergency", "needs", "listen",
  ]),
  role("graphic-designer", "Graphic designer", "Graphic designers", CREATIVE, [
    "visuals", "requirements", "present", "deadlines", "customers", "quality", "coordinate", "interview",
  ]),
];

export const skillLabel = (id: string): string => {
  const skill = SKILLS.find((s) => s.id === id);
  if (!skill) throw new Error(`Unknown skill id in the example data: ${id}`);
  return skill.label;
};
