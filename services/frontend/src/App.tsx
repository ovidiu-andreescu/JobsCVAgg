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
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";

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

export default function App() {
  // DEFAULT TO PROXY PATHS
  const [umBase, setUmBase] = useLocalStorage("cfg.umBase", "/api");
  const [aggBase, setAggBase] = useLocalStorage("cfg.aggBase", "/agg");
  const [notifBase, setNotifBase] = useLocalStorage("cfg.notifBase", "/notif");

  // one-time migration away from old absolute localhost values
  useEffect(() => {
    const fix = (v: string, rel: string) =>
      v.startsWith("http://127.0.0.1") || v.startsWith("http://localhost")
        ? rel
        : v;

    const newUm = fix(umBase, "/api");
    const newAgg = fix(aggBase, "/agg");
    const newNotif = fix(notifBase, "/notif");

    if (newUm !== umBase) setUmBase(newUm);
    if (newAgg !== aggBase) setAggBase(newAgg);
    if (newNotif !== notifBase) setNotifBase(newNotif);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [email, setEmail] = useLocalStorage("auth.email", "");
  const [token, setToken] = useLocalStorage<string | null>("auth.token", null);
  const isAuthed = !!token;

  const [tab, setTab] = useState("search");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const [q, setQ] = useLocalStorage("search.q", "software engineer");
  const [loc, setLoc] = useLocalStorage("search.loc", "Bucharest, RO");
  const [page, setPage] = useLocalStorage<number>("search.page", 1);
  const [perPage, setPerPage] = useLocalStorage<number>("search.perPage", 20);
  const [jobs, setJobs] = useState<Job[] | null>(null);

  const [notifyTo, setNotifyTo] = useState("");
  const [notifySubject, setNotifySubject] = useState("JobsCVAgg test message");
  const [notifyMessage, setNotifyMessage] = useState(
    "Hello from the demo UI! ✨"
  );

  async function apiRegister() {
    setBusy(true);
    try {
      const r = await fetch(`${abs(umBase)}/auth/register`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, password: "changeme123" }),
      });
      if (!r.ok) throw new Error(`Register failed: ${r.status}`);
      setToast(
        "Registration successful. Check your inbox to verify your email."
      );
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
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, password: "changeme123" }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data?.detail || `Login failed: ${r.status}`);
      if (data?.access_token) setToken(data.access_token);
      else if (data?.ok) setToken("dummy");
      setToast("Logged in ✅");
    } catch (e: any) {
      setToast(e.message || "Login failed");
    } finally {
      setBusy(false);
    }
  }

  async function apiVerifyLink() {
    setBusy(true);
    try {
      const r = await fetch(
        `${abs(umBase)}/auth/_debug/verify_link?email=${encodeURIComponent(
          email
        )}`
      );
      const data = await r.json();
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
      const url = new URL(aggBase, window.location.origin); // supports "/agg" or absolute
      if (!url.search) {
        url.searchParams.set("q", q);
        if (loc) url.searchParams.set("location", loc);
        url.searchParams.set("page", String(page || 1));
        url.searchParams.set("results_per_page", String(perPage || 20));
      }
      const r = await fetch(url.toString());
      const data = await r.json();
      if (!r.ok) throw new Error(data?.error || `Search failed: ${r.status}`);
      setJobs(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setToast(e.message || "Search failed");
    } finally {
      setBusy(false);
    }
  }

  async function apiSendNotification() {
    setBusy(true);
    try {
      const r = await fetch(`${abs(notifBase)}/notifications/send`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          to: notifyTo || email,
          subject: notifySubject,
          message: notifyMessage,
          channel: "console",
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data?.detail || `Failed: ${r.status}`);
      setToast("Notification sent ✉️");
    } catch (e: any) {
      setToast(e.message || "Notification failed");
    } finally {
      setBusy(false);
    }
  }

  const SettingsPanel = (
    <Card className="border-0 shadow-xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2 className="w-5 h-5" /> Settings
        </CardTitle>
        <CardDescription>
          Point the UI to your running services.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div className="grid gap-2">
          <Label>User Management base URL</Label>
          <Input
            value={umBase}
            onChange={(e) => setUmBase(e.target.value)}
            placeholder="/api"
          />
        </div>
        <div className="grid gap-2">
          <Label>Job Aggregator endpoint (Lambda/API GW)</Label>
          <Input
            value={aggBase}
            onChange={(e) => setAggBase(e.target.value)}
            placeholder="/agg"
          />
        </div>
        <div className="grid gap-2">
          <Label>Notifications base URL</Label>
          <Input
            value={notifBase}
            onChange={(e) => setNotifBase(e.target.value)}
            placeholder="/notif"
          />
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
        <div className="grid gap-2">
          <Label>Email</Label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </div>
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
          <div className="grid gap-2">
            <Label>Keywords</Label>
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="e.g., Python, Data, React"
            />
          </div>
          <div className="grid gap-2">
            <Label>Location</Label>
            <Input
              value={loc}
              onChange={(e) => setLoc(e.target.value)}
              placeholder="Bucharest, RO"
            />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="grid gap-2">
              <Label>Page</Label>
              <Input
                type="number"
                value={page}
                onChange={(e) => setPage(parseInt(e.target.value || "1"))}
              />
            </div>
            <div className="grid gap-2">
              <Label>Per page</Label>
              <Input
                type="number"
                value={perPage}
                onChange={(e) => setPerPage(parseInt(e.target.value || "20"))}
              />
            </div>
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
          <div className="grid gap-2">
            <Label>To</Label>
            <Input
              value={notifyTo}
              onChange={(e) => setNotifyTo(e.target.value)}
              placeholder={email || "you@example.com"}
            />
          </div>
          <div className="grid gap-2">
            <Label>Subject</Label>
            <Input
              value={notifySubject}
              onChange={(e) => setNotifySubject(e.target.value)}
            />
          </div>
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
            <TabsList>
              <TabsTrigger value="search">Search</TabsTrigger>
              <TabsTrigger value="auth">Auth</TabsTrigger>
              <TabsTrigger value="notify">Notify</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 grid gap-6">
        <div className="md:hidden">
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="w-full grid grid-cols-4">
              <TabsTrigger value="search">Search</TabsTrigger>
              <TabsTrigger value="auth">Auth</TabsTrigger>
              <TabsTrigger value="notify">Notify</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {tab === "search" && SearchCard}
        {tab === "auth" && AuthCard}
        {tab === "notify" && NotificationsCard}
        {tab === "settings" && SettingsPanel}
      </main>

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

      <footer className="py-8 text-center text-xs text-gray-500">
        Built for the provided repo · Tweak endpoints in Settings · Password is
        hardcoded as <code>changeme123</code> for demo.
      </footer>
    </div>
  );
}
