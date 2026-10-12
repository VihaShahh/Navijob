"use client";

import { useState, type FormEvent } from "react";
import { ActionButton, InputField, LoadingState, Notice, TextAreaField } from "@/components/ui/Controls";
import { mutateApi } from "@/lib/api";
import { useResource } from "@/lib/useResource";
import { formatLabel } from "@/lib/formatters";

export type DeletionRequest = { id: number; status: string; reason: string; response: string; email?: string };

export function DeletionRequests() {
  const { data, error, loading, refresh } = useResource<DeletionRequest[]>("me/deletion/");
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState("");
  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPending(true); setFailure("");
    const form = event.currentTarget;
    try { await mutateApi("me/deletion/", Object.fromEntries(new FormData(form))); form.reset(); refresh(); }
    catch (reason) { setFailure(reason instanceof Error ? reason.message : "Could not request deletion."); }
    finally { setPending(false); }
  }
  async function cancel(id: number) {
    setPending(true); setFailure("");
    try { await mutateApi(`me/deletion/${id}/cancel/`); refresh(); }
    catch (reason) { setFailure(reason instanceof Error ? reason.message : "Could not cancel request."); }
    finally { setPending(false); }
  }
  return <section className="panel stack"><h2>Request account deletion.</h2><p className="muted">The review team will review your request. Approval disables account access and starts a separate erasure review; it does not immediately erase records or PDFs. Submitted applications and hiring-team records may need retention review, and NaviJob cannot erase copies already downloaded by employers. Export your data first.</p>{failure && <Notice kind="error">{failure}</Notice>}{loading ? <LoadingState /> : error ? <Notice kind="error">{error}</Notice> : <>{data?.some(item => item.status === "pending") ? <Notice>Your request is pending. You can cancel it until the review team handles it.</Notice> : <form className="stack" onSubmit={send}><TextAreaField name="reason" label="Anything the review team should know? (optional)" maxLength={2000} /><InputField name="confirmation" label="Type REQUEST DELETION to confirm" pattern="REQUEST DELETION" required /><ActionButton variant="outline" disabled={pending}>{pending ? "Sending…" : "Request deletion review"}</ActionButton></form>}{data?.map(item => <article className="team-note" key={item.id}><strong>{formatLabel(item.status)}</strong>{item.response && <p>{item.response}</p>}{item.status === "pending" && <ActionButton variant="quiet" disabled={pending} onClick={() => cancel(item.id)}>Cancel deletion request</ActionButton>}</article>)}</>}</section>;
}
