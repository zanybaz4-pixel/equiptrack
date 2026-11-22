import { useEffect, useId, useRef, useState } from "react";
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Inbox,
  LoaderCircle,
  X,
} from "lucide-react";
import { api } from "./api.js";

export const requestStatuses = [
  "pending",
  "approved",
  "released",
  "returned",
  "rejected",
  "canceled",
];
export const availabilityStatuses = [
  "available",
  "reserved",
  "on_loan",
  "maintenance",
  "retired",
];

const labels = {
  on_loan: "On loan",
  released: "On loan",
  returned_late: "Returned late",
  admin: "Custodian",
  borrower: "Borrower",
};

export function label(value) {
  return (
    labels[value] ||
    (value ? value[0].toUpperCase() + value.slice(1).replaceAll("_", " ") : "—")
  );
}

const dateFormatter = new Intl.DateTimeFormat("en-PH", {
  timeZone: "Asia/Manila",
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

export function displayDate(value) {
  return value ? dateFormatter.format(new Date(value)) : "—";
}

export function manilaInput(value) {
  // Contemporary Asia/Manila is UTC+08:00, independent of the browser's zone.
  return new Date(value.getTime() + 8 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 16);
}

export function periodValues(data) {
  const start = data.get("borrow_at");
  const end = data.get("due_at");
  const borrow_at = start ? `${start}:00+08:00` : "";
  const due_at = end ? `${end}:00+08:00` : "";
  if (!start || !end || new Date(due_at) <= new Date(borrow_at)) {
    throw new Error("Choose a borrowing time and a later return time.");
  }
  if (Date.parse(borrow_at) <= Date.now())
    throw new Error("Choose a future borrowing time.");
  return { borrow_at, due_at };
}

export function endpoint(path, params) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== "" && value != null) query.set(key, value);
  }
  return query.size ? `${path}?${query}` : path;
}

export function useResource(path) {
  const [request, setRequest] = useState(0);
  const [result, setResult] = useState(null);
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    api(path, controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setResult({ path, request, data });
      },
      (error) => {
        if (!controller.signal.aborted) setResult({ path, request, error });
      },
    );
    return () => controller.abort();
  }, [path, request]);
  const current =
    result?.path === path && result?.request === request ? result : null;
  return {
    data: current?.data,
    error: current?.error,
    loading: Boolean(path && !current),
    reload: () => setRequest((value) => value + 1),
  };
}

export function useMutation() {
  const inFlight = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function run(action) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError(failure.message);
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }
  return { busy, error, run };
}

export function write(session, method, path, body) {
  const headers = { "X-CSRF-Token": session.csrf_token };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  return api(path, undefined, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function PageTitle({ title, description, children }) {
  return (
    <header className="work-title">
      <div>
        <h1 tabIndex={-1}>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {children}
    </header>
  );
}

export function State({ resource, empty, children }) {
  if (resource.loading)
    return (
      <div className="work-state" role="status">
        <LoaderCircle size={19} className="work-spin" /> Loading…
      </div>
    );
  if (resource.error)
    return (
      <div className="work-state" role="alert">
        <AlertCircle size={21} />
        <p>{resource.error.message}</p>
        <button className="secondary-button" onClick={resource.reload}>
          Try again
        </button>
      </div>
    );
  if (empty)
    return (
      <div className="work-state">
        <Inbox size={22} />
        <p>{empty}</p>
      </div>
    );
  return children(resource.data);
}

export function Badge({ value }) {
  return <span className={`work-badge tone-${value}`}>{label(value)}</span>;
}

export function RequestBadge({ row }) {
  return (
    <Badge
      value={
        row.is_overdue
          ? "overdue"
          : row.was_returned_late
            ? "returned_late"
            : row.status
      }
    />
  );
}

export function Pager({ offset, size, hasMore, setOffset }) {
  return (
    (offset > 0 || hasMore) && (
      <nav className="work-pager" aria-label="Pagination">
        <button
          className="secondary-button"
          disabled={!offset}
          onClick={() => setOffset(offset - size)}
        >
          <ChevronLeft size={15} /> Previous
        </button>
        <span>Page {Math.floor(offset / size) + 1}</span>
        <button
          className="secondary-button"
          disabled={!hasMore}
          onClick={() => setOffset(offset + size)}
        >
          Next <ChevronRight size={15} />
        </button>
      </nav>
    )
  );
}

export function Dialog({ title, close, busy = false, children }) {
  const dialog = useRef(null);
  const titleId = useId();
  useEffect(() => {
    const element = dialog.current;
    element.showModal();
    return () => element.close();
  }, []);
  return (
    <dialog
      className="work-dialog"
      ref={dialog}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
    >
      <div className="work-dialog-header">
        <h2 id={titleId}>{title}</h2>
        <button
          type="button"
          className="icon-button"
          aria-label="Close dialog"
          disabled={busy}
          onClick={close}
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}

export function Fields({ entries }) {
  return (
    <dl className="work-fields">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{value ?? "—"}</dd>
        </div>
      ))}
    </dl>
  );
}

export function ActionError({ error }) {
  return (
    error && (
      <p className="work-error" role="alert">
        {error}
      </p>
    )
  );
}

export function FormActions({ busy, submit, close, danger = false }) {
  return (
    <div className="work-actions">
      {close && (
        <button
          className="secondary-button"
          type="button"
          onClick={close}
          disabled={busy}
        >
          Cancel
        </button>
      )}
      <button
        className={danger ? "danger-button" : "primary-button"}
        disabled={busy}
      >
        {busy ? "Saving…" : submit}
      </button>
    </div>
  );
}
