import { HOME_VARIABLE, newHome, stack } from "./stack";

// A fresh stack for every run: remove any leftover test project, build the images from this
// checkout, then start in demo mode (no Careerwright service has a route out of the machine).
export default function globalSetup(): void {
  process.env[HOME_VARIABLE] = newHome();
  stack("down");
  stack("build");
  stack("demo");
}
