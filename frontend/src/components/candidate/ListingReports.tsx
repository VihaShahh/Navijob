"use client";

import { useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import { ActionButton, InputField, LoadingState, Notice, SelectField, TextAreaField } from "@/components/ui/Controls";
import { mutateApi } from "@/lib/api";
import { useResource } from "@/lib/useResource";

export type Report = { id: number; job: number; title: string; category: string; details: string; status: string; response: string };

export function ListingReports() {
  const search = useSearchParams();
  const { data, error, loading, refresh } = useResource<Report[]>("reports/");
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState("");
  const [message, setMessage] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPending(true); setFailure(""); setMessage("");
    const form = event.currentTarget;
    try { await mutateApi("reports/", Object.fromEntries(new FormData(form))); form.reset(); setMessage("Report received. You can follow its review below."); refresh(); }
    catch (reason) { setFailure(reason instanceof Error ? reason.message : "Could not send this report."); }
    finally { setPending(false); }
  }
  return <section className="stack"><p className="eyebrow">Help keep roles useful</p><h1>Report a listing.</h1><p className="muted">Tell the review team what needs attention. Your report is private to you and authorized operators. Submit one report per listing; avoid including sensitive personal information.</p><form className="panel stack" onSubmit={submit}><InputField label="Listing ID" name="job" type="number" min={1} defaultValue={search.get("job") || ""} required /><SelectField label="Concern" name="category"><option value="misleading">Misleading details</option><option value="closed">Role no longer open</option><option value="unsafe">Unsafe or abusive</option><option value="other">Other concern</option></SelectField><TextAreaField label="What should we review?" name="details" maxLength={3000} required />{failure && <Notice kind="error">{failure}</Notice>}{message && <Notice kind="success">{message}</Notice>}<ActionButton disabled={pending}>{pending ? "Sending…" : "Send report"}</ActionButton></form><h2>Your reports</h2>{loading ? <LoadingState /> : error ? <Notice kind="error">{error}</Notice> : data?.length ? data.map(report => <article className="panel" key={report.id}><h3>{report.title}</h3><p className="badge">{report.status}</p><p>{report.details}</p>{report.response && <p>Review team: {report.response}</p>}</article>) : <p className="muted">No reports yet.</p>}</section>;
}
