"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/SessionProvider";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { ActionButton, LoadingState, Notice, SelectField, TextAreaField } from "@/components/ui/Controls";
import type { DeletionRequest } from "@/components/candidate/DeletionRequests";
import { mutateApi } from "@/lib/api";
import { useResource } from "@/lib/useResource";

function RequestReview({ item, refresh }: { item: DeletionRequest; refresh: () => void }) {
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPending(true); setError("");
    try { await mutateApi(`operator/deletion/${item.id}/`, Object.fromEntries(new FormData(event.currentTarget))); refresh(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not record review."); }
    finally { setPending(false); }
  }
  return <article className="panel stack"><h2>{item.email}</h2><p>{item.reason || "No reason provided."}</p><form className="stack" onSubmit={send}><SelectField label="Decision" name="action"><option value="disable_access">Approve access removal; erasure review pending</option><option value="decline">Decline with an explanation</option></SelectField><TextAreaField name="reason" label="Response and retention-review next steps" maxLength={2000} required />{error && <Notice kind="error">{error}</Notice>}<ActionButton disabled={pending}>{pending ? "Recording…" : "Record deletion review"}</ActionButton></form></article>;
}

export function DeletionQueue() {
  const { user, loading } = useSession();
  const { data, error, refresh } = useResource<DeletionRequest[]>(user?.is_operator ? "operator/deletion/" : null);
  return <PublicLayout><section className="container workspace-content stack"><Link href="/operator">← Operator reviews</Link><h1>Deletion requests</h1><p className="muted">Approval disables access. No files or hiring records are erased by this action; record the retention and physical-erasure follow-up explicitly.</p>{loading ? <LoadingState /> : !user?.is_operator ? <Notice>Authorized operators only.</Notice> : error ? <Notice kind="error">{error}</Notice> : !data ? <LoadingState /> : data.length ? data.map(item => <RequestReview key={item.id} item={item} refresh={refresh} />) : <p>No pending requests.</p>}</section></PublicLayout>;
}
