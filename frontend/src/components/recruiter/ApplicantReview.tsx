"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { ApplicationSnapshot } from "@/components/candidate/ApplicationSnapshot";
import { ActionButton, LoadingState, Notice, SelectField, TextAreaField } from "@/components/ui/Controls";
import { mutateApi } from "@/lib/api";
import { useResource } from "@/lib/useResource";
import { formatDate, formatLabel } from "@/lib/formatters";
import type { ApplicationRecord } from "@/lib/applications";

type TeamNote = { id: number; body: string; author_name: string; created_at: string };
type RecruiterApplication = ApplicationRecord & { allowed_transitions: string[]; notes: TeamNote[] };

function ReviewContent({ initial }: { initial: RecruiterApplication }) {
  const [application, setApplication] = useState(initial);
  const [target, setTarget] = useState("");
  const [note, setNote] = useState("");
  const [pending, setPending] = useState<"stage" | "note" | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  async function stage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPending("stage"); setError(""); setMessage("");
    try { const updated = await mutateApi<RecruiterApplication>(`recruiter/applications/${application.id}/stage/`, { status: target, expected_status: application.status }); setApplication(updated); setTarget(""); setMessage("Stage updated. The candidate can see this change in application history."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not update the stage."); }
    finally { setPending(null); }
  }
  async function addNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPending("note"); setError(""); setMessage("");
    try { const saved = await mutateApi<TeamNote>(`recruiter/applications/${application.id}/notes/`, { body: note }); setApplication(current => ({ ...current, notes: [saved, ...current.notes] })); setNote(""); setMessage("Private note saved for your company’s hiring team."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save the note."); }
    finally { setPending(null); }
  }
  return <section className="stack"><div><Link className="back-link" href={`/recruiter/applicants?job=${application.job.id}`}>← Back to applications</Link><span className="badge">{formatLabel(application.status)}</span><h1>{application.snapshot?.candidate?.full_name || "Candidate application"}</h1><p className="muted">{application.job.title} · Submitted {formatDate(application.submitted_at)}</p></div>{error && <Notice kind="error">{error} <button className="button button--quiet" onClick={() => window.location.reload()}>Reload application</button></Notice>}{message && <Notice kind="success">{message}</Notice>}<section className="panel stack"><h2>Move the application forward</h2>{application.allowed_transitions.length ? <form className="actions" onSubmit={stage}><SelectField label="Next stage" value={target} onChange={event => setTarget(event.target.value)} required disabled={pending !== null}><option value="">Choose a stage</option>{application.allowed_transitions.map(status => <option key={status} value={status}>{formatLabel(status)}</option>)}</SelectField><ActionButton type="submit" disabled={pending !== null || !target}>{pending === "stage" ? "Updating…" : "Update stage"}</ActionButton></form> : <Notice>This application is at a terminal stage. Its submitted content and history remain available.</Notice>}<p className="small-copy muted">Stage changes appear in the candidate’s application history. Use private notes for team discussion.</p></section>{application.snapshot?.candidate && application.snapshot?.resume ? <ApplicationSnapshot snapshot={application.snapshot} downloadUrl={application.resume_download_url} /> : <Notice>This older application does not contain a complete submitted snapshot.</Notice>}{application.cover_letter && <section className="panel"><h2>Candidate’s note</h2><p className="preserve-lines">{application.cover_letter}</p></section>}{application.snapshot?.questions?.length ? <section className="panel stack"><h2>Role-specific answers</h2>{application.snapshot.questions.map(question => <div key={question.id}><h3>{question.label}</h3><p className="small-copy preserve-lines">{application.answers[question.id] || "Not provided."}</p></div>)}</section> : null}<section className="panel stack"><h2>Private team notes</h2><p className="small-copy muted">Visible to reviewed recruiters in your company. These notes are not part of the candidate’s history.</p><form className="stack" onSubmit={addNote}><TextAreaField label="Add a private note" value={note} onChange={event => setNote(event.target.value)} required maxLength={4000} disabled={pending !== null} /><ActionButton type="submit" disabled={pending !== null || !note.trim()}>{pending === "note" ? "Saving…" : "Save private note"}</ActionButton></form>{application.notes.length ? application.notes.map(item => <article className="team-note" key={item.id}><p className="preserve-lines">{item.body}</p><p className="small-copy muted">{item.author_name || "Hiring teammate"} · {formatDate(item.created_at)}</p></article>) : <p className="small-copy muted">No team notes yet.</p>}</section><section className="panel stack"><h2>Application history</h2><ol className="timeline">{application.events.map(event => <li key={event.id}><strong>{formatLabel(event.status)}</strong><span className="small-copy muted">{formatDate(event.created_at)}</span><p className="small-copy">{event.note}</p></li>)}</ol></section></section>;
}

export function ApplicantReview({ id }: { id: string }) {
  const { data, loading, error, refresh } = useResource<RecruiterApplication>(`recruiter/applications/${encodeURIComponent(id)}/`);
  if (loading) return <LoadingState label="Opening the submitted profile…" />;
  if (error) return <Notice kind="error"><p>{error}</p><ActionButton variant="outline" onClick={refresh}>Try again</ActionButton></Notice>;
  return data ? <ReviewContent initial={data} key={data.id} /> : null;
}
