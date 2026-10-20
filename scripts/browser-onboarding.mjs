import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { connectBrowser } from "./browser-client.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));
const shell = code => execFileSync(`${root}backend/.venv/bin/python`, ["manage.py", "shell", "--settings=config.settings.preview", "-c", code], { cwd: `${root}backend`, encoding: "utf8" }).trim().split("\n").at(-1);
const browser = await connectBrowser();
const { call, evaluate, until, navigate, fill, click, screenshot } = browser;
const stamp = Date.now();
const email = `hiring-journey-${stamp}@sample.navijob.test`;
const company = `Fictional Hiring Journey ${stamp}`;
const password = "Journey-Hiring-42!";
const expectText = text => until(`document.body.innerText.includes(${JSON.stringify(text)})`, text);
async function login(account, secret, destination) {
  await navigate("/login", "Sign in ↗"); await fill("email", account); await fill("password", secret); await click("Sign in ↗");
  await until(`location.pathname === ${JSON.stringify(destination)} && !!document.querySelector('.workspace-main')`, "signed-in workspace");
}
async function logout() { await click("Sign out"); await until('location.pathname === "/" && fetch("/api/auth/session/").then(r=>r.json()).then(r=>r.user === null)', "sign out"); }
try {
  await call("Network.clearBrowserCookies");
  await call("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await navigate("/signup?role=recruiter", "What brings you here?");
  await fill("name", "Fictional Hiring Journey"); await fill("email", email); await fill("password", password); await click("Create account ↗"); await expectText("Check your email");
  const token = shell(`from django.contrib.auth import get_user_model; from django.core import signing; from django.utils.crypto import salted_hmac; from apps.accounts.tokens import CONFIRMATION_SALT; u=get_user_model().objects.get(email=${JSON.stringify(email)}); print(signing.dumps({'user': u.pk, 'email': u.email, 'version': salted_hmac('navijob.confirm-password', u.password).hexdigest()}, salt=CONFIRMATION_SALT))`);
  await navigate(`/confirm-email?token=${encodeURIComponent(token)}`, "Confirm my email"); await click("Confirm my email ↗"); await expectText("Email confirmed");
  await login(email, password, "/recruiter");
  await navigate("/recruiter/setup", "Introduce your company");
  await fill("name", company); await fill("website", "https://example.com"); await fill("description", "Synthetic company for a local hiring journey; no employer partnership."); await fill("recruiter_title", "Sample founder");
  await evaluate('document.querySelector("input[name=declaration]").click()'); await click("Send for company review ↗"); await expectText("Company review: pending");
  await navigate("/recruiter/jobs/new", "Company identity and your hiring authority need review");
  assert.equal(await evaluate('document.querySelector("button[value=review]").disabled'), true, "unreviewed publication blocked");
  await logout();
  await login("operator@sample.navijob.test", process.env.NAVIJOB_SAMPLE_PASSWORD || "NaviJob-Preview-42!", "/candidate");
  await navigate("/operator", company);
  const companyScope = `[...document.querySelectorAll('article')].find(el => el.querySelector('h3')?.textContent === ${JSON.stringify(company)})`;
  await fill("decision", "reject", companyScope); await fill("method", "Fictional onboarding review", companyScope); await fill("reason", "Add clearer sample company context", companyScope); await click("Record decision", companyScope); await until(`!(${companyScope})`, "company rejection completed");
  await logout(); await login(email, password, "/recruiter");
  await navigate("/recruiter/setup", "Company review: rejected"); await fill("description", "Updated synthetic company description for local browser checks."); await click("Save company details"); await expectText("Company review: pending");
  await logout(); await login("operator@sample.navijob.test", process.env.NAVIJOB_SAMPLE_PASSWORD || "NaviJob-Preview-42!", "/candidate");
  await navigate("/operator", company);
  await fill("method", "Fictional local identity review", companyScope); await fill("reason", "Synthetic company context accepted", companyScope); await click("Record decision", companyScope); await until(`!(${companyScope})`, "company approval completed");
  const recruiterScope = `[...document.querySelectorAll('article')].find(el => el.querySelector('h3')?.textContent === 'Fictional Hiring Journey' && el.textContent.includes(${JSON.stringify(company)}))`;
  await fill("method", "Fictional authority declaration review", recruiterScope); await fill("reason", "Synthetic authority accepted for local preview", recruiterScope); await click("Record decision", recruiterScope); await until(`!(${recruiterScope})`, "authority approval completed");
  await logout(); await login(email, password, "/recruiter"); await navigate("/recruiter/setup", "Company review: approved");
  await screenshot("recruiter-onboarding");
  await navigate("/recruiter/applicants", "No applications");
  assert.deepEqual(browser.exceptions, []);
  console.log(JSON.stringify({ ok: true, email, company, journeys: ["recruiter signup/confirmation", "company declaration", "unreviewed publication denial", "operator rejection", "company correction/resubmission", "company identity approval", "separate authority approval", "empty applicant state"] }, null, 2));
} finally { browser.close(); }
