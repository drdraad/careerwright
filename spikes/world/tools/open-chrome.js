// Vite runs this (BROWSER=tools/open-chrome.js) with the address as the last argument. It opens
// the spike in Google Chrome, the browser everything was checked and measured in, rather than the
// computer's default browser.
import { execFile } from "node:child_process";

const url = process.argv.at(-1) ?? "http://127.0.0.1:53300/";
execFile("open", ["-a", "Google Chrome", url], (error) => {
  if (error) console.log(`Google Chrome didn't open. Open ${url} in Google Chrome.`);
});
