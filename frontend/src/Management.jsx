import { useState } from "react";
import { Plus } from "lucide-react";
import {
  ActionError,
  Badge,
  Dialog,
  Fields,
  FormActions,
  PageTitle,
  Pager,
  State,
  availabilityStatuses,
  displayDate,
  endpoint,
  label,
  useMutation,
  useResource,
  write,
} from "./workspace-ui.jsx";

const SIZE = 12;

function EquipmentEditor({ item, session, close, completed }) {
  const mutation = useMutation();
  const [condition, setCondition] = useState(item?.condition || "good");
  const initiallyUnavailable = ["maintenance", "retired"].includes(
    item?.availability,
  );
  const [status, setStatus] = useState(
    initiallyUnavailable ? item.availability : "serviceable",
  );
  const checkedOut = item?.availability === "on_loan";

  function submit(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    mutation.run(async () => {
      const body = {
        name: data.get("name").trim(),
        storage_rack: data.get("storage_rack").trim(),
        location: data.get("location").trim(),
        description: item ? data.get("description").trim() : "",
        condition,
        service_status: status,
      };
      if (!body.name || !body.storage_rack || !body.location)
        throw new Error("Enter an equipment name, storage rack and location code.");
      await write(
        session,
        item ? "PUT" : "POST",
        item ? `/equipment/${item.id}` : "/equipment",
        body,
      );
      completed(item ? "Equipment updated." : "Equipment added.");
    });
  }
  return (
    <Dialog
      title={item ? "Edit equipment" : "Add equipment"}
      close={close}
      busy={mutation.busy}
    >
      <form className="work-dialog-form" onSubmit={submit}>
        <fieldset className="work-form-fields" disabled={mutation.busy}>
          <div className="work-form-columns">
            <label>
              Equipment name
              <input
                name="name"
                defaultValue={item?.name}
                required
                maxLength={120}
              />
            </label>
            <label>
              Storage Rack
              <input
                name="storage_rack"
                defaultValue={item?.storage_rack ?? item?.asset_code}
                required
                maxLength={40}
              />
            </label>
            <label>
              Location Code
              <input
                name="location"
                defaultValue={item?.location}
                required
                maxLength={120}
              />
            </label>
            <label>
              Condition
              <select
                value={condition}
                disabled={checkedOut}
                onChange={(event) => {
                  const value = event.target.value;
                  setCondition(value);
                  if (value === "damaged" && status === "serviceable")
                    setStatus("maintenance");
                }}
              >
                {["good", "fair", "damaged"].map((value) => (
                  <option key={value} value={value}>
                    {label(value)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Service status
              <select
                value={status}
                disabled={checkedOut}
                onChange={(event) => setStatus(event.target.value)}
              >
                {["serviceable", "maintenance", "retired"].map((value) => (
                  <option
                    key={value}
                    value={value}
                    disabled={
                      value === "serviceable" && condition === "damaged"
                    }
                  >
                    {label(value)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {checkedOut && (
            <p className="work-muted">
              Record the return to change the condition or service status.
            </p>
          )}
          {item && (
            <label>
              Description
              <textarea
                name="description"
                defaultValue={item.description}
                maxLength={1000}
                rows={3}
              />
            </label>
          )}
        </fieldset>
        <ActionError error={mutation.error} />
        <FormActions
          busy={mutation.busy}
          submit={item ? "Save equipment" : "Add equipment"}
          close={close}
        />
      </form>
    </Dialog>
  );
}

export function Inventory({ session }) {
  const [q, setQuery] = useState("");
  const [availability, setAvailability] = useState("");
  const [offset, setOffset] = useState(0);
  const [editor, setEditor] = useState(null);
  const [notice, setNotice] = useState("");
  const items = useResource(
    endpoint("/equipment", { q, availability, offset, limit: SIZE }),
  );
  function completed(message) {
    setEditor(null);
    setNotice(message);
    setOffset(0);
    items.reload();
  }
  return (
    <>
      <PageTitle
        title="Equipment inventory"
        description="Manage equipment records and service status."
      >
        <div className="work-inline">
          <button
            className="primary-button"
            onClick={() => setEditor({ kind: "equipment" })}
          >
            <Plus size={16} /> Add equipment
          </button>
        </div>
      </PageTitle>
      {notice && (
        <p className="work-success" role="status">
          {notice}
        </p>
      )}
      <section
        className="work-panel work-section"
        aria-label="Inventory records"
      >
        <form
          className="work-filters work-panel-filters"
          onSubmit={(event) => {
            event.preventDefault();
            setQuery(new FormData(event.currentTarget).get("search").trim());
            setOffset(0);
          }}
        >
          <label className="work-grow">
            Equipment name, storage rack or location code
            <input
              type="search"
              name="search"
              maxLength={120}
              placeholder="e.g. Pliers, MT03 or MT03.01"
            />
          </label>
          <label>
            Availability
            <select
              value={availability}
              onChange={(event) => {
                setAvailability(event.target.value);
                setOffset(0);
              }}
            >
              <option value="">All statuses</option>
              {availabilityStatuses.map((value) => (
                <option key={value} value={value}>
                  {label(value)}
                </option>
              ))}
            </select>
          </label>
          <button className="secondary-button">Search</button>
        </form>
        <State resource={items}>
          {(data) => (
            <>
              {data.items.length ? (
                <div className="work-table-wrap">
                  <table className="work-table">
                    <thead>
                      <tr>
                        <th scope="col">Equipment</th>
                        <th scope="col">Location Code</th>
                        <th scope="col">Condition</th>
                        <th scope="col">Availability</th>
                        <th scope="col">
                          <span className="sr-only">Actions</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.items.map((item) => (
                        <tr key={item.id}>
                          <th scope="row">
                            {item.name}
                            <span>
                              {item.storage_rack ?? item.asset_code}
                            </span>
                          </th>
                          <td data-label="Location Code">{item.location}</td>
                          <td data-label="Condition">
                            {label(item.condition)}
                          </td>
                          <td data-label="Availability">
                            <Badge value={item.availability} />
                          </td>
                          <td>
                            <button
                              className="text-button"
                              aria-label={`Edit ${item.name}`}
                              onClick={() =>
                                setEditor({ kind: "equipment", item })
                              }
                            >
                              Edit
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="work-state">
                  No equipment matches these filters. Try All statuses or another equipment name, rack or location code.
                </p>
              )}
              <Pager
                offset={offset}
                size={SIZE}
                hasMore={offset + SIZE < data.total}
                setOffset={setOffset}
              />
            </>
          )}
        </State>
      </section>
      {editor?.kind === "equipment" && (
        <EquipmentEditor
          item={editor.item}
          session={session}
          close={() => setEditor(null)}
          completed={completed}
        />
      )}
    </>
  );
}

function AccountEditor({ account, session, close, completed }) {
  const mutation = useMutation();
  const [role, setRole] = useState(account?.role || "borrower");
  const isOwn = account?.id === session.user.id;
  function submit(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    mutation.run(async () => {
      const body = {
        full_name: data.get("full_name").trim(),
        role,
        borrower_type: role === "borrower" ? data.get("borrower_type") : null,
      };
      if (!body.full_name) throw new Error("Enter a display name.");
      if (account) body.is_active = isOwn || data.get("active") === "true";
      else {
        body.email = data.get("email").trim();
        body.password = data.get("password");
      }
      const result = await write(
        session,
        account ? "PUT" : "POST",
        account ? `/users/${account.id}` : "/users",
        body,
      );
      completed(account ? "Account updated." : "Account added.", result);
    });
  }
  return (
    <Dialog
      title={account ? "Edit account" : "Add account"}
      close={close}
      busy={mutation.busy}
    >
      <form
        className="work-dialog-form"
        onSubmit={submit}
        aria-describedby="account-privacy"
      >
        <p className="work-muted" id="account-privacy">
          Use an email address you own, including Gmail. It will be your
          EquipTrack sign-in email. Passwords are stored as hashes.
        </p>
        <fieldset className="work-form-fields" disabled={mutation.busy}>
          <label>
            Display name
            <input
              name="full_name"
              defaultValue={account?.full_name}
              required
              maxLength={120}
            />
          </label>
          {account ? (
            <Fields entries={[["Email", account.email]]} />
          ) : (
            <>
              <label>
                Email
                <input
                  name="email"
                  type="email"
                  placeholder="name@gmail.com"
                  autoComplete="email"
                  required
                  maxLength={254}
                />
              </label>
              <label>
                Initial password
                <input
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={12}
                  maxLength={128}
                />
                <span className="work-muted">Use at least 12 characters.</span>
              </label>
            </>
          )}
          <div className="work-form-columns">
            <label>
              Role
              <select
                value={role}
                disabled={isOwn}
                onChange={(event) => setRole(event.target.value)}
              >
                <option value="borrower">Borrower</option>
                <option value="admin">Custodian</option>
              </select>
            </label>
            {role === "borrower" && (
              <label>
                Borrower type
                <select
                  name="borrower_type"
                  defaultValue={account?.borrower_type || "student"}
                >
                  <option value="student">Student</option>
                  <option value="faculty">Faculty</option>
                </select>
              </label>
            )}
            {account && (
              <label>
                Account status
                <select
                  name="active"
                  defaultValue={String(account.is_active)}
                  disabled={isOwn}
                >
                  <option value="true">Active</option>
                  <option value="false">Inactive</option>
                </select>
              </label>
            )}
          </div>
          {account && !isOwn && (
            <p className="work-muted">
              Deactivation and role changes end that account’s current sessions.
            </p>
          )}
        </fieldset>
        <ActionError error={mutation.error} />
        <FormActions
          busy={mutation.busy}
          submit={account ? "Save account" : "Add account"}
          close={close}
        />
      </form>
    </Dialog>
  );
}

export function Accounts({ session, updateUser }) {
  const [offset, setOffset] = useState(0);
  const [editor, setEditor] = useState(null);
  const [notice, setNotice] = useState("");
  const accounts = useResource(endpoint("/users", { offset, limit: SIZE + 1 }));
  return (
    <>
      <PageTitle
        title="User management"
        description="Create accounts and manage access."
      >
        <button className="primary-button" onClick={() => setEditor({})}>
          <Plus size={16} /> Add account
        </button>
      </PageTitle>
      {notice && (
        <p className="work-success" role="status">
          {notice}
        </p>
      )}
      <section className="work-panel work-section" aria-label="User accounts">
        <State resource={accounts}>
          {(items) => (
            <>
              {items.length ? (
                <div className="work-table-wrap">
                  <table className="work-table">
                    <thead>
                      <tr>
                        <th scope="col">Account</th>
                        <th scope="col">Role</th>
                        <th scope="col">Status</th>
                        <th scope="col">
                          <span className="sr-only">Actions</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.slice(0, SIZE).map((user) => (
                        <tr key={user.id}>
                          <th scope="row">
                            {user.full_name}
                            <span>{user.email}</span>
                          </th>
                          <td data-label="Role">
                            {label(user.role)}
                            {user.borrower_type &&
                              ` · ${label(user.borrower_type)}`}
                          </td>
                          <td data-label="Status">
                            <Badge
                              value={user.is_active ? "active" : "inactive"}
                            />
                          </td>
                          <td>
                            <button
                              className="text-button"
                              aria-label={`Edit account for ${user.full_name}`}
                              onClick={() => setEditor({ account: user })}
                            >
                              Edit
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="work-state">No accounts on this page.</p>
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
      {editor && (
        <AccountEditor
          account={editor.account}
          session={session}
          close={() => setEditor(null)}
          completed={(message, user) => {
            setEditor(null);
            setNotice(message);
            if (user.id === session.user.id) updateUser(user);
            accounts.reload();
          }}
        />
      )}
    </>
  );
}

function ProfileForm({ session, user, updateUser }) {
  const mutation = useMutation();
  const [notice, setNotice] = useState("");
  return (
    <form
      className="work-panel work-form"
      aria-describedby="profile-privacy"
      onSubmit={(event) => {
        event.preventDefault();
        const name = new FormData(event.currentTarget).get("full_name").trim();
        setNotice("");
        mutation.run(async () => {
          if (!name) throw new Error("Enter a display name.");
          const result = await write(session, "PATCH", "/profile", {
            full_name: name,
          });
          updateUser(result);
          setNotice("Profile updated.");
        });
      }}
    >
      <Fields
        entries={[
          ["Email", user.email],
          ["Role", label(user.role)],
          ...(user.borrower_type
            ? [["Borrower type", label(user.borrower_type)]]
            : []),
        ]}
      />
      <label>
        Display name
        <input
          name="full_name"
          defaultValue={user.full_name}
          required
          maxLength={120}
          disabled={mutation.busy}
        />
      </label>
      <p className="work-muted" id="profile-privacy">
        Use a fictional name. It identifies your demonstration account to the
        custodian.
      </p>
      <ActionError error={mutation.error} />
      {notice && (
        <p className="work-success" role="status">
          {notice}
        </p>
      )}
      <FormActions busy={mutation.busy} submit="Save profile" />
    </form>
  );
}

export function Profile({ session, updateUser }) {
  const profile = useResource("/profile");
  return (
    <>
      <PageTitle
        title="My profile"
        description="View your account details and correct your display name."
      />
      <State resource={profile}>
        {(user) => (
          <ProfileForm session={session} updateUser={updateUser} user={user} />
        )}
      </State>
    </>
  );
}

export function AuditTrail() {
  const [offset, setOffset] = useState(0);
  const logs = useResource(
    endpoint("/audit-logs", { offset, limit: SIZE + 1 }),
  );
  return (
    <>
      <PageTitle
        title="Audit trail"
        description="View recorded changes to requests, equipment and accounts."
      />
      <section className="work-panel work-section" aria-label="Audit records">
        <State resource={logs}>
          {(items) => (
            <>
              {items.length ? (
                <div className="work-table-wrap">
                  <table className="work-table">
                    <thead>
                      <tr>
                        <th scope="col">Action</th>
                        <th scope="col">Record</th>
                        <th scope="col">Actor</th>
                        <th scope="col">Philippine time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.slice(0, SIZE).map((row) => (
                        <tr key={row.id}>
                          <th scope="row">
                            {label(row.action.replaceAll(".", " "))}
                          </th>
                          <td data-label="Record">
                            {row.entity_type === "request" ? (
                              <a href={`#/requests/${row.entity_id}`}>
                                Request #{row.entity_id}
                              </a>
                            ) : (
                              `${label(row.entity_type)} #${row.entity_id}`
                            )}
                          </td>
                          <td data-label="Actor">Account #{row.actor_id}</td>
                          <td data-label="Philippine time">
                            <time dateTime={row.created_at}>
                              {displayDate(row.created_at)}
                            </time>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="work-state">No audit events on this page.</p>
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
