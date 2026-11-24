import { useState } from "react";
import DepartmentLogo, { DEPARTMENT_NAME } from "./DepartmentLogo.jsx";
import {
  ArrowLeft,
  ArrowRight,
  ClipboardList,
  Clock3,
  Layers,
  Package,
  PackageCheck,
  Plus,
  Users,
  TriangleAlert,
} from "lucide-react";
import {
  ActionError,
  Badge,
  Dialog,
  Fields,
  FormActions,
  PageTitle,
  Pager,
  RequestBadge,
  State,
  displayDate,
  endpoint,
  label,
  requestStatuses,
  useMutation,
  useResource,
  write,
} from "./workspace-ui.jsx";

const SIZE = 12;
const metricItems = [
  {
    status: "pending",
    title: "Pending review",
    Icon: ClipboardList,
    tone: "amber",
    adminPath: "/admin/review",
    description: "Awaiting a decision",
  },
  {
    status: "approved",
    title: "Approved",
    Icon: PackageCheck,
    tone: "green",
    adminPath: "/admin/release",
    description: "Ready for equipment pickup",
  },
  {
    status: "released",
    title: "On loan",
    Icon: Clock3,
    tone: "blue",
    adminPath: "/admin/active",
    description: "Currently checked out",
  },
  {
    status: "overdue",
    title: "Overdue",
    Icon: TriangleAlert,
    tone: "red",
    adminPath: "/admin/overdue",
    description: "Past the scheduled return",
  },
];

export function RequestTable({ items, admin }) {
  return (
    <div className="work-table-wrap">
      <table className="work-table">
        <thead>
          <tr>
            <th scope="col">Equipment</th>
            {admin && <th scope="col">Borrower</th>}
            <th scope="col">Return by</th>
            <th scope="col">Status</th>
            <th scope="col">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((row) => (
            <tr key={row.id}>
              <th scope="row">
                <a className="request-equipment" href={`#/requests/${row.id}`}>
                  <span className="request-equipment-icon">
                    <Package size={20} strokeWidth={1.6} aria-hidden="true" />
                  </span>
                  <span className="request-equipment-name">
                    {row.equipment_name}
                    <small>
                      #{row.id} · {row.asset_code}
                    </small>
                  </span>
                </a>
              </th>
              {admin && (
                <td data-label="Borrower">
                  {row.borrower_name || `#${row.borrower_id}`}
                </td>
              )}
              <td data-label="Return by">
                <time dateTime={row.due_at}>{displayDate(row.due_at)}</time>
              </td>
              <td data-label="Status">
                <RequestBadge row={row} />
              </td>
              <td>
                <a
                  className="request-open-button"
                  href={`#/requests/${row.id}`}
                  aria-label={`Open request ${row.id} for ${row.equipment_name}`}
                >
                  View <ArrowRight size={14} aria-hidden="true" />
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Dashboard({ session }) {
  const admin = session.user.role === "admin";
  const overview = useResource("/dashboard");
  const recent = useResource("/requests?limit=5");
  const active = useResource("/requests?custody=active&limit=3");
  const shortcuts = admin
    ? [
        {
          title: "Equipment inventory",
          description: "Equipment records and availability",
          path: "/admin/inventory",
          Icon: Layers,
        },
        {
          title: "Record a return",
          description: "Close a loan and check condition",
          path: "/admin/returns",
          Icon: PackageCheck,
        },
        {
          title: "Manage users",
          description: "Accounts and workspace access",
          path: "/admin/accounts",
          Icon: Users,
        },
      ]
    : [
        {
          title: "Browse equipment",
          description: "Find resources for your next class",
          path: "/equipment",
          Icon: Layers,
        },
        {
          title: "My requests",
          description: "Check approvals and pickup details",
          path: "/requests",
          Icon: ClipboardList,
        },
        {
          title: "Borrowing history",
          description: "View your past loans and returns",
          path: "/history",
          Icon: Clock3,
        },
      ];
  return (
    <>
      <section className="dashboard-intro" aria-labelledby="dashboard-title">
        <div className="dashboard-intro-copy">
          <p className="dashboard-eyebrow">
            {admin ? "Custodian workspace" : "Borrower workspace"}
          </p>
          <h1 id="dashboard-title" tabIndex={-1}>
            {admin ? "Equipment overview" : "Your borrowing overview"}
          </h1>
          <p>
            {admin
              ? "A clear view of requests, department equipment and every handover."
              : "Your requests, upcoming pickups and equipment returns, together."}
          </p>
          <div className="dashboard-intro-actions">
            <a
              className="primary-button"
              href={admin ? "#/admin/review" : "#/equipment"}
            >
              {admin ? (
                <ClipboardList size={17} aria-hidden="true" />
              ) : (
                <Plus size={17} aria-hidden="true" />
              )}
              {admin ? "Review requests" : "Borrow equipment"}
            </a>
            <a
              className="secondary-button"
              href={admin ? "#/admin/inventory" : "#/history"}
            >
              {admin ? "View inventory" : "View borrowing history"}{" "}
              <ArrowRight size={15} aria-hidden="true" />
            </a>
          </div>
        </div>
        <div className="dashboard-campus-card">
          <DepartmentLogo width={86} height={86} decorative />
          <div>
            <strong>{DEPARTMENT_NAME}</strong>
            <span>Equipment borrowing workspace</span>
          </div>
        </div>
      </section>
      <State resource={overview}>
        {(data) => (
          <div className="work-metric-grid">
            {metricItems.map(
              ({ status, title, Icon, tone, adminPath, description }) => (
                <a
                  className={`work-metric work-panel metric-${tone}`}
                  key={status}
                  href={`#${admin ? adminPath : "/requests"}`}
                >
                  <div className="work-metric-top">
                    <p>{title}</p>
                    <span className={`work-metric-icon ${tone}`}>
                      <Icon size={21} />
                    </span>
                  </div>
                  <strong>
                    {status === "overdue"
                      ? data.overdue
                      : (data.requests_by_status[status] ?? 0)}
                  </strong>
                  <div className="work-metric-bottom">
                    <span>{description}</span>
                    <ArrowRight size={15} aria-hidden="true" />
                  </div>
                </a>
              ),
            )}
          </div>
        )}
      </State>
      <div className="dashboard-content-grid">
        <section
          className="work-panel work-section"
          aria-labelledby="recent-title"
        >
          <header className="work-section-header">
            <div>
              <h2 id="recent-title">Recent requests</h2>
              <p>Latest borrowing activity · Philippine time</p>
            </div>
            <a
              className="text-button"
              href={admin ? "#/admin/history" : "#/requests"}
            >
              View all <ArrowRight size={16} />
            </a>
          </header>
          <State
            resource={recent}
            empty={
              recent.data?.length === 0 &&
              "No requests have been submitted yet."
            }
          >
            {(items) => <RequestTable items={items} admin={admin} />}
          </State>
        </section>
        <aside className="dashboard-side">
          <section
            className="work-panel dashboard-shortcuts"
            aria-labelledby="shortcuts-title"
          >
            <div className="dashboard-panel-title">
              <h2 id="shortcuts-title">Quick actions</h2>
            </div>
            {shortcuts.map(({ title, description, path, Icon }) => (
              <a key={path} href={`#${path}`} className="dashboard-shortcut">
                <span className="dashboard-shortcut-icon">
                  <Icon size={19} strokeWidth={1.7} aria-hidden="true" />
                </span>
                <span>
                  <strong>{title}</strong>
                  <small>{description}</small>
                </span>
                <ArrowRight size={15} aria-hidden="true" />
              </a>
            ))}
          </section>
          <section
            className="work-panel dashboard-loans"
            aria-labelledby="loans-title"
          >
            <div className="dashboard-panel-title">
              <h2 id="loans-title">On loan</h2>
              <a
                href={admin ? "#/admin/active" : "#/requests"}
                className="text-button"
              >
                View all <ArrowRight size={13} />
              </a>
            </div>
            <State
              resource={active}
              empty={
                active.data?.length === 0 &&
                "No equipment is currently on loan."
              }
            >
              {(loans) =>
                loans.map((loan) => (
                  <a
                    href={`#/requests/${loan.id}`}
                    key={loan.id}
                    className="dashboard-loan"
                  >
                    <span className="dashboard-loan-icon">
                      <Package size={20} aria-hidden="true" />
                    </span>
                    <span>
                      <strong>{loan.equipment_name}</strong>
                      <small>Due {displayDate(loan.due_at)}</small>
                    </span>
                    <ArrowRight size={14} aria-hidden="true" />
                  </a>
                ))
              }
            </State>
          </section>
        </aside>
      </div>
    </>
  );
}

const views = {
  requests: {
    title: "My requests",
    description: "Track your bookings and open a request to see its details.",
    filter: true,
  },
  history: {
    title: "Borrowing history",
    description: "Review your past and current requests and loan records.",
    filter: true,
  },
  review: {
    title: "Review requests",
    description: "Approve or reject pending requests.",
    status: "pending",
  },
  release: {
    title: "Release equipment",
    description: "Confirm pickup for approved requests.",
    status: "approved",
  },
  returns: {
    title: "Record returns",
    description: "Inspect returned equipment and record its condition.",
    custody: "active",
  },
  active: {
    title: "Active loans",
    description: "See equipment currently checked out and its due time.",
    custody: "active",
  },
  overdue: {
    title: "Overdue equipment",
    description: "Review open loans past their due time.",
    custody: "overdue",
  },
  transaction: {
    title: "Transaction history",
    description: "Search borrowing, release and return records.",
    filter: true,
  },
};

export function RequestList({ view, session }) {
  const config = views[view];
  const [status, setStatus] = useState(view === "history" ? "returned" : "");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const rows = useResource(
    endpoint("/requests", {
      q: query,
      status: config.status || status,
      custody: config.custody,
      offset,
      limit: SIZE + 1,
    }),
  );
  const admin = session.user.role === "admin";
  function search(event) {
    event.preventDefault();
    setQuery(new FormData(event.currentTarget).get("search").trim());
    setOffset(0);
  }

  return (
    <>
      <PageTitle title={config.title} description={config.description} />
      <section className="work-panel work-section" aria-label={config.title}>
        <form className="work-filters work-panel-filters" onSubmit={search}>
          <label className="work-grow">
            Equipment or storage rack
            <input
              name="search"
              type="search"
              placeholder="Search requests"
              maxLength={120}
            />
          </label>
          {config.filter && (
            <label>
              Status
              <select
                value={status}
                onChange={(event) => {
                  setStatus(event.target.value);
                  setOffset(0);
                }}
              >
                <option value="">All statuses</option>
                {requestStatuses.map((value) => (
                  <option key={value} value={value}>
                    {label(value)}
                  </option>
                ))}
              </select>
            </label>
          )}
          <button className="secondary-button">Search</button>
        </form>
        <p className="work-table-timezone">Due times use Philippine time.</p>
        <State resource={rows}>
          {(items) => (
            <>
              {items.length ? (
                <RequestTable items={items.slice(0, SIZE)} admin={admin} />
              ) : (
                <p className="work-state">No requests match this view.</p>
              )}
              <Pager
                offset={offset}
                size={SIZE}
                hasMore={items.length > SIZE}
                setOffset={setOffset}
              />
            </>
          )}
        </State>
      </section>
    </>
  );
}

const actions = {
  cancel: {
    title: "Cancel request",
    verb: "Cancel request",
    method: "DELETE",
    suffix: "",
    copy: "This request will be canceled and kept in your history.",
    success: "Request canceled.",
  },
  approve: {
    title: "Approve request",
    verb: "Approve request",
    method: "PATCH",
    suffix: "/decision",
    copy: "Approval reserves the equipment for the requested dates.",
    success: "Request approved.",
  },
  reject: {
    title: "Reject request",
    verb: "Reject request",
    method: "PATCH",
    suffix: "/decision",
    copy: "The borrower will see that the request was rejected.",
    success: "Request rejected.",
  },
  release: {
    title: "Confirm equipment release",
    verb: "Confirm release",
    method: "POST",
    suffix: "/release",
    copy: "Record the item’s condition at pickup.",
    success: "Equipment released.",
  },
  return: {
    title: "Confirm equipment return",
    verb: "Confirm return",
    method: "PUT",
    suffix: "/return",
    copy: "Record the condition after inspecting the returned item. Damaged equipment will be marked for maintenance.",
    success: "Return recorded.",
  },
};

function RequestAction({ type, row, session, close, completed }) {
  const mutation = useMutation();
  const action = actions[type];
  function submit(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    mutation.run(async () => {
      const remarks = data.get("remarks")?.trim() || undefined;
      let body;
      if (type === "approve" || type === "reject")
        body = {
          decision: type === "approve" ? "approved" : "rejected",
          remarks,
        };
      if (type === "release" || type === "return")
        body = { condition: data.get("condition"), remarks };
      await write(
        session,
        action.method,
        `/requests/${row.id}${action.suffix}`,
        body,
      );
      completed(action.success);
    });
  }
  return (
    <Dialog title={action.title} busy={mutation.busy} close={close}>
      <form className="work-dialog-form" onSubmit={submit}>
        <p>{action.copy}</p>
        <fieldset className="work-form-fields" disabled={mutation.busy}>
          {(type === "release" || type === "return") && (
            <label>
              Equipment condition
              <select name="condition" required defaultValue="">
                <option value="" disabled>
                  Select condition
                </option>
                <option value="good">Good</option>
                <option value="fair">Fair</option>
                {type === "return" && <option value="damaged">Damaged</option>}
              </select>
            </label>
          )}
          {["approve", "reject", "return"].includes(type) && (
            <label>
              Remarks (optional)
              <textarea
                name="remarks"
                rows={3}
                maxLength={500}
                aria-describedby="remarks-privacy"
              />
              <span className="work-muted" id="remarks-privacy">
                Keep personal information out of remarks. The borrower and
                custodian can see them.
              </span>
            </label>
          )}
        </fieldset>
        <ActionError error={mutation.error} />
        <FormActions
          busy={mutation.busy}
          submit={action.verb}
          close={close}
          danger={type === "cancel" || type === "reject"}
        />
      </form>
    </Dialog>
  );
}

export function RequestDetails({ id, session }) {
  const request = useResource(`/requests/${id}`);
  const [action, setAction] = useState(null);
  const [notice, setNotice] = useState("");
  const admin = session.user.role === "admin";
  const row = request.data;
  return (
    <>
      <a className="work-back" href={admin ? "#/admin/history" : "#/requests"}>
        <ArrowLeft size={16} />
        {admin ? "Transaction history" : "My requests"}
      </a>
      <PageTitle
        title={row?.equipment_name || `Request #${id}`}
        description={row ? `Request #${id} · ${row.asset_code}` : undefined}
      >
        {row && <RequestBadge row={row} />}
      </PageTitle>
      {notice && (
        <p className="work-success" role="status">
          {notice}
        </p>
      )}
      <State resource={request}>
        {(data) => (
          <div className="work-detail-grid">
            <section className="work-panel work-detail">
              <h2>Request details</h2>
              <p className="work-muted">Dates are shown in Philippine time.</p>
              <Fields
                entries={[
                  ...(admin
                    ? [
                        [
                          "Borrower",
                          data.borrower_name || `#${data.borrower_id}`,
                        ],
                      ]
                    : []),
                  ["Borrow from", displayDate(data.borrow_at)],
                  ["Return by", displayDate(data.due_at)],
                  ["Submitted", displayDate(data.created_at)],
                  ["Purpose", data.purpose],
                  ...(data.decided_at
                    ? [["Decision time", displayDate(data.decided_at)]]
                    : []),
                  ...(data.canceled_at
                    ? [["Canceled at", displayDate(data.canceled_at)]]
                    : []),
                  ...(data.decision_remarks
                    ? [["Decision remarks", data.decision_remarks]]
                    : []),
                ]}
              />
              {!admin && data.status === "pending" && (
                <div className="work-actions">
                  <button
                    className="danger-button"
                    onClick={() => setAction("cancel")}
                  >
                    Cancel request
                  </button>
                </div>
              )}
              {admin && data.status === "pending" && (
                <div className="work-actions">
                  <button
                    className="danger-button"
                    onClick={() => setAction("reject")}
                  >
                    Reject request
                  </button>
                  <button
                    className="primary-button"
                    onClick={() => setAction("approve")}
                  >
                    Approve request
                  </button>
                </div>
              )}
              {admin && data.status === "approved" && (
                <div className="work-actions">
                  <button
                    className="primary-button"
                    onClick={() => setAction("release")}
                  >
                    Release equipment
                  </button>
                </div>
              )}
              {admin && data.status === "released" && (
                <div className="work-actions">
                  <button
                    className="primary-button"
                    onClick={() => setAction("return")}
                  >
                    Record return
                  </button>
                </div>
              )}
            </section>
            <section className="work-panel work-detail">
              <h2>Equipment custody</h2>
              {data.loan ? (
                <Fields
                  entries={[
                    ["Released at", displayDate(data.loan.released_at)],
                    ["Release condition", label(data.loan.release_condition)],
                    ["Returned at", displayDate(data.loan.returned_at)],
                    ["Return condition", label(data.loan.return_condition)],
                    [
                      "Equipment service status",
                      <Badge value={data.equipment_state} />,
                    ],
                    ...(data.loan.return_remarks
                      ? [["Return remarks", data.loan.return_remarks]]
                      : []),
                  ]}
                />
              ) : (
                <p className="work-muted">
                  Equipment has not been released for this request.
                </p>
              )}
            </section>
          </div>
        )}
      </State>
      {action && row && (
        <RequestAction
          type={action}
          row={row}
          session={session}
          close={() => setAction(null)}
          completed={(message) => {
            setAction(null);
            setNotice(message);
            request.reload();
          }}
        />
      )}
    </>
  );
}
