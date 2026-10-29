"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/SessionProvider";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { ActionButton, InputField, LoadingState, Notice, SelectField, TextAreaField } from "@/components/ui/Controls";
import { mutateApi } from "@/lib/api";
import { useResource } from "@/lib/useResource";
import { formatDate } from "@/lib/formatters";

type Item = { id: number; name: string; website?: string; description?: string; company?: string; title?: string; updated_at: string };
type Audit = { id: number; kind: string; target_id: number; decision: string; reason: string; method: string; actor: string; created_at: string };
type Queues = { companies: Item[]; recruiters: Item[]; jobs: Item[]; audit: Audit[] };

function DecisionForm({ item, kind, refresh }: { item: Item; kind: string; refresh: () => void }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    setPending(true); setError("");
    try { await mutateApi(`operator/reviews/${kind}/${item.id}/`, { ...values, expected_updated_at: item.updated_at }); refresh(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not record this decision."); }
    finally { setPending(false); }
  }
  return <article className="panel stack"><h3>{item.name}</h3><p className="small-copy">{item.company} {item.title} {item.website}</p>{item.description && <p className="preserve-lines small-copy">{item.description}</p>}<form className="stack" onSubmit={submit}><SelectField name="decision" label="Decision" required><option value="approve">Approve</option><option value="reject">Request changes / revoke review</option></SelectField><InputField name="method" label="What evidence did you check?" hint="Company review methods are public. Use a general check description without personal details." maxLength={240} required /><TextAreaField name="reason" label="Reason and permitted feedback" maxLength={2000} hint="Company and job feedback is shared with the hiring team. Keep sensitive investigation details out." required />{error && <Notice kind="error">{error}</Notice>}<ActionButton disabled={pending}>{pending ? "Recording…" : "Record decision"}</ActionButton></form></article>;
}

export function OperatorReviews() {
  const { user, loading } = useSession();
  const { data, error, refresh } = useResource<Queues>(user?.is_operator ? "operator/reviews/" : null);
  return <PublicLayout><section className="container workspace-content stack"><p className="eyebrow">Marketplace operations</p><h1>Review with a reason.</h1>{loading ? <LoadingState /> : !user?.is_operator ? <Notice>Sign in with an authorized operator account to review the marketplace. <Link href="/login">Sign in</Link></Notice> : <><nav className="actions"><Link href="/operator">Review queues</Link><Link href="/operator/reports">Listing reports</Link><Link href="/operator/deletion">Deletion requests</Link><ActionButton variant="quiet" onClick={refresh}>Reload queues</ActionButton></nav><p className="muted">Review company identity, recruiter authority and role publication separately. Each queue shows up to 100 oldest requests.</p>{error ? <Notice kind="error">{error}</Notice> : !data ? <LoadingState /> : <>{([ ["companies", "company", "Company identity"], ["recruiters", "recruiter", "Recruiter authority"], ["jobs", "job", "Role publication"] ] as const).map(([key, kind, label]) => <section className="stack" key={kind}><h2>{label}</h2>{data[key].length ? data[key].map(item => <DecisionForm key={`${kind}-${item.id}-${item.updated_at}`} item={item} kind={kind} refresh={refresh} />) : <p className="muted">No pending requests.</p>}</section>)}<section className="stack"><h2>Recent decisions</h2>{data.audit.map(record => <article className="panel" key={record.id}><strong>{record.kind} #{record.target_id} · {record.decision}</strong><p>{record.reason}</p><p className="small-copy muted">{record.method} · {record.actor} · {formatDate(record.created_at)}</p></article>)}</section></>}</>}</section></PublicLayout>;
}
