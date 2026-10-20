import { mkdirSync, writeFileSync } from "node:fs";

export async function connectBrowser() {
  const endpoint = process.env.CDP_URL || "http://127.0.0.1:9341";
  const tabs = await (await fetch(`${endpoint}/json/list`)).json();
  const tab = tabs.find(item => item.type === "page");
  if (!tab) throw new Error("Open a Chrome page with remote debugging enabled.");
  const socket = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.addEventListener("open", resolve, { once: true }); socket.addEventListener("error", reject, { once: true }); });
  const pending = new Map();
  const exceptions = [];
  let sequence = 0;
  socket.addEventListener("message", event => {
    const response = JSON.parse(event.data);
    if (response.method === "Runtime.exceptionThrown") exceptions.push(response.params.exceptionDetails.text);
    const entry = pending.get(response.id);
    if (!entry) return;
    pending.delete(response.id);
    clearTimeout(entry.timeout);
    if (response.error) entry.reject(new Error(response.error.message)); else entry.resolve(response.result);
  });
  const call = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence;
    const timeout = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 20000);
    pending.set(id, { resolve, reject, timeout });
    socket.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async expression => {
    const result = await call("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    return result.result.value;
  };
  const until = async (expression, label = expression) => {
    const start = Date.now();
    while (Date.now() - start < 20000) {
      try { if (await evaluate(expression)) return; } catch (error) { if (!/context|Cannot find|Cannot read properties of null/.test(error.message)) throw error; }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error(`Timed out: ${label}\n${await evaluate("document.body.innerText")}`);
  };
  const site = process.env.NAVIJOB_BROWSER_URL || "http://localhost:3100";
  if (!["localhost", "127.0.0.1"].includes(new URL(site).hostname)) throw new Error("Browser journeys may mutate only a local preview.");
  await call("Runtime.enable");
  await call("Page.enable");
  const navigate = async (path, text, destination = path.split("?")[0]) => {
    await call("Page.navigate", { url: `${site}${path}` });
    await until(`location.pathname === ${JSON.stringify(destination)} && document.readyState === "complete"`, path);
    if (text) await until(`document.body.innerText.includes(${JSON.stringify(text)})`, text);
  };
  const fill = async (name, value, scope = "document") => {
    await until(`(() => { const field = ${scope}?.querySelector(${JSON.stringify(`:is(input,textarea,select)[name="${name}"]`)}); return field && Object.keys(field).some(key => key.startsWith('__reactProps')); })()`, `hydrated field ${name}`);
    return evaluate(`(() => {
    const field = ${scope}.querySelector(${JSON.stringify(`:is(input,textarea,select)[name="${name}"]`)});
    if (!field) throw new Error(${JSON.stringify(`Missing field: ${name}`)});
    const proto = field.tagName === "SELECT" ? HTMLSelectElement.prototype : field.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, "value").set.call(field, ${JSON.stringify(value)});
    field.dispatchEvent(new Event("input", { bubbles: true })); field.dispatchEvent(new Event("change", { bubbles: true }));
  })()`);
  };
  const click = async (text, scope = "document") => {
    await until(`(() => { const button = [...(${scope}?.querySelectorAll("button, a") || [])].find(item => item.textContent.trim() === ${JSON.stringify(text)}); return button && !button.disabled && Object.keys(button).some(key => key.startsWith('__reactProps')); })()`, `hydrated action ${text}`);
    return evaluate(`(() => {
    const button = [...${scope}.querySelectorAll("button, a")].find(item => item.textContent.trim() === ${JSON.stringify(text)});
    if (!button || button.disabled) throw new Error(${JSON.stringify(`Missing or disabled action: ${text}`)});
    button.click();
  })()`);
  };
  const screenshot = async name => {
    await evaluate("window.scrollTo({top:0, behavior:'instant'})");
    const folder = process.env.NAVIJOB_BROWSER_ARTIFACTS || "/tmp/navijob-browser-artifacts";
    mkdirSync(folder, { recursive: true });
    const result = await call("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    writeFileSync(`${folder}/${name}.png`, Buffer.from(result.data, "base64"));
  };
  return { call, evaluate, until, navigate, fill, click, screenshot, exceptions, close: () => socket.close() };
}
