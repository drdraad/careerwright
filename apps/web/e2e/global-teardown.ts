import { rmSync } from "node:fs";
import { HOME_VARIABLE, stack } from "./stack";

// Removes the test project's containers, network and volumes; the default stack is untouched
// (`down` refuses the default project).
export default function globalTeardown(): void {
  stack("down");
  const home = process.env[HOME_VARIABLE];
  if (home !== undefined) rmSync(home, { recursive: true, force: true });
}
