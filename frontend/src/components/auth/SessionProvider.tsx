"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { getApi } from "@/lib/api";

export type AccountUser = { id: number; name: string; email: string; role: "candidate" | "recruiter"; email_verified: boolean; is_operator?: boolean };
type SessionState = { user: AccountUser | null; loading: boolean; error?: string };
type Session = SessionState & { refresh: () => Promise<void>; signIn: (user: AccountUser) => void };
const SessionContext = createContext<Session | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>({ user: null, loading: true });
  const sequence = useRef(0);
  const refresh = useCallback(async () => {
    const request = ++sequence.current;
    try {
      const result = await getApi<{ user: AccountUser | null }>("auth/session/");
      if (request === sequence.current) setState({ user: result.user, loading: false });
    } catch (reason) {
      if (request === sequence.current) setState(current => ({ ...current, loading: false, error: current.user ? undefined : reason instanceof Error ? reason.message : "Could not check your session." }));
    }
  }, []);
  const signIn = useCallback((user: AccountUser) => { sequence.current++; setState({ user, loading: false }); }, []);
  useEffect(() => {
    void refresh();
    window.addEventListener("focus", refresh);
    return () => { sequence.current++; window.removeEventListener("focus", refresh); };
  }, [refresh]);
  return <SessionContext.Provider value={{ ...state, refresh, signIn }}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession requires SessionProvider");
  return value;
}
