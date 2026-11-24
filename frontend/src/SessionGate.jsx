import { useEffect, useState } from "react";
import App from "./App.jsx";
import { api } from "./api.js";
import PasswordRecovery from "./PasswordRecovery.jsx";
import DepartmentLogo, { DEPARTMENT_NAME } from "./DepartmentLogo.jsx";
import { Eye, EyeOff, LockKeyhole, Mail, ShieldCheck } from "lucide-react";

export default function SessionGate() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [authLocation, setAuthLocation] = useState(() => window.location.hash);
  const authPath = authLocation.split("?")[0];

  useEffect(() => {
    function changed() { setAuthLocation(window.location.hash); }
    window.addEventListener("hashchange", changed);
    return () => window.removeEventListener("hashchange", changed);
  }, []);

  useEffect(() => {
    if (session && authPath === "#/login") window.location.replace("#/");
  }, [session, authPath]);

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

  if (authPath === "#/forgot-password" || authPath === "#/reset-password") {
    return <PasswordRecovery key={authLocation} mode={authPath === "#/reset-password" ? "reset" : "request"} completed={() => setSession(null)} />;
  }
  if (loading || (session && authPath === "#/login"))
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
    <main className="login-page">
      <div className="login-campus" aria-hidden="true" />
      <div className="login-layout">
        <section className="login-card" aria-labelledby="sign-in-title">
          <div className="login-seal-wrap">
            <DepartmentLogo className="login-seal" width={120} height={120} />
          </div>
          <p className="login-department">{DEPARTMENT_NAME}</p>
          <h1 id="sign-in-title">Sign in to EquipTrack</h1>
          <p className="login-description">
            Your department’s equipment, in one shared workspace.
          </p>
          <form
            onSubmit={signIn}
            aria-describedby="login-privacy"
            className="login-form"
          >
            <label className="login-field">
              Email address
              <span className="login-input-wrap">
                <Mail size={18} aria-hidden="true" />
                <input
                  id="login-email"
                  name="email"
                  type="email"
                  autoComplete="username"
                  required
                  maxLength={254}
                  placeholder="Enter your email address"
                />
              </span>
            </label>
            <div className="login-field">
              <label htmlFor="login-password">Password</label>
              <div className="login-input-wrap">
                <LockKeyhole size={18} aria-hidden="true" />
                <input
                  id="login-password"
                  name="password"
                  type={passwordVisible ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  maxLength={128}
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  className="login-password-toggle"
                  aria-label={
                    passwordVisible ? "Hide password" : "Show password"
                  }
                  aria-pressed={passwordVisible}
                  onClick={() => setPasswordVisible((visible) => !visible)}
                >
                  {passwordVisible ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
            <a className="login-forgot" href="#/forgot-password">Forgot password?</a>
            {error && (
              <p role="alert" className="login-error">
                {error}
              </p>
            )}
            <button className="login-submit" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <p id="login-privacy" className="login-privacy">
            Use your demonstration account to manage equipment borrowing,
            pickups and returns.
          </p>
          <p className="login-demo-note">
            <ShieldCheck size={15} aria-hidden="true" />
            Academic project · Equipment borrowing workspace
          </p>
        </section>
      </div>
    </main>
  );
}
