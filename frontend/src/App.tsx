import { FormEvent, useState } from "react";
import { request, Session } from "./api";

type Page = "dashboard" | "orchestrate" | "agents" | "knowledge";

export function App() {
  const [session, setSession] = useState<Session | null>(null);
  if (!session) return <Login onSuccess={setSession} />;
  return <Workspace session={session} onLogout={() => setSession(null)} />;
}

function Login({ onSuccess }: { onSuccess: (session: Session) => void }) {
  const [email, setEmail] = useState("owner@example.com");
  const [password, setPassword] = useState("Password123");
  const [organization, setOrganization] = useState("Acme");
  const [mode, setMode] = useState<"login" | "register">("register");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const path = mode === "register" ? "/auth/register" : "/auth/login";
      const body = mode === "register"
        ? { email, password, full_name: "Acme Owner", organization_name: organization }
        : { email, password };
      const result = await request<{ access_token: string; organizations: { name: string }[] }>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });
      onSuccess({ accessToken: result.access_token, organizationName: result.organizations[0]?.name || organization });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "로그인에 실패했습니다.");
    }
  }

  return (
    <form className="login" onSubmit={submit}>
      <h1>SYLQENTRA</h1>
      <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="이메일" />
      <input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="비밀번호" type="password" />
      {mode === "register" && (
        <input value={organization} onChange={(event) => setOrganization(event.target.value)} placeholder="회사 이름" />
      )}
      {error && <p className="error">{error}</p>}
      <button className="primary" type="submit">{mode === "register" ? "회사 등록" : "로그인"}</button>
      <button type="button" onClick={() => setMode(mode === "register" ? "login" : "register")}>
        {mode === "register" ? "이미 계정이 있습니다" : "새 회사 등록"}
      </button>
    </form>
  );
}

function Workspace({ session, onLogout }: { session: Session; onLogout: () => void }) {
  const [page, setPage] = useState<Page>("dashboard");
  return (
    <div className="app">
      <nav>
        <strong>{session.organizationName}</strong>
        {(["dashboard", "orchestrate", "agents", "knowledge"] as Page[]).map((item) => (
          <button key={item} className={page === item ? "active" : ""} onClick={() => setPage(item)}>{item}</button>
        ))}
        <button onClick={onLogout}>로그아웃</button>
      </nav>
      <main>
        {page === "dashboard" && <Dashboard token={session.accessToken} />}
        {page === "orchestrate" && <Orchestrate token={session.accessToken} />}
        {page === "agents" && <Agents token={session.accessToken} />}
        {page === "knowledge" && <Knowledge token={session.accessToken} />}
      </main>
    </div>
  );
}

function Dashboard({ token }: { token: string }) {
  const [text, setText] = useState("대시보드를 아직 불러오지 않았습니다.");
  async function load() {
    const body = await request<Record<string, unknown>>("/dashboard", {}, token);
    setText(JSON.stringify(body, null, 2));
  }
  return <section><h2>Dashboard</h2><button className="primary" onClick={load}>불러오기</button><pre>{text}</pre></section>;
}

function Orchestrate({ token }: { token: string }) {
  const [requestText, setRequestText] = useState("이번 달 매출 보고서를 작성해줘");
  const [result, setResult] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    const body = await request<Record<string, unknown>>("/orchestrations", {
      method: "POST",
      body: JSON.stringify({ request: requestText, provider: "openai", model: "gpt-4.1" }),
    }, token);
    setResult(JSON.stringify(body, null, 2));
  }
  return <section><h2>업무 요청</h2><form onSubmit={submit}><textarea value={requestText} onChange={(event) => setRequestText(event.target.value)} /><button className="primary">실행</button></form><pre>{result}</pre></section>;
}

function Agents({ token }: { token: string }) {
  const [text, setText] = useState("");
  async function load() {
    const body = await request<unknown[]>("/agents", {}, token);
    setText(JSON.stringify(body, null, 2));
  }
  return <section><h2>Agents</h2><button className="primary" onClick={load}>목록</button><pre>{text}</pre></section>;
}

function Knowledge({ token }: { token: string }) {
  const [content, setContent] = useState("3월 매출은 420입니다.");
  const [answer, setAnswer] = useState("");
  async function upload(event: FormEvent) {
    event.preventDefault();
    await request("/knowledge/documents", {
      method: "POST",
      body: JSON.stringify({ title: "메모", filename: "note.md", content }),
    }, token);
    const body = await request<Record<string, unknown>>("/knowledge/ask", {
      method: "POST",
      body: JSON.stringify({ query: "매출은 얼마인가", provider: "openai", model: "gpt-4.1" }),
    }, token);
    setAnswer(JSON.stringify(body, null, 2));
  }
  return <section><h2>Knowledge</h2><form onSubmit={upload}><textarea value={content} onChange={(event) => setContent(event.target.value)} /><button className="primary">저장 후 질문</button></form><pre>{answer}</pre></section>;
}
