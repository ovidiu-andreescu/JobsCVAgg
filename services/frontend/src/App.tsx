import React, { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Search as SearchIcon,
  LogIn,
  UserPlus,
  MailCheck,
  Loader2,
  Settings2,
  Building2,
  MapPin,
  Globe2,
  CheckCircle2,
  Link as LinkIcon,
  BellRing,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";

import "./styles.css";

// ----------------------------- Types & helpers -----------------------------

interface Job {
  source: string;
  source_job_id: string;
  title: string;
  company: string;
  location?: string | null;
  remote?: boolean | null;
  url: string;
  description?: string | null;
  keywords?: string[] | null;
  salary?: string | null;
  posted_at?: string | null;
  extras?: Record<string, any>;
}

type FetchDebug = {
  ts: string;
  request: {
    url: string;
    method: string;
    headers: Record<string, string>;
    bodyPreview?: string;
  };
  response?: {
    ok: boolean;
    status: number;
    statusText: string;
    headers: Record<string, string>;
    bodyText?: string;
  };
  error?: string;
};

const authHeaders = (token?: string) =>
  token ? { Authorization: `Bearer ${token}` } : {};

const fmtDate = (iso?: string | null) => {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  return d.toLocaleDateString();
};

// helper: make an absolute base (works for "/api" and "http://..."), trim trailing slash
const abs = (base: string) =>
  new URL(base, window.location.origin).toString().replace(/\/$/, "");

// simple localStorage hook
const useLocalStorage = <T,>(key: string, initial: T) => {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : initial;
    } catch {
      return initial;
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {}
  }, [key, value]);
  return [value, setValue] as const;
};

// small labeled input helper
function LabeledInput(props: {
  label: string;
  value: string;
  placeholder?: string;
  type?: string;
  onChange: React.ChangeEventHandler<HTMLInputElement>;
}) {
  return (
    <div className="grid gap-2">
      <Label>{props.label}</Label>
      <Input
        value={props.value}
        type={props.type || "text"}
        placeholder={props.placeholder}
        onChange={props.onChange}
      />
    </div>
  );
}

// --------------------------------- App ---------------------------------

export default function App() {
  // API bases: default to execute-api (you can override in Settings)
  const EXEC_BASE = "https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com";

  const [umBase, setUmBase] = useLocalStorage("cfg.umBase", EXEC_BASE);
  const [aggBase, setAggBase] = useLocalStorage(
    "cfg.aggBase",
    EXEC_BASE + "/jobs/search"
  );
  const [notifBase, setNotifBase] = useLocalStorage("cfg.notifBase", EXEC_BASE);
  const [cvBase, setCvBase] = useLocalStorage("cfg.cvBase", EXEC_BASE);
  const [matcherBase, setMatcherBase] = useLocalStorage(
    "cfg.matcherBase",
    EXEC_BASE
  );

  const DEFAULTS = useMemo(
    () => ({
      um: EXEC_BASE,
      agg: EXEC_BASE + "/jobs/search",
      notif: EXEC_BASE,
      cv: EXEC_BASE,
      matcher: EXEC_BASE,
    }),
    []
  );

  function resetApiBasesToDefaults() {
    setUmBase(DEFAULTS.um);
    setAggBase(DEFAULTS.agg);
    setNotifBase(DEFAULTS.notif);
    setCvBase(DEFAULTS.cv);
    setMatcherBase(DEFAULTS.matcher);
    setToast("API bases reset to execute-api defaults");
  }

  // auth & ui state
  const [email, setEmail] = useLocalStorage("auth.email", "");
  const [password, setPassword] = useState("");
  const [token, setToken] = useLocalStorage<string | null>("auth.token", null);
  const isAuthed = !!token;

  const [tab, setTab] = useState("search");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  // search state
  const [q, setQ] = useLocalStorage("search.q", "software engineer");
  const [loc, setLoc] = useLocalStorage("search.loc", "Bucharest, RO");
  const [page, setPage] = useLocalStorage<number>("search.page", 1);
  const [perPage, setPerPage] = useLocalStorage<number>("search.perPage", 20);
  const [jobs, setJobs] = useState<Job[] | null>(null);

  // notifications state
  const [notifyTo, setNotifyTo] = useState("");
  const [notifySubject, setNotifySubject] =
    useState("JobsCVAgg test message");
  const [notifyMessage, setNotifyMessage] = useState(
    "Hello from the demo UI! ✨"
  );

  // CV & matches state
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [cvStatus, setCvStatus] = useState<any>(null);
  const [matches, setMatches] = useState<any[] | null>(null);
  const [lastUploadKey, setLastUploadKey] = useState<string | null>(null);
  const [cvNotReady, setCvNotReady] = useState(false);

  // debug panel state (listens to global fetch debugger from main.tsx)
  const [debugOpen, setDebugOpen] = useState(false);
  const [lastDebug, setLastDebug] = useState<FetchDebug | null>(null);

  useEffect(() => {
    function onDbg(e: Event) {
      const ev = e as CustomEvent<FetchDebug>;
      setLastDebug(ev.detail);
    }
    window.addEventListener("fetch-debug", onDbg as any);
    if ((window as any).__fetchDebug?.last)
      setLastDebug((window as any).__fetchDebug.last as FetchDebug);
    return () => window.removeEventListener("fetch-debug", onDbg as any);
  }, []);

  async function copyDebug() {
    try {
      await navigator.clipboard.writeText(JSON.stringify(lastDebug, null, 2));
      setToast("Copied last error JSON");
    } catch {}
  }

  // ----------------------------- API calls -----------------------------

async function apiRegister() {
  setBusy(true);
  try {
     const r = await fetch(`${abs(umBase)}/auth/register`, {
      method: "POST",
      mode: "cors",
      credentials: "omit",
      headers: {
        "accept": "application/json",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        email: email,
        password: password,
      }),
    });
    if (!r.ok) throw new Error(`Register failed: ${r.status}`);
    setToast("Registration successful. Check your inbox to verify your email.");
    setTab("auth");
  } catch (e: any) {
    setToast(e.message || "Registration failed");
  } finally {
    setBusy(false);
  }
}

async function apiLogin() {
  setBusy(true);
  try {
    const r = await fetch(`${abs(umBase)}/auth/login`, {
      method: "POST",
      mode: "cors",
      credentials: "omit",
      headers: {
        "accept": "application/json",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        email: email,
        password: password, // <-- from a password input state
      }),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((data as any)?.detail || `Login failed: ${r.status}`);
    if ((data as any)?.access_token) setToken((data as any).access_token);
    else if ((data as any)?.ok) setToken("dummy");
    setToast("Logged in ");
  } catch (e: any) {
    setToast(e?.message || "Login failed (network/CORS?)");
  } finally {
    setBusy(false);
  }
}


  async function apiVerifyLink() {
    setBusy(true);
    try {
      const r = await fetch(
        `${abs(umBase)}/auth/_debug/verify_link?email=${encodeURIComponent(email)}`,
        {
          method: "GET",
          mode: "cors",
          credentials: "omit",
          headers: { "accept": "application/json" },
        }
      );
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data?.detail || `Error: ${r.status}`);
      if (data?.url) window.open(data.url, "_blank");
      else setToast("Already verified");
    } catch (e: any) {
      setToast(e.message || "Cannot fetch verify link");
    } finally {
      setBusy(false);
    }
  }

  async function apiSearch() {
    setBusy(true);
    setJobs(null);
    try {
      const url = new URL(aggBase, window.location.origin); // supports absolute or relative
      if (!url.search) {
        url.searchParams.set("q", q);
        if (loc) url.searchParams.set("location", loc);
        url.searchParams.set("page", String(page || 1));
        url.searchParams.set("results_per_page", String(perPage || 20));
      }
      const r = await fetch(url.toString());
      const data = await r.json().catch(() => []);
      if (!r.ok) throw new Error((data as any)?.error || `Search failed: ${r.status}`);
      setJobs(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setToast(e.message || "Search failed");
    } finally {
      setBusy(false);
    }
  }

async function apiPresignAndUploadCV() {
  if (!cvFile) return setToast("Pick a PDF first");
  if (!token) return setToast("Please log in first");
  setBusy(true);
  try {
    const r = await fetch(`${abs(cvBase)}/me/cv/presign`, {
      method: "POST",
      mode: "cors",
      credentials: "omit",
      headers: {
        "accept": "application/json",
        "content-type": "application/json",
        ...authHeaders(token),
      },
      body: JSON.stringify({
        filename: cvFile.name,
        content_type: cvFile.type || "application/pdf",
      }),
    });

    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((data as any)?.detail || "Failed to presign");

    const url = (data as any).url as string;
    const fields = ((data as any).fields ?? {}) as Record<string, string>;

    // 2) Build FormData from *only* the presigned fields
    const form = new FormData();
    for (const [k, v] of Object.entries(fields)) {
      form.append(k, v);
    }

    if (!Object.prototype.hasOwnProperty.call(fields, "Content-Type")) {
      form.append("Content-Type", cvFile.type || "application/pdf");
    }

    form.append("file", cvFile);

    {
      let keyCount = 0;
      for (const [k] of (form as any).entries()) if (k === "key") keyCount++;
      if (keyCount !== 1) {
        throw new Error(`Upload form is invalid: expected 1 "key" field, found ${keyCount}`);
      }
    }

    // 6) POST to S3
    const s3 = await fetch(url, { method: "POST", body: form, mode: "cors" });
    if (!s3.ok) {
      const text = await s3.text().catch(() => "");
      throw new Error(`S3 upload failed: ${s3.status}${text ? ` — ${text.slice(0, 300)}` : ""}`);
    }

    setToast("Uploaded. Processing may take ~30–60s. Check status.");
  } catch (e: any) {
    setToast(e.message || "CV upload failed");
  } finally {
    setBusy(false);
  }
}



  async function apiCvStatus() {
    if (!token) return setToast("Please log in first");
    setBusy(true);
    try {
      const r = await fetch(`${abs(cvBase)}/me/cv`, {
        method: "GET",
        mode: "cors",
        credentials: "omit",
        headers: {
          "accept": "application/json",
          ...authHeaders(token),
        },
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error((data as any)?.detail || "CV status failed");
      setCvStatus(data);
    } catch (e: any) {
      setToast(e.message || "CV status error");
    } finally {
      setBusy(false);
    }
  }

  async function apiFetchMatches() {
    if (!token) return setToast("Please log in first");
    setBusy(true);
    try {
      const r = await fetch(`${abs(matcherBase)}/me/matches`, {
        method: "GET",
        mode: "cors",
        credentials: "omit",
        headers: {
          "accept": "application/json",
          ...authHeaders(token),
        },
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error((data as any)?.detail || "Fetch matches failed");
      setMatches(Array.isArray(data) ? data : (data as any).items || []);
    } catch (e: any) {
      setToast(e.message || "Matches error");
    } finally {
      setBusy(false);
    }
  }

  async function apiSendNotification() {
    setBusy(true);
    try {
     const r = await fetch(`${abs(notifBase)}/notifications/send`, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: {
          "accept": "application/json",
          "content-type": "application/json",
        },
        body: JSON.stringify({
          to: notifyTo || email,
          subject: notifySubject,
          message: notifyMessage,
          channel: "console",
        }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error((data as any)?.detail || `Failed: ${r.status}`);
      setToast("Notification sent ✉️");
    } catch (e: any) {
      setToast(e.message || "Notification failed");
    } finally {
      setBusy(false);
    }
  }

  async function probeCorsLogin() {
  setBusy(true);
  try {
    const url = `${abs(umBase)}/auth/login`;
    const r = await fetch(url, {
      method: "OPTIONS",
      mode: "cors",
      credentials: "omit",
      headers: {
        "origin": window.location.origin,
        "access-control-request-method": "POST",
        "access-control-request-headers": "content-type,authorization",
      },
    });

    const headers: Record<string, string> = {};
    r.headers.forEach((v, k) => (headers[k.toLowerCase()] = v));

    const dbg = {
      ts: new Date().toISOString(),
      request: {
        url,
        method: "OPTIONS",
        headers: {
          origin: window.location.origin,
          "access-control-request-method": "POST",
          "access-control-request-headers": "content-type,authorization",
        },
      },
      response: {
        ok: r.ok,
        status: r.status,
        statusText: r.statusText,
        headers,
        bodyText: "", // preflights usually have empty bodies
      },
    };
    window.dispatchEvent(new CustomEvent("fetch-debug", { detail: dbg }));

    const allowOrigin = headers["access-control-allow-origin"] || "∅";
    const allowMethods = headers["access-control-allow-methods"] || "∅";
    const allowHeaders = headers["access-control-allow-headers"] || "∅";
    setToast(
      `CORS preflight ${r.ok ? "OK" : r.status}: ` +
      `Allow-Origin=${allowOrigin} | Methods=${allowMethods} | Headers=${allowHeaders}`
    );
  } catch (e: any) {
    setToast(e?.message || "CORS probe failed");
  } finally {
    setBusy(false);
  }
}

  // ------------------------------- UI chunks -------------------------------

  const SettingsPanel = (
    <Card className="border-0 shadow-xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2 className="w-5 h-5" /> Settings
        </CardTitle>
        <CardDescription>Point the UI to your running services.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        <LabeledInput
          label="User Management base URL"
          value={umBase}
          onChange={(e) => setUmBase(e.target.value)}
          placeholder={EXEC_BASE}
        />
        <LabeledInput
          label="Job Aggregator endpoint"
          value={aggBase}
          onChange={(e) => setAggBase(e.target.value)}
          placeholder={EXEC_BASE + "/jobs/search"}
        />
        <LabeledInput
          label="Notifications base URL"
          value={notifBase}
          onChange={(e) => setNotifBase(e.target.value)}
          placeholder={EXEC_BASE}
        />
        <LabeledInput
          label="CV Handling base URL"
          value={cvBase}
          onChange={(e) => setCvBase(e.target.value)}
          placeholder={EXEC_BASE}
        />
        <LabeledInput
          label="Matcher base URL"
          value={matcherBase}
          onChange={(e) => setMatcherBase(e.target.value)}
          placeholder={EXEC_BASE}
        />
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={resetApiBasesToDefaults}>
            Reset to execute-api defaults
          </Button>
          <Button variant="outline" onClick={probeCorsLogin}>
            Probe CORS for /auth/login
          </Button>
          <span className="text-xs text-gray-500">
            Emits preflight result to the error panel.
          </span>
        </div>
      </CardContent>
    </Card>
  );

  const AuthCard = (
  <Card className="border-0 shadow-xl">
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <LogIn className="w-5 h-5" /> Authenticate
      </CardTitle>
      <CardDescription>
        Create an account, verify it, then sign in.
      </CardDescription>
    </CardHeader>
    <CardContent className="grid gap-4">
      <LabeledInput
        label="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@example.com"
        type="email"
      />
      <LabeledInput
        label="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="••••••••"
        type="password"
      />
      <div className="flex flex-wrap gap-2">
        <Button onClick={apiRegister} disabled={busy} className="gap-2">
          <UserPlus className="w-4 h-4" /> Register
        </Button>
        <Button
          variant="secondary"
          onClick={apiVerifyLink}
          disabled={busy}
          className="gap-2"
        >
          <MailCheck className="w-4 h-4" /> Get verify link
        </Button>
        <Button
          variant="default"
          onClick={apiLogin}
          disabled={busy}
          className="gap-2"
        >
          <LogIn className="w-4 h-4" /> Login
        </Button>
      </div>
      {isAuthed && (
        <div className="flex items-center gap-2 text-sm">
          <CheckCircle2 className="w-4 h-4" /> Signed in as{" "}
          <span className="font-medium">{email}</span>
        </div>
      )}
    </CardContent>
  </Card>
);

  const SearchCard = (
    <Card className="border-0 shadow-xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <SearchIcon className="w-5 h-5" /> Search Jobs
        </CardTitle>
        <CardDescription>
          Query multiple providers and see deduplicated results.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div className="grid md:grid-cols-3 gap-3">
          <LabeledInput
            label="Keywords"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g., Python, Data, React"
          />
          <LabeledInput
            label="Location"
            value={loc}
            onChange={(e) => setLoc(e.target.value)}
            placeholder="Bucharest, RO"
          />
          <div className="grid grid-cols-2 gap-2">
            <LabeledInput
              label="Page"
              value={String(page)}
              onChange={(e) => setPage(parseInt(e.target.value || "1"))}
              type="number"
            />
            <LabeledInput
              label="Per page"
              value={String(perPage)}
              onChange={(e) => setPerPage(parseInt(e.target.value || "20"))}
              type="number"
            />
          </div>
        </div>

        <div className="flex gap-2">
          <Button onClick={apiSearch} disabled={busy} className="gap-2">
            <SearchIcon className="w-4 h-4" /> Search
          </Button>
        </div>

        <Separator />

        {busy && (
          <div className="flex items-center gap-2 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" /> Working…
          </div>
        )}

        {Array.isArray(jobs) && (
          <div className="grid gap-3">
            <div className="text-sm text-gray-500">{jobs.length} result(s)</div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {jobs.map((job) => (
                <motion.a
                  key={`${job.source}:${job.source_job_id}`}
                  href={job.url}
                  target="_blank"
                  rel="noreferrer"
                  whileHover={{ y: -2 }}
                  className="block rounded-2xl shadow hover:shadow-lg p-4 border bg-card"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-base font-semibold leading-tight truncate">
                        {job.title}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                        <Building2 className="w-4 h-4" />
                        <span className="truncate">
                          {job.company || "Unknown"}
                        </span>
                      </div>
                    </div>
                    <Badge>{job.source}</Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 mt-3 text-sm text-gray-500">
                    {job.location && (
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {job.location}
                      </span>
                    )}
                    {job.remote != null && (
                      <span className="inline-flex items-center gap-1">
                        <Globe2 className="w-4 h-4" />
                        {job.remote ? "Remote" : "On-site"}
                      </span>
                    )}
                    {job.posted_at && <span>{fmtDate(job.posted_at)}</span>}
                  </div>
                  {job.keywords && job.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {job.keywords.slice(0, 6).map((k, idx) => (
                        <Badge key={idx}>{k}</Badge>
                      ))}
                    </div>
                  )}
                  {job.description && (
                    <p className="mt-3 text-sm line-clamp-3 whitespace-pre-line">
                      {job.description}
                    </p>
                  )}
                  <div className="mt-3 inline-flex items-center gap-1 text-sm font-medium">
                    <LinkIcon className="w-4 h-4" /> Open listing
                  </div>
                </motion.a>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const NotificationsCard = (
    <Card className="border-0 shadow-xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BellRing className="w-5 h-5" /> Send test notification
        </CardTitle>
        <CardDescription>
          Uses the Notifications service <code>/notifications/send</code>.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3">
        <div className="grid md:grid-cols-2 gap-3">
          <LabeledInput
            label="To"
            value={notifyTo}
            onChange={(e) => setNotifyTo(e.target.value)}
            placeholder={email || "you@example.com"}
          />
          <LabeledInput
            label="Subject"
            value={notifySubject}
            onChange={(e) => setNotifySubject(e.target.value)}
          />
        </div>
        <div className="grid gap-2">
          <Label>Message</Label>
          <Textarea
            value={notifyMessage}
            onChange={(e) => setNotifyMessage(e.target.value)}
            rows={4}
          />
        </div>
        <div>
          <Button onClick={apiSendNotification} disabled={busy}>
            Send
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  // --------------------------------- Render ---------------------------------

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-muted/20">
      <header className="sticky top-0 z-40 backdrop-blur supports-[backdrop-filter]:bg-white/70 border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="w-9 h-9 rounded-2xl bg-black/5 grid place-items-center"
            >
              <SearchIcon className="w-5 h-5" />
            </motion.div>
            <div>
              <div className="font-semibold leading-tight">JobsCVAgg</div>
              <div className="text-xs text-gray-500 -mt-0.5"></div>
            </div>
          </div>

          <Tabs value={tab} onValueChange={setTab} className="hidden md:block">
            <TabsList className="hidden md:flex gap-2">
              <TabsTrigger value="search">Search</TabsTrigger>
              <TabsTrigger value="auth">Auth</TabsTrigger>
              <TabsTrigger value="notify">Notify</TabsTrigger>
              <TabsTrigger value="cv">CV</TabsTrigger>
              <TabsTrigger value="matches">Matches</TabsTrigger>
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 grid gap-6">
        <div className="md:hidden">
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="w-full grid grid-cols-7">
              <TabsTrigger value="search">Search</TabsTrigger>
              <TabsTrigger value="auth">Auth</TabsTrigger>
              <TabsTrigger value="notify">Notify</TabsTrigger>
              <TabsTrigger value="cv">CV</TabsTrigger>
              <TabsTrigger value="matches">Matches</TabsTrigger>
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {tab === "search" && SearchCard}
        {tab === "auth" && AuthCard}

        {tab === "cv" && (
          <Card className="p-6 space-y-4">
            <h2 className="text-xl font-semibold">CV Upload & Status</h2>
            <div className="grid md:grid-cols-2 gap-4 items-end">
              <div>
                <Label>Pick PDF</Label>
                <Input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setCvFile(e.target.files?.[0] || null)}
                />
              </div>
              <div className="flex gap-2">
                <Button disabled={!cvFile || busy} onClick={apiPresignAndUploadCV}>
                  Upload CV
                </Button>
                <Button variant="secondary" onClick={apiCvStatus} disabled={busy}>
                  Refresh Status
                </Button>
              </div>
            </div>
            {cvStatus && (
              <div className="text-sm space-y-2">
                <div>
                  <b>PDF key:</b> {cvStatus.cv_pdf_key || "—"}
                </div>
                <div>
                  <b>Keywords key:</b> {cvStatus.cv_keywords_key || "—"}
                </div>
                <div>
                  <b>Keywords (sample):</b>{" "}
                  <code className="break-all">
                    {Array.isArray(cvStatus.keywords)
                      ? cvStatus.keywords.slice(0, 20).join(", ")
                      : "—"}
                  </code>
                </div>
              </div>
            )}
          </Card>
        )}

        {tab === "matches" && (
          <Card className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Matches</h2>
              <Button onClick={apiFetchMatches} disabled={busy}>
                Refresh
              </Button>
            </div>
            {!matches && (
              <p className="text-sm text-gray-500">No matches loaded yet.</p>
            )}
            {Array.isArray(matches) && matches.length > 0 && (
              <div className="grid gap-3">
                {matches.map((m: any, idx: number) => (
                  <Card key={idx} className="p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium">
                          {m.title || m.job_title || "Match"}
                        </div>
                        <div className="text-xs text-gray-500">
                          {m.company || m.company_name || ""}
                        </div>
                      </div>
                      <div className="text-xs">
                        {typeof m.score !== "undefined" ? (
                          <>
                            Score: <b>{Math.round((m.score || 0) * 100) / 100}</b>
                          </>
                        ) : null}
                      </div>
                    </div>
                    {m.url && (
                      <a
                        className="inline-flex items-center text-sm underline mt-2"
                        href={m.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <LinkIcon className="w-4 h-4 mr-1" />
                        Open job
                      </a>
                    )}
                    {Array.isArray(m.keywords) && m.keywords.length > 0 && (
                      <div className="mt-2 text-xs">
                        <b>Keywords:</b> {m.keywords.slice(0, 15).join(", ")}
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            )}
          </Card>
        )}

        {tab === "profile" && (
          <Card className="p-6 space-y-4">
            <h2 className="text-xl font-semibold">Profile</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <LabeledInput
                label="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <div>
                <Label>Token</Label>
                <div className="text-xs p-2 border rounded bg-gray-50 break-all">
                  {token || "—"}
                </div>
              </div>
            </div>
            <p className="text-sm text-gray-500">
              Use <code>/me</code> endpoints with the token. The UI stores it in
              local storage.
            </p>
          </Card>
        )}

        {tab === "notify" && NotificationsCard}
        {tab === "settings" && SettingsPanel}
      </main>

      {/* Toast */}
      {toast && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="fixed bottom-4 left-1/2 -translate-x-1/2"
        >
          <div className="px-4 py-2 rounded-full shadow bg-white border text-sm flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{toast}</span>
            <Button size="sm" variant="ghost" onClick={() => setToast(null)}>
              Close
            </Button>
          </div>
        </motion.div>
      )}

      {/* Debug toggle + panel */}
      {lastDebug && (
        <div className="fixed right-4 bottom-4 z-50 flex flex-col items-end gap-2">
          <Button
            size="sm"
            variant={debugOpen ? "default" : "secondary"}
            onClick={() => setDebugOpen((v) => !v)}
          >
            {debugOpen ? "Hide errors" : "Show last error"}
          </Button>
        </div>
      )}
      {debugOpen && lastDebug && (
        <div className="fixed inset-x-0 bottom-0 z-40">
          <Card className="m-4 p-4 max-w-5xl mx-auto shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="font-semibold">Last network error</div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="secondary" onClick={copyDebug}>
                  Copy JSON
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setDebugOpen(false)}
                >
                  Close
                </Button>
              </div>
            </div>
            <Separator className="my-3" />
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div>
                  <b>Time:</b> {lastDebug.ts}
                </div>
                <div className="break-all">
                  <b>URL:</b> {lastDebug.request.url}
                </div>
                <div>
                  <b>Method:</b> {lastDebug.request.method}
                </div>
                {lastDebug.error && (
                  <div className="text-red-600">
                    <b>Error:</b> {lastDebug.error}
                  </div>
                )}
                <div>
                  <b>Request headers</b>
                  <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">
                    {JSON.stringify(lastDebug.request.headers, null, 2)}
                  </pre>
                </div>
                {lastDebug.request.bodyPreview && (
                  <div>
                    <b>Request body (preview)</b>
                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">
                      {lastDebug.request.bodyPreview}
                    </pre>
                  </div>
                )}
              </div>
              <div className="space-y-2">
                <div>
                  <b>Status:</b> {lastDebug.response?.status}{" "}
                  {lastDebug.response?.statusText}
                </div>
                <div>
                  <b>Response headers</b>
                  <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">
                    {JSON.stringify(lastDebug.response?.headers ?? {}, null, 2)}
                  </pre>
                </div>
                <div>
                  <b>Response body</b>
                  <Textarea
                    readOnly
                    className="text-xs h-40"
                    value={lastDebug.response?.bodyText ?? ""}
                  />
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      <footer className="py-8 text-center text-xs text-gray-500">
        Built for the provided repo · Tweak endpoints in Settings · Password is{" "}
        <code>changeme123</code> for demo.
      </footer>
    </div>
  );
}
