import { useEffect, useRef, useState } from "react";
import { ArrowLeft, KeyRound, LockKeyhole, Mail, ShieldCheck } from "lucide-react";
import { api } from "./api.js";
import DepartmentLogo, { DEPARTMENT_NAME } from "./DepartmentLogo.jsx";

function tokenFromLink() {
  return new URLSearchParams(window.location.hash.split("?")[1] || "").get("token") || "";
}

export default function PasswordRecovery({ mode, completed }) {
  const [token] = useState(tokenFromLink);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [done, setDone] = useState(false);
  const heading = useRef(null);
  const reset = mode === "reset";
  const validToken = /^[A-Za-z0-9_-]{43}$/.test(token);

  useEffect(() => {
    heading.current?.focus();
    if (reset && token) {
      // Keep the bearer token in component memory, out of the address bar/history.
      window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}#/reset-password`);
    }
  }, [reset, token]);

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    const form = event.currentTarget;
    const fields = new FormData(form);
    setError("");
    setNotice("");
    if (reset && fields.get("password") !== fields.get("confirmation")) {
      setError("Your passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      const result = await api(reset ? "/auth/reset-password" : "/auth/forgot-password", undefined, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reset
          ? { token, password: fields.get("password") }
          : { email: fields.get("email").trim() }),
      });
      form.reset();
      setNotice(result.message);
      setDone(true);
      if (reset) completed();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-page">
      <div className="login-campus" aria-hidden="true" />
      <div className="login-layout">
        <section className="login-card recovery-card" aria-labelledby="recovery-title">
          <div className="login-seal-wrap">
            <DepartmentLogo className="login-seal" width={120} height={120} />
          </div>
          <p className="login-department">{DEPARTMENT_NAME}</p>
          <h1 id="recovery-title" tabIndex={-1} ref={heading}>
            {done ? (reset ? "Password updated" : "Check your inbox") : (reset ? "Choose a new password" : "Forgot your password?")}
          </h1>
          <p className="login-description">
            {reset ? "Use a separate EquipTrack password with at least 12 characters." : "Enter your account email and we’ll send you a reset link."}
          </p>
          {notice && <p className="recovery-success" role="status">{notice}</p>}
          {reset && !validToken && !done ? (
            <div className="login-form">
              <p className="login-error" role="alert">This reset link is missing or invalid. Request a new one to continue.</p>
              <a className="login-submit recovery-submit" href="#/forgot-password">Request a new link</a>
            </div>
          ) : !done && (
            <form className="login-form" onSubmit={submit} aria-describedby="recovery-privacy">
              {reset ? (
                <>
                  <label className="login-field">
                    New password
                    <span className="login-input-wrap">
                      <KeyRound size={18} aria-hidden="true" />
                      <input name="password" type="password" autoComplete="new-password" required minLength={12} maxLength={128} disabled={busy} placeholder="At least 12 characters" />
                    </span>
                  </label>
                  <label className="login-field">
                    Confirm new password
                    <span className="login-input-wrap">
                      <LockKeyhole size={18} aria-hidden="true" />
                      <input name="confirmation" type="password" autoComplete="new-password" required minLength={12} maxLength={128} disabled={busy} placeholder="Enter the same password again" />
                    </span>
                  </label>
                </>
              ) : (
                <label className="login-field">
                  Email address
                  <span className="login-input-wrap">
                    <Mail size={18} aria-hidden="true" />
                    <input name="email" type="email" autoComplete="email" required maxLength={254} disabled={busy} placeholder="Enter your account email" />
                  </span>
                </label>
              )}
              {error && <p className="login-error" role="alert">{error}</p>}
              <button className="login-submit" disabled={busy}>
                {busy ? (reset ? "Saving password…" : "Sending link…") : (reset ? "Save new password" : "Send reset link")}
              </button>
            </form>
          )}
          <a className="recovery-back" href="#/login"><ArrowLeft size={16} aria-hidden="true" />Back to sign in</a>
          <p id="recovery-privacy" className="login-privacy">
            Reset links expire after 15 minutes and can be used once. Your password stays unchanged until you choose a new one.
          </p>
          <p className="login-demo-note"><ShieldCheck size={15} aria-hidden="true" />Secure account recovery</p>
        </section>
      </div>
    </main>
  );
}
