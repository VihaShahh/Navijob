import assert from "node:assert/strict";
import { connectBrowser } from "./browser-client.mjs";

const browser = await connectBrowser();
const { call, evaluate, until, navigate, fill, click } = browser;
const results = [];
async function inspect(path, text) {
  await navigate(path, text);
  await until('!!document.querySelector("main") && !document.querySelector(".loading-state")', path);
  const tree = await call("Accessibility.getFullAXTree");
  const unnamed = tree.nodes.filter(node => !node.ignored && ["button", "link", "textbox", "combobox", "checkbox"].includes(node.role?.value) && !node.name?.value?.trim());
  assert.equal(unnamed.length, 0, `${path}: controls need accessible names`);
  const contrast = await evaluate(`(() => {
    const rgb = value => (value.match(/[\\d.]+/g) || []).slice(0,3).map(Number);
    const luminance = values => values.map(value => { value /= 255; return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4; }).reduce((sum,value,index) => sum + value * [.2126,.7152,.0722][index], 0);
    const failures = []; let checked = 0;
    const walk = document.createTreeWalker(document.querySelector('main'), NodeFilter.SHOW_TEXT);
    while (walk.nextNode()) {
      const text = walk.currentNode; const element = text.parentElement;
      if (!text.textContent.trim() || !element.getClientRects().length || element.closest(':disabled, script, style')) continue;
      const style = getComputedStyle(element);
      if (style.visibility !== 'visible') continue;
      let parent = element; let background = 'rgb(255,255,255)';
      while (parent) { const color = getComputedStyle(parent).backgroundColor; if (!['transparent','rgba(0, 0, 0, 0)'].includes(color)) { background = color; break; } parent = parent.parentElement; }
      const foregroundLum = luminance(rgb(style.color)); const backgroundLum = luminance(rgb(background));
      const ratio = (Math.max(foregroundLum,backgroundLum) + .05) / (Math.min(foregroundLum,backgroundLum) + .05);
      const size = parseFloat(style.fontSize); const large = size >= 24 || (size >= 18.66 && parseInt(style.fontWeight) >= 700);
      checked++;
      if (ratio + .01 < (large ? 3 : 4.5)) failures.push({text:text.textContent.trim().slice(0,60), ratio:ratio.toFixed(2), foreground:style.color, background});
    }
    return {checked, failures};
  })()`);
  assert.deepEqual(contrast.failures, [], `${path}: text contrast`);
  for (const width of [390, 1440]) {
    await call("Emulation.setDeviceMetricsOverride", { width, height: 1000, deviceScaleFactor: 1, mobile: width === 390 });
    await new Promise(resolve => setTimeout(resolve, 100));
    assert.equal(await evaluate(`document.documentElement.scrollWidth <= ${width + 1} && innerWidth <= ${width + 1}`), true, `${path}: overflow at ${width}`);
  }
  results.push({ path, named_controls: tree.nodes.filter(node => !node.ignored && ["button", "link", "textbox", "combobox", "checkbox"].includes(node.role?.value)).length, contrast_nodes: contrast.checked });
}
async function login(role, destination) {
  await call("Network.clearBrowserCookies");
  await navigate("/login", "Good to see you again.");
  await fill("email", `${role}@sample.navijob.test`); await fill("password", process.env.NAVIJOB_SAMPLE_PASSWORD || "NaviJob-Preview-42!"); await click("Sign in ↗");
  await until(`location.pathname === ${JSON.stringify(destination)} && !!document.querySelector('.workspace-main')`, role);
}
try {
  await call("Network.clearBrowserCookies"); await call("Network.clearBrowserCache");
  await call("Accessibility.enable"); await call("Network.enable");
  await inspect("/", "Less paperwork");
  await navigate("/");
  await call("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
  await call("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
  assert.equal(await evaluate('document.activeElement.textContent.trim()'), "Skip to content", "first keyboard stop");
  assert.equal(await evaluate('getComputedStyle(document.activeElement).outlineStyle'), "solid", "visible keyboard focus");
  await call("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  await call("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  await until('document.activeElement.id === "main"', "skip link target");
  await call("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  assert.equal(await evaluate('getComputedStyle(document.documentElement).scrollBehavior'), "auto", "reduced motion");
  await call("Emulation.setEmulatedMedia", { features: [] });
  await inspect("/jobs", "Sample Engineer");
  await inspect("/jobs/sample-sprout-engineer", "Posting source");
  await inspect("/jobs/sample-sprout-closed", "This role is closed");
  await inspect("/companies/sample-sprout-studio", "What the labels mean");
  await inspect("/privacy", "Privacy and data handling");
  await inspect("/terms", "Preview terms");
  await inspect("/for-employers", "your next teammate.");
  await call("Network.setBlockedURLs", { urls: ["*localhost:3100/api/jobs/*"] });
  await navigate("/jobs", "Try again");
  await call("Network.setBlockedURLs", { urls: [] }); await click("Try again");
  await until('document.body.innerText.includes("Sample Engineer")', "discovery failure recovery");
  await login("candidate", "/candidate");
  assert.equal(await evaluate(`fetch('/api/auth/logout/', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'}).then(r=>r.status)`), 403, "missing CSRF token denied");
  await inspect("/candidate/profile", "Save career profile");
  await inspect("/candidate/experience", "Your experience");
  await inspect("/candidate/education", "Your education");
  await inspect("/candidate/projects", "The work behind your skills");
  await inspect("/candidate/settings", "Privacy & settings");
  await inspect("/candidate/resumes", "Resume versions");
  await login("recruiter", "/recruiter");
  await inspect("/recruiter/setup", "Your company");
  await inspect("/recruiter/jobs/new", "Create a role");
  await inspect("/recruiter/applicants", "Fictional Journey Candidate");
  await login("operator", "/candidate");
  await inspect("/operator", "Review with a reason.");
  await inspect("/operator/reports", "Listing reports");
  await inspect("/operator/deletion", "Deletion requests");
  assert.deepEqual(browser.exceptions, [], "uncaught browser exceptions");
  console.log(JSON.stringify({ ok: true, scope: "Accessible names, rendered text contrast, keyboard skip/focus, reduced motion, responsive widths and API failure recovery. This is not a complete WCAG audit.", routes: results }, null, 2));
} finally { browser.close(); }
