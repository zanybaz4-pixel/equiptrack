import { useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  MapPin,
  Search,
  Wrench,
} from "lucide-react";
import { api } from "./api.js";
import {
  ActionError,
  Badge,
  Fields,
  FormActions,
  PageTitle,
  Pager,
  State,
  availabilityStatuses,
  endpoint,
  label,
  manilaInput,
  periodValues,
  useMutation,
  useResource,
  write,
} from "./workspace-ui.jsx";

const SIZE = 12;
export default function Catalog() {
  const [query, setQuery] = useState("");
  const [availability, setAvailability] = useState("");
  const [offset, setOffset] = useState(0);
  const catalog = useResource(
    endpoint("/equipment", {
      q: query,
      availability,
      offset,
      limit: SIZE,
    }),
  );

  function search(event) {
    event.preventDefault();
    setQuery(new FormData(event.currentTarget).get("search").trim());
    setOffset(0);
  }

  return (
    <>
      <PageTitle
        title="Equipment catalog"
        description="Find department equipment and check availability for your borrowing dates."
      />
      <form className="work-filters work-panel" onSubmit={search}>
        <label className="work-grow">
          Equipment or storage rack
          <input
            name="search"
            type="search"
            placeholder="Search the catalog"
            maxLength={120}
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
        <button className="primary-button">
          <Search size={16} /> Search
        </button>
      </form>
      <State
        resource={catalog}
        empty={
          catalog.data?.items.length === 0 &&
          !offset &&
          "No equipment matches these filters."
        }
      >
        {(page) => (
          <>
            <p className="work-result-count" role="status">
              {page.total} {page.total === 1 ? "item" : "items"}
            </p>
            <div className="work-catalog-grid">
              {page.items.map((item) => {
                return (
                  <article className="work-equipment" key={item.id}>
                    <div className="work-equipment-image">
                      <Wrench size={43} strokeWidth={1.5} aria-hidden="true" />
                      <Badge value={item.availability} />
                    </div>
                    <div className="work-equipment-body">
                      <p className="work-muted">
                        {item.asset_code}
                      </p>
                      <h2>
                        <a href={`#/equipment/${item.id}`}>{item.name}</a>
                      </h2>
                      <p className="work-equipment-location">
                        <MapPin size={14} />
                        {item.location}
                      </p>
                      <a
                        className="work-card-link"
                        href={`#/equipment/${item.id}`}
                        aria-label={`View ${item.name}`}
                      >
                        View equipment <ArrowRight size={15} />
                      </a>
                    </div>
                  </article>
                );
              })}
            </div>
            <Pager
              offset={offset}
              size={SIZE}
              hasMore={offset + SIZE < page.total}
              setOffset={setOffset}
            />
          </>
        )}
      </State>
    </>
  );
}

export function EquipmentDetails({ id, session }) {
  const item = useResource(`/equipment/${id}`);
  return (
    <>
      <a className="work-back" href="#/equipment">
        <ArrowLeft size={16} /> Equipment catalog
      </a>
      <PageTitle
        title={item.data?.name || "Equipment details"}
        description={item.data?.description}
      />
      <State resource={item}>
        {(data) => (
          <section className="work-panel work-detail">
            <Fields
              entries={[
                ["Storage Rack", data.asset_code],
                ["Location Code", data.location],
                ["Condition", label(data.condition)],
                ["Current availability", <Badge value={data.availability} />],
              ]}
            />
            {session.user.role === "borrower" &&
              (["maintenance", "retired"].includes(data.availability) ? (
                <p className="work-muted">
                  This item is unavailable for borrowing.
                </p>
              ) : (
                <div className="work-actions">
                  <a
                    className="primary-button"
                    href={`#/equipment/${id}/request`}
                  >
                    Request equipment <ArrowRight size={17} />
                  </a>
                </div>
              ))}
          </section>
        )}
      </State>
    </>
  );
}

function BorrowForm({ item, session }) {
  const form = useRef(null);
  const [availability, setAvailability] = useState(null);
  const [earliest] = useState(() => manilaInput(new Date()));
  const checking = useMutation();
  const submission = useMutation();
  const busy = checking.busy || submission.busy;
  const blocked = ["maintenance", "retired"].includes(item.availability);

  function check() {
    checking.run(async () => {
      const period = periodValues(new FormData(form.current));
      const result = await api(endpoint(`/equipment/${item.id}`, period));
      setAvailability(result.availability);
    });
  }
  function submit(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    submission.run(async () => {
      const purpose = data.get("purpose").trim();
      if (purpose.length < 5)
        throw new Error("Enter a purpose of at least five characters.");
      const period = periodValues(data);
      const result = await write(session, "POST", "/requests", {
        ...period,
        purpose,
        equipment_id: item.id,
      });
      window.location.hash = `/requests/${result.id}`;
    });
  }

  if (blocked)
    return (
      <section className="work-panel work-detail">
        <Badge value={item.availability} />
        <p>This item is unavailable for borrowing.</p>
      </section>
    );

  return (
    <form
      ref={form}
      className="work-panel work-form"
      onSubmit={submit}
      aria-describedby="request-privacy"
    >
      <p className="work-form-intro">
        {item.asset_code} · {item.name}
      </p>
      <fieldset disabled={busy} className="work-form-fields">
        <p className="work-muted">
          Enter the borrowing and return times in Philippine time (UTC+08:00).
        </p>
        <div
          className="work-form-columns"
          onChange={() => setAvailability(null)}
        >
          <label>
            Borrow from
            <input
              type="datetime-local"
              name="borrow_at"
              required
              min={earliest}
            />
          </label>
          <label>
            Return by
            <input
              type="datetime-local"
              name="due_at"
              required
              min={earliest}
            />
          </label>
        </div>
        <div className="work-inline">
          <button className="secondary-button" type="button" onClick={check}>
            {checking.busy ? "Checking…" : "Check dates"}
          </button>
          {availability && (
            <span role="status">
              <Badge value={availability} /> for these dates
            </span>
          )}
        </div>
        <ActionError error={!availability && checking.error} />
        <label>
          Purpose
          <textarea
            name="purpose"
            required
            minLength={5}
            maxLength={500}
            rows={4}
            placeholder="E.g., Synthetic classroom presentation"
          />
        </label>
        <p className="work-muted" id="request-privacy">
          The custodian sees your request, purpose and dates. Use synthetic
          details and keep personal information out of the purpose.
        </p>
      </fieldset>
      <ActionError error={submission.error} />
      <div className="work-actions">
        <a className="secondary-button" href={`#/equipment/${item.id}`}>
          Back
        </a>
        <button
          className="primary-button"
          disabled={
            busy || Boolean(availability && availability !== "available")
          }
        >
          {submission.busy ? "Submitting…" : "Submit request"}
        </button>
      </div>
    </form>
  );
}

export function BorrowRequest({ id, session }) {
  const item = useResource(`/equipment/${id}`);
  return (
    <>
      <PageTitle
        title="Request equipment"
        description="The custodian will review your dates and purpose."
      />
      <State resource={item}>
        {(data) => <BorrowForm item={data} session={session} />}
      </State>
    </>
  );
}
