import { useEffect, useRef, useState } from "react";
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  ChevronRight,
  ClipboardCheck,
  ClipboardList,
  Clock3,
  History,
  LayoutDashboard,
  LibraryBig,
  LogOut,
  Menu,
  Package,
  ShieldCheck,
  TriangleAlert,
  UserRound,
  Users,
} from "lucide-react";
import Catalog, { BorrowRequest, EquipmentDetails } from "./Catalog.jsx";
import { Accounts, AuditTrail, Inventory, Profile } from "./Management.jsx";
import { Dashboard, RequestDetails, RequestList } from "./Requests.jsx";
import { Dialog, PageTitle } from "./workspace-ui.jsx";

const borrowerNav = [
  ["/", "Dashboard", LayoutDashboard],
  ["/equipment", "Equipment catalog", LibraryBig],
  ["/requests", "My requests", ClipboardList],
  ["/history", "Borrowing history", History],
  ["/profile", "My profile", UserRound],
];
const adminNav = [
  ["/", "Dashboard", LayoutDashboard],
  ["/admin/review", "Review requests", ClipboardCheck, "review"],
  ["/admin/release", "Release equipment", ArrowUpFromLine, "release"],
  ["/admin/returns", "Record returns", ArrowDownToLine, "returns"],
  ["/admin/active", "Active loans", Clock3, "active"],
  ["/admin/overdue", "Overdue equipment", TriangleAlert, "overdue"],
  ["/admin/inventory", "Inventory", Package],
  ["/admin/accounts", "User management", Users],
  ["/admin/history", "Transaction history", History, "transaction"],
  ["/admin/audit", "Audit trail", ShieldCheck],
];

function locationPath() {
  if (["#catalog", "#equipment-list"].includes(window.location.hash))
    return "/equipment";
  return window.location.hash.slice(1).replace(/\/$/, "") || "/";
}

function navMatches(path, route) {
  return path === route || (route !== "/" && path.startsWith(`${route}/`));
}

function Navigation({ items, path, close, grouped = false }) {
  return (
    <nav className="work-nav" aria-label="Workspace">
      {items.map(([route, title, Icon], index) => (
        <div key={route}>
          {grouped &&
            (index === 0 ||
              route === "/admin/inventory" ||
              route === "/profile") && (
              <p className="work-nav-group">
                {index === 0
                  ? "Workspace"
                  : route === "/profile"
                    ? "Account"
                    : "Management"}
              </p>
            )}
          <a
            href={`#${route}`}
            onClick={close}
            aria-current={navMatches(path, route) ? "page" : undefined}
          >
            <Icon size={18} aria-hidden="true" />
            <span>{title}</span>
            {navMatches(path, route) && (
              <span className="work-nav-indicator" aria-hidden="true" />
            )}
          </a>
        </div>
      ))}
    </nav>
  );
}

function Privacy({ close }) {
  return (
    <Dialog title="Privacy and data use" close={close}>
      <div className="work-dialog-form">
        <p>
          Use synthetic data for this demonstration. The custodian can see
          account names, borrowing details and equipment history. Borrowers can
          view their own requests and update their display name.
        </p>
        <p>
          EquipTrack uses a session cookie to keep you signed in. Avoid entering
          real names, email addresses or sensitive information in forms and
          remarks.
        </p>
        <div className="work-actions">
          <button className="primary-button" onClick={close}>
            Done
          </button>
        </div>
      </div>
    </Dialog>
  );
}

function WorkspacePage({ path, session, updateUser }) {
  const admin = session.user.role === "admin";
  if (path === "/") return <Dashboard session={session} />;
  if (path === "/profile")
    return <Profile session={session} updateUser={updateUser} />;
  if (path === "/equipment") return <Catalog />;
  if (path === "/requests")
    return (
      <RequestList
        view={admin ? "transaction" : "requests"}
        session={session}
      />
    );
  if (path === "/history")
    return (
      <RequestList view={admin ? "transaction" : "history"} session={session} />
    );
  const detail = path.match(/^\/equipment\/([1-9]\d*)(\/request)?$/);
  if (detail && !detail[2])
    return <EquipmentDetails id={detail[1]} session={session} />;
  if (detail && !admin)
    return <BorrowRequest id={detail[1]} session={session} />;
  const request = path.match(/^\/requests\/([1-9]\d*)$/);
  if (request) return <RequestDetails id={request[1]} session={session} />;
  if (admin && path === "/admin/inventory")
    return <Inventory session={session} />;
  if (admin && path === "/admin/accounts")
    return <Accounts session={session} updateUser={updateUser} />;
  if (admin && path === "/admin/audit") return <AuditTrail />;
  const view = admin && adminNav.find(([route]) => route === path)?.[3];
  if (view) return <RequestList view={view} session={session} />;

  const forbidden =
    (!admin && path.startsWith("/admin/")) || Boolean(admin && detail?.[2]);
  return (
    <>
      <PageTitle
        title={forbidden ? "Access denied" : "Page not found"}
        description={
          forbidden
            ? "Your role does not have access to this page."
            : "Check the address or go back to your dashboard."
        }
      />
      <a className="primary-button" href="#/">
        Back to dashboard
      </a>
    </>
  );
}

export default function App({
  session,
  signOut,
  signingOut,
  sessionError,
  updateUser,
}) {
  const [path, setPath] = useState(locationPath);
  const [menuOpen, setMenuOpen] = useState(false);
  const [privacyOpen, setPrivacyOpen] = useState(false);
  const main = useRef(null);
  const cameFromNavigation = useRef(false);
  const admin = session.user.role === "admin";
  const items = admin ? adminNav : borrowerNav;
  const role = admin ? "Custodian" : "Borrower";
  const section = items.find(([route]) => navMatches(path, route))?.[1];
  const initials = session.user.full_name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();

  useEffect(() => {
    function changed() {
      const next = locationPath();
      if (next !== path) {
        cameFromNavigation.current = true;
        setPath(next);
      }
      setMenuOpen(false);
    }
    window.addEventListener("hashchange", changed);
    return () => window.removeEventListener("hashchange", changed);
  }, [path]);

  useEffect(() => {
    if (!cameFromNavigation.current) return;
    cameFromNavigation.current = false;
    main.current?.querySelector("h1")?.focus();
    window.scrollTo(0, 0);
  }, [path]);

  return (
    <div className="work-shell">
      <a
        className="work-skip"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          main.current?.focus();
        }}
      >
        Skip to content
      </a>
      <aside className="work-sidebar">
        <a className="work-brand" href="#/">
          <img
            src="/images/bu-seal.png"
            alt="Bicol University seal"
            width="46"
            height="46"
          />
          <span className="work-brand-name">
            Equip<span>Track</span>
            <small>Bicol University</small>
          </span>
        </a>
        <Navigation items={items} path={path} grouped />
        <div className="work-sidebar-footer">
          <button type="button" onClick={() => setPrivacyOpen(true)}>
            <ShieldCheck size={17} />
            Privacy and data use
          </button>
          <div className="work-sidebar-project">
            <span className="work-project-mark">
              <Package size={17} aria-hidden="true" />
            </span>
            <span>
              Equipment workspace<small>MIS 215 · Academic project</small>
            </span>
          </div>
        </div>
      </aside>
      <div className="work-frame">
        <header className="work-topbar">
          <div className="work-inline">
            <button
              className="icon-button work-mobile-menu"
              aria-label="Open navigation"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen(true)}
            >
              <Menu size={22} />
            </button>
            <span className="work-topbar-context">
              <span>Workspace</span>
              <ChevronRight size={13} aria-hidden="true" />
              <strong>{section || `${role} workspace`}</strong>
            </span>
          </div>
          <div className="work-topbar-account">
            <time className="work-today" dateTime={new Date().toISOString()}>
              {new Intl.DateTimeFormat("en-PH", {
                timeZone: "Asia/Manila",
                month: "short",
                day: "numeric",
                year: "numeric",
              }).format(new Date())}
            </time>
            <a
              href="#/profile"
              className="work-account"
              aria-label="My profile"
            >
              <span className="work-avatar" aria-hidden="true">
                {initials}
              </span>
              <span className="work-account-name">
                <strong>{session.user.full_name}</strong>
                <small>{role}</small>
              </span>
            </a>
            <button
              className="secondary-button work-signout"
              onClick={signOut}
              disabled={signingOut}
            >
              <LogOut size={16} aria-hidden="true" />
              {signingOut ? "Signing out…" : "Sign out"}
            </button>
          </div>
        </header>
        <main className="work-main" id="main-content" ref={main} tabIndex={-1}>
          {sessionError && (
            <p className="work-error" role="alert">
              {sessionError}
            </p>
          )}
          <WorkspacePage
            key={path}
            path={path}
            session={session}
            updateUser={updateUser}
          />
        </main>
      </div>
      {menuOpen && (
        <Dialog title="EquipTrack navigation" close={() => setMenuOpen(false)}>
          <div className="work-mobile-nav">
            <Navigation
              items={items}
              path={path}
              close={() => setMenuOpen(false)}
            />
            <button
              className="secondary-button"
              onClick={() => {
                setMenuOpen(false);
                setPrivacyOpen(true);
              }}
            >
              Privacy and data use
            </button>
          </div>
        </Dialog>
      )}
      {privacyOpen && <Privacy close={() => setPrivacyOpen(false)} />}
    </div>
  );
}
