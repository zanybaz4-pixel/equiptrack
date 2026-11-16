import { useEffect, useState } from "react";
import App from "./App.jsx";
import { api } from "./api.js";

export default function SessionGate() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    function expire() {
      setSession(null);
      setError("Your session ended. Sign in again to continue.");
    }
    window.addEventListener("equiptrack:session-expired", expire);
    return () =>
      window.removeEventListener("equiptrack:session-expired", expire);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    api("/auth/me", controller.signal)
      .then(setSession)
      .catch((failure) => {
        if (failure.name !== "AbortError" && failure.status !== 401) {
          setError(failure.message);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  async function signIn(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    setError("");
    try {
      const result = await api("/auth/login", undefined, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: data.get("email"),
          password: data.get("password"),
        }),
      });
      form.reset();
      setSession(result);
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    setBusy(true);
    setError("");
    try {
      await api("/auth/logout", undefined, {
        method: "POST",
        headers: { "X-CSRF-Token": session.csrf_token },
      });
      setSession(null);
    } catch (failure) {
      if (failure.status === 401) setSession(null);
      else setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading)
    return (
      <main className="grid min-h-screen place-items-center" role="status">
        Checking your session…
      </main>
    );
  if (session) {
    return (
      <App
        session={session}
        signOut={signOut}
        signingOut={busy}
        sessionError={error}
        updateUser={(user) =>
          setSession((current) => current && { ...current, user })
        }
      />
    );
  }
  return (
    <main className="grid min-h-screen place-items-center p-5">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="eyebrow">EQUIPTRACK</p>
        <h1>Sign in</h1>
        <p
          id="login-privacy"
          className="mt-3 text-sm leading-relaxed text-slate-600"
        >
          Use your synthetic demonstration account. EquipTrack uses your email
          and password to verify access to your lending workspace.
        </p>
        <form
          onSubmit={signIn}
          aria-describedby="login-privacy"
          className="mt-6 flex flex-col gap-4"
        >
          <label className="flex flex-col gap-2">
            Email
            <input
              name="email"
              type="email"
              autoComplete="username"
              required
              maxLength={254}
              className="rounded-lg border border-slate-300 p-3"
            />
          </label>
          <label className="flex flex-col gap-2">
            Password
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
              maxLength={128}
              className="rounded-lg border border-slate-300 p-3"
            />
          </label>
          {error && (
            <p role="alert" className="error-text">
              {error}
            </p>
          )}
          <button className="primary-button" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
