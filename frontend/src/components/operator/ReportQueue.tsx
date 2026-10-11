"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/SessionProvider";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { ActionButton, LoadingState, Notice, SelectField, TextAreaField } from "@/components/ui/Controls";
import type { Report } from "@/components/candidate/ListingReports";
import { mutateApi } from "@/lib/api";
import { useResource } from "@/lib/useResource";

function ReportAction({ report, refresh }: { report: Report; refresh: () => void }) {
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPending(true); setError("");
    try { await mutateApi(`operator/reports/${report.id}/`, Object.fromEntries(new FormData(event.currentTarget))); refresh(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not resolve report."); }
    finally { setPending(false); }
  }
  return <article className="panel stack"><h2>{report.title}</h2><p>{report.category}: {report.details}</p><form className="stack" onSubmit={submit}><SelectField name="action" label="Resolution"><option value="resolve">Resolve without closing</option><option value="close">Close listing and resolve</option><option value="dismiss">Dismiss report</option></SelectField><TextAreaField name="reason" label="Response to reporter" maxLength={2000} required />{error && <Notice kind="error">{error}</Notice>}<ActionButton disabled={pending}>{pending ? "Recording…" : "Record resolution"}</ActionButton></form></article>;
}

export function ReportQueue() {
  const { user, loading } = useSession();
  const { data, error, refresh } = useResource<Report[]>(user?.is_operator ? "operator/reports/" : null);
  return <PublicLayout><section className="container workspace-content stack"><Link href="/operator">← Operator reviews</Link><h1>Listing reports</h1>{loading ? <LoadingState /> : !user?.is_operator ? <Notice>Authorized operators only.</Notice> : error ? <Notice kind="error">{error}</Notice> : !data ? <LoadingState /> : data.length ? data.map(report => <ReportAction key={report.id} report={report} refresh={refresh} />) : <p>No pending reports.</p>}</section></PublicLayout>;
}
