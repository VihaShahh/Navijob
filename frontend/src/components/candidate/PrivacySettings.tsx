"use client";

import { useState, type FormEvent } from "react";
import { ActionButton, LoadingState, Notice } from "@/components/ui/Controls";
import { mutateApi } from "@/lib/api";
import { useResource } from "@/lib/useResource";
import { DeletionRequests } from "./DeletionRequests";

type Preferences = { is_open_to_work: boolean | null; public_visibility: boolean; sharing: string };

function PreferenceForm({ data }: { data: Preferences }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPending(true); setError(""); setMessage("");
    try { await mutateApi("me/privacy/", { is_open_to_work: new FormData(event.currentTarget).get("is_open_to_work") === "on" }, "PATCH"); setMessage("Preference saved. Previously submitted applications keep the information you reviewed at submission."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save your preference."); }
    finally { setPending(false); }
  }
  return <section className="panel stack"><h2>Your profile stays private.</h2><p className="muted">{data.sharing}</p>{data.is_open_to_work !== null && <form className="stack" onSubmit={save}><label className="checkbox-field"><input name="is_open_to_work" type="checkbox" defaultChecked={data.is_open_to_work} />I’m open to new opportunities</label><p className="small-copy muted">This is included when you review and share your career profile in an application. It does not publish your profile in a directory.</p>{error && <Notice kind="error">{error}</Notice>}{message && <Notice kind="success">{message}</Notice>}<ActionButton disabled={pending}>{pending ? "Saving…" : "Save preference"}</ActionButton></form>}</section>;
}

export function PrivacySettings() {
  const { data, loading, error, refresh } = useResource<Preferences>("me/privacy/");
  return <section className="stack"><p className="eyebrow">Your information, your choices</p><h1>Privacy &amp; settings</h1>{loading ? <LoadingState /> : error ? <Notice kind="error">{error} <ActionButton onClick={refresh}>Try again</ActionButton></Notice> : data && <PreferenceForm data={data} />}<section className="panel stack"><h2>Take a copy of your data.</h2><p className="muted">Download your account, career profile, projects, saved roles, reports and submitted applications as JSON. Resume metadata includes private download links; download the PDFs separately while signed in. Hiring teams’ private notes are excluded.</p><a className="button button--outline" href="/api/me/export/">Download account data</a></section><DeletionRequests /></section>;
}
