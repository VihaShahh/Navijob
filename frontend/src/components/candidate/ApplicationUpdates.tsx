"use client";

import Link from "next/link";
import { useState } from "react";
import { ActionButton, EmptyState, LoadingState, Notice } from "@/components/ui/Controls";
import { mutateApi } from "@/lib/api";
import { formatDate } from "@/lib/formatters";
import { useResource } from "@/lib/useResource";

type Update = { id: number; title: string; body: string; href: string; created_at: string; read_at: string | null };

export function ApplicationUpdates() {
  const { data, loading, error, refresh } = useResource<{ unread_count: number; results: Update[] }>("updates/");
  const [pending, setPending] = useState<number | null>(null);
  const [failure, setFailure] = useState("");
  async function markRead(id: number) {
    setPending(id); setFailure("");
    try { await mutateApi(`updates/${id}/read/`); refresh(); }
    catch (reason) { setFailure(reason instanceof Error ? reason.message : "Could not mark this update read."); }
    finally { setPending(null); }
  }
  return <section className="stack"><p className="eyebrow">Keep the next step in view</p><h1>Application updates</h1><p className="muted">Submission, withdrawal and hiring-stage changes appear here. Showing the latest 100 updates; full history stays with each application.</p>{failure && <Notice kind="error">{failure}</Notice>}{loading ? <LoadingState /> : error ? <Notice kind="error">{error} <ActionButton onClick={refresh}>Try again</ActionButton></Notice> : data?.results.length ? <><p className="badge">{data.unread_count} unread</p>{data.results.map(item => <article className="panel stack" key={item.id}><div className="section-heading"><h2>{item.title}</h2>{!item.read_at && <span className="badge">Unread</span>}</div><p>{item.body}</p><p className="small-copy muted">{formatDate(item.created_at)}</p><div className="actions"><Link href={item.href}>Open application ↗</Link>{!item.read_at && <ActionButton variant="quiet" disabled={pending !== null} onClick={() => markRead(item.id)}>{pending === item.id ? "Saving…" : "Mark as read"}</ActionButton>}</div></article>)}</> : <EmptyState title="You’re all caught up.">Application activity will appear here when there’s something to share.</EmptyState>}</section>;
}
