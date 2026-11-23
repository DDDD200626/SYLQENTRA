import { FormEvent, ReactNode, useCallback, useEffect, useState } from "react";
import { request, Session } from "./api";

type PageId = "dashboard" | "orchestrations" | "agents" | "knowledge" | "automation";

type DashboardData = {
  organization_id: string;
  agent_count: number;
  pending_approvals: number;
  total_tokens: number;
  estimated_cost: string | number;
  tasks: Record<string, number>;
};

type AgentRow = {
  id: string;
  name: string;
  role: string;
  description: string;
  model_provider: string | null;
  model_name: string | null;
  is_active: boolean;
};

type OrchestrationResult = {
  task_id: string;
  status: string;
  plan: string[];
  outputs: Record<string, string>;
  final_output: string;
  error: string;
};

type AskResult = {
  answer?: string;
  sources?: { document_id: string; chunk_index: number }[];
};

const PAGES: { id: PageId; path: string; label: string; description: string }[] = [
  { id: "dashboard", path: "/dashboard", label: "현황", description: "조직의 작업 현황과 사용량" },
  { id: "knowledge", path: "/knowledge", label: "문서", description: "회사 문서를 저장하고, 그 내용으로 질문합니다" },
  { id: "agents", path: "/agents", label: "에이전트", description: "역할을 나눈 에이전트가 이 회사에서 대기합니다" },
  { id: "orchestrations", path: "/orchestrations", label: "실행", description: "업무 요청을 계획하고 검토까지 진행합니다" },
  { id: "automation", path: "/automation", label: "자동화", description: "에이전트 단계를 워크플로로 저장하고 실행합니다" },
];

type CatalogPlan = {
  name: string;
  monthly_token_limit: number;
  price_krw: number | null;
  description: string;
};

const PLAN_CATALOG: CatalogPlan[] = [
  { name: "free", monthly_token_limit: 100000, price_krw: 0, description: "기본 Agent와 제한된 작업" },
  { name: "starter", monthly_token_limit: 500000, price_krw: 49000, description: "개인 업무 자동화" },
  { name: "team", monthly_token_limit: 2000000, price_krw: 190000, description: "팀 단위 Agent와 Workflow" },
  { name: "business", monthly_token_limit: 10000000, price_krw: 790000, description: "기업용 업무 자동화" },
  { name: "enterprise", monthly_token_limit: 50000000, price_krw: null, description: "멀티 조직과 고급 관리" },
];

const PLAN_LABELS: Record<string, string> = {
  free: "Free",
  starter: "Starter",
  team: "Team",
  business: "Business",
  enterprise: "Enterprise",
};

const STAGES = [
  { step: "01", name: "이해", body: "회사 문서를 저장하고, 그 내용에서 근거를 찾아 답합니다." },
  { step: "02", name: "실행", body: "조사, 데이터, 개발, 문서, 검토, 자동화 에이전트가 맡은 일을 수행합니다." },
  { step: "03", name: "협업", body: "매니저가 역할을 나누고, 전문 에이전트의 결과를 모아 검토합니다." },
  { step: "04", name: "운영", body: "승인, 사용량, 요금제로 실행을 통제하고 다음 달에도 같은 한도로 운영합니다." },
];

const PRODUCTS = [
  {
    href: "/knowledge",
    kicker: "문서 운영",
    title: "문서",
    body: "정책, 보고서, 메모를 저장하고 그 맥락으로 답을 받습니다.",
  },
  {
    href: "/orchestrations",
    kicker: "에이전트 운영",
    title: "에이전트",
    body: "매니저가 역할을 나누고, 전문 에이전트가 실행한 뒤 검토합니다.",
  },
  {
    href: "/automation",
    kicker: "업무 자동화",
    title: "자동화",
    body: "데이터 분석과 문서 작성을 하나의 워크플로로 저장해 다시 실행합니다.",
  },
];

const TASK_LABELS: { key: string; label: string }[] = [
  { key: "total", label: "전체" },
  { key: "pending", label: "대기" },
  { key: "planning", label: "계획" },
  { key: "running", label: "실행 중" },
  { key: "reviewing", label: "검토" },
  { key: "awaiting_approval", label: "승인 대기" },
  { key: "completed", label: "완료" },
  { key: "failed", label: "실패" },
  { key: "cancelled", label: "취소" },
];

function normalizePath(pathname: string) {
  if (!pathname) return "/";
  if (pathname.length > 1 && pathname.endsWith("/")) return pathname.slice(0, -1);
  return pathname;
}

function useRoute() {
  const [path, setPath] = useState(() => normalizePath(window.location.pathname));

  useEffect(() => {
    const sync = () => setPath(normalizePath(window.location.pathname));
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  const navigate = useCallback((next: string, replace = false) => {
    const target = normalizePath(next);
    if (normalizePath(window.location.pathname) !== target) {
      window.history[replace ? "replaceState" : "pushState"](null, "", target);
    }
    setPath(target);
    document.title = "SYLQENTRA";
  }, []);

  return { path, navigate };
}

export function App() {
  const [session, setSession] = useState<Session | null>(null);
  const { path, navigate } = useRoute();
  const page = PAGES.find((item) => item.path === path);

  useEffect(() => {
    document.title = "SYLQENTRA";
  }, [path]);

  useEffect(() => {
    if (session && (path === "/login" || path === "/register")) {
      navigate("/dashboard", true);
    } else if (!session && page) {
      navigate("/login", true);
    }
  }, [session, path, page, navigate]);

  if (!session) {
    if (page) return null;
    if (path === "/login" || path === "/register") {
      return (
        <Login
          mode={path === "/register" ? "register" : "login"}
          onNavigate={navigate}
          onSuccess={(next) => {
            setSession(next);
            navigate("/dashboard");
          }}
        />
      );
    }
    if (path !== "/") return <NotFound onNavigate={navigate} signedIn={false} />;
    return <Landing onNavigate={navigate} />;
  }

  if (!page) return <NotFound onNavigate={navigate} signedIn />;

  return (
    <Workspace
      session={session}
      page={page}
      onNavigate={navigate}
      onLogout={() => {
        setSession(null);
        navigate("/", true);
      }}
    />
  );
}

function Landing({ onNavigate }: { onNavigate: (path: string) => void }) {
  return (
    <div>
      <header className="site-header">
        <a className="logo" href="/" onClick={(event) => go(event, onNavigate, "/")}>
          <span className="logo-mark">S</span>
          SYLQENTRA
        </a>
        <nav className="site-nav" aria-label="제품">
          <a href="#stages">진화</a>
          <a href="#products">제품</a>
          <a href="#pricing">요금</a>
          <a href="#faq">질문</a>
        </nav>
        <div className="header-actions">
          <a className="btn" href="/login" onClick={(event) => go(event, onNavigate, "/login")}>
            로그인
          </a>
          <a className="btn btn-dark" href="/register" onClick={(event) => go(event, onNavigate, "/register")}>
            시작하기
          </a>
        </div>
      </header>
      <section className="hero">
        <div>
          <p className="eyebrow">Enterprise Agentic AI</p>
          <h1>도입에서 멈추지 않고, 운영으로 이어지는 기업 AI.</h1>
          <p className="hero-copy">
            SYLQENTRA는 이해, 실행, 협업, 운영을 한 플랫폼에 둡니다. 에이전트와 문서, 승인, 월 사용 한도를 회사 자산으로 남깁니다.
          </p>
          <div className="hero-actions">
            <a className="btn btn-dark" href="#pricing">
              요금 보기
            </a>
            <a className="btn" href="/register" onClick={(event) => go(event, onNavigate, "/register")}>
              Free로 시작
            </a>
          </div>
        </div>
        <aside className="hero-panel">
          <p className="eyebrow">월간 매출 보고</p>
          <ol>
            <li>데이터 에이전트가 숫자를 읽습니다.</li>
            <li>문서 에이전트가 보고서를 작성합니다.</li>
            <li>검토 에이전트가 결과를 확인합니다.</li>
          </ol>
        </aside>
      </section>
      <section className="section" id="stages">
        <p className="eyebrow">01 이해 · 02 실행 · 03 협업 · 04 운영</p>
        <h2>한 번 만든 에이전트와 지식을 다음 업무로 확장합니다.</h2>
        <div className="feature-grid" style={{ marginTop: 28 }}>
          {STAGES.map((stage) => (
            <article className="feature" key={stage.step}>
              <p className="eyebrow">{stage.step}</p>
              <h3>{stage.name}</h3>
              <p>{stage.body}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="section">
        <h2>파일럿에서 멈추지 않게, 운영에 필요한 통제를 넣었습니다.</h2>
        <div className="feature-grid" style={{ marginTop: 28 }}>
          <article className="feature">
            <h3>문서의 맥락</h3>
            <p>저장된 문서에서 근거를 찾아 답합니다.</p>
          </article>
          <article className="feature">
            <h3>역할의 분업</h3>
            <p>조사, 데이터, 개발, 문서, 검토, 자동화가 각자 맡은 일을 수행합니다.</p>
          </article>
          <article className="feature">
            <h3>사람의 승인</h3>
            <p>이메일과 Slack은 승인 대기 상태로 남고, 결정 전에는 발송하지 않습니다.</p>
          </article>
          <article className="feature">
            <h3>기존 도구 연결</h3>
            <p>GitHub 이슈와 Slack 메시지를 같은 업무 흐름에 붙입니다.</p>
          </article>
        </div>
      </section>
      <section className="section" id="products">
        <p className="eyebrow">제품</p>
        <h2>시작부터 실행까지, 세 가지로 나뉩니다.</h2>
        <div className="product-grid" style={{ marginTop: 28 }}>
          {PRODUCTS.map((product) => (
            <a
              key={product.href}
              className="product-card"
              href="/login"
              onClick={(event) => go(event, onNavigate, "/login")}
            >
              <p className="eyebrow">{product.kicker}</p>
              <h3>{product.title}</h3>
              <p>{product.body}</p>
              <span>콘솔에서 열기</span>
            </a>
          ))}
        </div>
      </section>
      <section className="section" id="flow">
        <div className="scenario-grid">
          <article className="scenario">
            <p className="eyebrow">업무 시나리오</p>
            <h2>보고서 요청 한 번으로 계획, 작성, 검토가 이어집니다.</h2>
            <p>콘솔의 실행 화면에 업무를 적으면 매니저가 필요한 역할을 고르고, 각 에이전트의 산출물을 모읍니다.</p>
          </article>
          <article className="scenario">
            <p className="eyebrow">운영 단위</p>
            <p className="stat">
              7
              <small>회사마다 준비되는 기본 에이전트</small>
            </p>
            <p className="stat">
              3
              <small>문서, 에이전트, 자동화</small>
            </p>
          </article>
        </div>
      </section>
      <section className="section" id="pricing">
        <p className="eyebrow">요금</p>
        <h2>월 토큰 한도로 고르는 사용 계획.</h2>
        <p className="section-intro">
          표시 금액은 월 구독 안내 가격입니다. 콘솔에서 요금제를 바꾸면 그 달의 토큰 한도가 바뀝니다. 카드 결제는 연결되어 있지 않습니다.
        </p>
        <div className="price-grid">
          {PLAN_CATALOG.map((plan) => (
            <article className={plan.name === "team" ? "price-card featured" : "price-card"} key={plan.name}>
              <p className="eyebrow">{PLAN_LABELS[plan.name]}</p>
              <p className="price">{plan.price_krw === null ? "문의" : plan.price_krw === 0 ? "무료" : `${plan.price_krw.toLocaleString("ko-KR")}원`}</p>
              <p>{plan.description}</p>
              <p className="meta">월 {plan.monthly_token_limit.toLocaleString("ko-KR")} 토큰</p>
              <a className="btn btn-dark" href="/register" onClick={(event) => go(event, onNavigate, "/register")}>
                {plan.price_krw === null ? "도입 상담" : "이 요금으로 시작"}
              </a>
            </article>
          ))}
        </div>
      </section>
      <section className="section" id="faq">
        <h2>자주 묻는 질문</h2>
        <div className="faq" style={{ marginTop: 20 }}>
          <details open>
            <summary>SYLQENTRA는 어떤 플랫폼인가요?</summary>
            <p>한 회사의 업무 요청을 여러 에이전트가 나누어 처리하고, 문서와 워크플로로 남기는 자동화 콘솔입니다.</p>
          </details>
          <details>
            <summary>기존 시스템을 교체해야 하나요?</summary>
            <p>아닙니다. 문서를 올리고, 에이전트에게 일을 맡기고, 필요한 경우 GitHub와 Slack으로 결과를 넘깁니다.</p>
          </details>
          <details>
            <summary>사람이 결과를 승인할 수 있나요?</summary>
            <p>이메일과 Slack 도구는 승인 전에는 보내지 않습니다. 현황 화면에서 승인 대기 건수를 확인합니다.</p>
          </details>
          <details>
            <summary>특정 모델만 써야 하나요?</summary>
            <p>OpenAI, Claude, Gemini 중에서 호출할 공급자를 고릅니다. 키가 없으면 해당 호출은 실행되지 않습니다.</p>
          </details>
          <details>
            <summary>요금은 어떻게 적용되나요?</summary>
            <p>회사는 Free로 시작합니다. 콘솔에서 Starter, Team, Business, Enterprise로 바꾸면 월 토큰 한도가 그 요금제에 맞게 바뀝니다. 결제 대행은 아직 연결되어 있지 않습니다.</p>
          </details>
        </div>
      </section>
      <section className="closing">
        <div>
          <h2>업무의 시작과 끝을 한 화면에 두세요.</h2>
          <p>회사를 등록하면 기본 에이전트와 콘솔이 바로 열립니다.</p>
        </div>
        <a className="btn" href="/register" onClick={(event) => go(event, onNavigate, "/register")}>
          시작하기
        </a>
      </section>
      <footer className="site-footer">SYLQENTRA · 문서, 에이전트, 자동화</footer>
    </div>
  );
}

function go(event: { preventDefault: () => void; metaKey: boolean; ctrlKey: boolean; shiftKey: boolean; altKey: boolean; button: number }, navigate: (path: string) => void, path: string) {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
  event.preventDefault();
  navigate(path);
}

function Login({
  mode,
  onSuccess,
  onNavigate,
}: {
  mode: "login" | "register";
  onSuccess: (session: Session) => void;
  onNavigate: (path: string) => void;
}) {
  const [email, setEmail] = useState("owner@example.com");
  const [password, setPassword] = useState("Password123");
  const [organization, setOrganization] = useState("Acme");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setPending(true);
    try {
      const path = mode === "register" ? "/auth/register" : "/auth/login";
      const body =
        mode === "register"
          ? { email, password, full_name: "Acme Owner", organization_name: organization }
          : { email, password };
      const result = await request<{ access_token: string; organizations: { name: string }[] }>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });
      onSuccess({ accessToken: result.access_token, organizationName: result.organizations[0]?.name || organization });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "로그인에 실패했습니다.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="auth-screen">
      <section className="auth-story">
        <a className="logo" href="/" onClick={(event) => go(event, onNavigate, "/")} style={{ color: "#fff" }}>
          <span className="logo-mark">S</span>
          SYLQENTRA
        </a>
        <div>
          <h1>문서, 에이전트, 자동화를 한 흐름으로.</h1>
          <p>회사를 등록하면 일곱 명의 기본 에이전트가 준비됩니다.</p>
        </div>
      </section>
      <form className="auth-card" onSubmit={submit}>
        <h1>{mode === "register" ? "회사 등록" : "로그인"}</h1>
        <p className="lede">{mode === "register" ? "회사와 소유자 계정을 만듭니다." : "등록된 회사 계정으로 들어갑니다."}</p>
        <label className="field">
          <span>이메일</span>
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            autoComplete="username"
            required
          />
        </label>
        <label className="field">
          <span>비밀번호</span>
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            autoComplete={mode === "register" ? "new-password" : "current-password"}
            required
          />
        </label>
        {mode === "register" && (
          <label className="field">
            <span>회사</span>
            <input
              value={organization}
              onChange={(event) => setOrganization(event.target.value)}
              autoComplete="organization"
              required
            />
          </label>
        )}
        {error && (
          <p className="banner error" role="alert">
            {error}
          </p>
        )}
        <button className="btn btn-dark btn-block" type="submit" disabled={pending}>
          {pending ? "처리 중" : mode === "register" ? "회사 등록" : "로그인"}
        </button>
        <button
          className="btn btn-block"
          type="button"
          onClick={() => onNavigate(mode === "register" ? "/" : "/register")}
        >
          {mode === "register" ? "로그인" : "회원가입"}
        </button>
      </form>
    </div>
  );
}

function Workspace({
  session,
  page,
  onNavigate,
  onLogout,
}: {
  session: Session;
  page: (typeof PAGES)[number];
  onNavigate: (path: string) => void;
  onLogout: () => void;
}) {
  return (
    <div className="console">
      <header className="console-bar">
        <a className="logo" href="/dashboard" onClick={(event) => go(event, onNavigate, "/dashboard")}>
          <span className="logo-mark">S</span>
          SYLQENTRA
        </a>
        <nav className="console-nav" aria-label="주 메뉴">
          {PAGES.map((item) => (
            <a
              key={item.id}
              href={item.path}
              className={page.id === item.id ? "active" : undefined}
              aria-current={page.id === item.id ? "page" : undefined}
              onClick={(event) => go(event, onNavigate, item.path)}
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="console-meta">
          <span className="org-chip">{session.organizationName}</span>
          <button className="btn" type="button" onClick={onLogout}>
            로그아웃
          </button>
        </div>
      </header>
      <main>
        {page.id === "dashboard" && <Dashboard token={session.accessToken} />}
        {page.id === "orchestrations" && <Orchestrate token={session.accessToken} />}
        {page.id === "agents" && <Agents token={session.accessToken} />}
        {page.id === "knowledge" && <Knowledge token={session.accessToken} />}
        {page.id === "automation" && <Automation token={session.accessToken} />}
      </main>
    </div>
  );
}

function PageHeading({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}

function PlanBoard({ token }: { token: string }) {
  const [current, setCurrent] = useState("free");
  const [plans, setPlans] = useState<CatalogPlan[]>(PLAN_CATALOG);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");

  useEffect(() => {
    void request<CatalogPlan[]>("/plans")
      .then((body) => {
        if (body.length) setPlans(body);
      })
      .catch(() => setPlans(PLAN_CATALOG));
    void request<{ plan?: string }>("/organizations/current", {}, token)
      .then((body) => setCurrent(body.plan || "free"))
      .catch(() => setCurrent("free"));
  }, [token]);

  async function choose(name: string) {
    setPending(name);
    setError("");
    setMessage("");
    try {
      const body = await request<{ plan: string }>(
        "/organizations/current/plan",
        { method: "PUT", body: JSON.stringify({ plan: name }) },
        token,
      );
      setCurrent(body.plan);
      setMessage(`${PLAN_LABELS[body.plan] || body.plan} 요금제로 바뀌었습니다. 카드 결제는 청구되지 않습니다.`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "요금제를 바꾸지 못했습니다.");
    } finally {
      setPending("");
    }
  }

  return (
    <article className="card" style={{ marginBottom: 14 }}>
      <h2>요금제</h2>
      <p className="meta">현재 {PLAN_LABELS[current] || current}. 바꾸면 월 토큰 한도만 갱신됩니다.</p>
      <div className="price-grid" style={{ marginTop: 16 }}>
        {plans.map((plan) => (
          <div className={plan.name === current ? "price-card featured" : "price-card"} key={plan.name}>
            <p className="eyebrow">{PLAN_LABELS[plan.name] || plan.name}</p>
            <p className="price">{plan.price_krw === null ? "문의" : plan.price_krw === 0 ? "무료" : `${plan.price_krw.toLocaleString("ko-KR")}원`}</p>
            <p className="meta">월 {plan.monthly_token_limit.toLocaleString("ko-KR")} 토큰</p>
            <button className="btn btn-dark" type="button" disabled={pending === plan.name || plan.name === current} onClick={() => void choose(plan.name)}>
              {plan.name === current ? "사용 중" : pending === plan.name ? "변경 중" : "이 요금으로 변경"}
            </button>
          </div>
        ))}
      </div>
      {message && <p className="meta">{message}</p>}
      {error && <p className="banner error" role="alert">{error}</p>}
    </article>
  );
}

function Dashboard({ token }: { token: string }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const load = useCallback(async () => {
    setPending(true);
    setError("");
    try {
      const body = await request<DashboardData>("/dashboard", {}, token);
      setData(body);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "대시보드를 불러오지 못했습니다.");
    } finally {
      setPending(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const page = PAGES.find((item) => item.id === "dashboard")!;
  return (
    <section>
      <PageHeading
        title={page.label}
        description={page.description}
        action={
          <button className="btn btn-dark" type="button" onClick={() => void load()} disabled={pending}>
            {pending ? "불러오는 중" : "새로고침"}
          </button>
        }
      />
      {error && (
        <p className="banner error" role="alert">
          {error}
        </p>
      )}
      {!data && !error && <p className="empty">대시보드를 불러오는 중입니다.</p>}
      {!data && error && <p className="empty">표시할 현황이 없습니다.</p>}
      {data && (
        <>
          <PlanBoard token={token} />
          <div className="metrics">
            <article className="card">
              <p className="metric-label">에이전트</p>
              <p className="metric-value">{formatCount(data.agent_count)}</p>
            </article>
            <article className="card">
              <p className="metric-label">승인 대기</p>
              <p className="metric-value">{formatCount(data.pending_approvals)}</p>
            </article>
            <article className="card">
              <p className="metric-label">토큰</p>
              <p className="metric-value">{formatCount(data.total_tokens)}</p>
            </article>
            <article className="card">
              <p className="metric-label">예상 비용</p>
              <p className="metric-value">{String(data.estimated_cost)}</p>
            </article>
          </div>
          <article className="card">
            <h2>작업 현황</h2>
            <table>
              <thead>
                <tr>
                  <th>상태</th>
                  <th>건수</th>
                </tr>
              </thead>
              <tbody>
                {TASK_LABELS.map((item) => (
                  <tr key={item.key}>
                    <td>{item.label}</td>
                    <td>{formatCount(data.tasks?.[item.key] ?? 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </article>
          <p className="meta">조직 ID {data.organization_id}</p>
        </>
      )}
    </section>
  );
}

function Orchestrate({ token }: { token: string }) {
  const [requestText, setRequestText] = useState("이번 달 매출 보고서를 작성해줘");
  const [result, setResult] = useState<OrchestrationResult | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const page = PAGES.find((item) => item.id === "orchestrations")!;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    setResult(null);
    try {
      const body = await request<OrchestrationResult>(
        "/orchestrations",
        {
          method: "POST",
          body: JSON.stringify({ request: requestText, provider: "openai", model: "gpt-4.1" }),
        },
        token,
      );
      setResult(body);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "오케스트레이션 요청에 실패했습니다.");
    } finally {
      setPending(false);
    }
  }

  const outputs = result ? Object.entries(result.outputs || {}) : [];

  return (
    <section>
      <PageHeading title={page.label} description={page.description} />
      <form className="card form-card" onSubmit={submit}>
        <label className="field">
          <span>업무 요청</span>
          <textarea value={requestText} onChange={(event) => setRequestText(event.target.value)} required />
        </label>
        <p className="meta">제공자 openai · 모델 gpt-4.1</p>
        <button className="btn btn-dark" type="submit" disabled={pending}>
          {pending ? "실행 중" : "실행"}
        </button>
      </form>
      {error && (
        <p className="banner error" role="alert">
          {error}
        </p>
      )}
      {!result && !error && <p className="empty">아직 실행 결과가 없습니다.</p>}
      {result && (
        <article className="card">
          <h2>실행 결과</h2>
          <dl className="facts">
            <div>
              <dt>작업 ID</dt>
              <dd>{result.task_id || "—"}</dd>
            </div>
            <div>
              <dt>상태</dt>
              <dd>{result.status || "—"}</dd>
            </div>
          </dl>
          <h3>계획</h3>
          {result.plan?.length ? (
            <ol className="plan">
              {result.plan.map((step, index) => (
                <li key={`${index}-${step}`}>{step}</li>
              ))}
            </ol>
          ) : (
            <p className="empty">반환된 계획이 없습니다.</p>
          )}
          <h3>산출물</h3>
          {outputs.length ? (
            <ul className="stack">
              {outputs.map(([name, value]) => (
                <li key={name}>
                  <strong>{name}</strong>
                  <p>{value}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty">반환된 산출물이 없습니다.</p>
          )}
          <h3>최종 결과</h3>
          <p className="prose">{result.final_output || "최종 결과가 없습니다."}</p>
          {result.error && (
            <p className="banner error" role="alert">
              {result.error}
            </p>
          )}
        </article>
      )}
    </section>
  );
}

function Agents({ token }: { token: string }) {
  const [rows, setRows] = useState<AgentRow[] | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const page = PAGES.find((item) => item.id === "agents")!;

  const load = useCallback(async () => {
    setPending(true);
    setError("");
    try {
      const body = await request<AgentRow[]>("/agents", {}, token);
      setRows(body);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "에이전트 목록을 불러오지 못했습니다.");
    } finally {
      setPending(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section>
      <PageHeading
        title={page.label}
        description={page.description}
        action={
          <button className="btn btn-dark" type="button" onClick={() => void load()} disabled={pending}>
            {pending ? "불러오는 중" : "목록"}
          </button>
        }
      />
      {error && (
        <p className="banner error" role="alert">
          {error}
        </p>
      )}
      {!rows && !error && <p className="empty">에이전트 목록을 불러오는 중입니다.</p>}
      {rows && rows.length === 0 && <p className="empty">등록된 에이전트가 없습니다.</p>}
      {rows && rows.length > 0 && (
        <article className="card">
          <table>
            <thead>
              <tr>
                <th>이름</th>
                <th>역할</th>
                <th>설명</th>
                <th>모델</th>
                <th>상태</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((agent) => (
                <tr key={agent.id}>
                  <td>{agent.name}</td>
                  <td>{agent.role}</td>
                  <td>{agent.description}</td>
                  <td>
                    {agent.model_provider || "미지정"}
                    {agent.model_name ? ` · ${agent.model_name}` : ""}
                  </td>
                  <td>{agent.is_active ? "사용" : "중지"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      )}
    </section>
  );
}

function Knowledge({ token }: { token: string }) {
  const [content, setContent] = useState("3월 매출은 420입니다.");
  const [answer, setAnswer] = useState<AskResult | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const page = PAGES.find((item) => item.id === "knowledge")!;

  async function upload(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    setAnswer(null);
    try {
      await request(
        "/knowledge/documents",
        {
          method: "POST",
          body: JSON.stringify({ title: "메모", filename: "note.md", content }),
        },
        token,
      );
      const body = await request<AskResult>(
        "/knowledge/ask",
        {
          method: "POST",
          body: JSON.stringify({ query: "매출은 얼마인가", provider: "openai", model: "gpt-4.1" }),
        },
        token,
      );
      setAnswer(body);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "지식 요청에 실패했습니다.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section>
      <PageHeading title={page.label} description={page.description} />
      <form className="card form-card" onSubmit={upload}>
        <dl className="facts">
          <div>
            <dt>문서 제목</dt>
            <dd>메모</dd>
          </div>
          <div>
            <dt>파일 이름</dt>
            <dd>note.md</dd>
          </div>
          <div>
            <dt>질문</dt>
            <dd>매출은 얼마인가</dd>
          </div>
        </dl>
        <label className="field">
          <span>문서 내용</span>
          <textarea value={content} onChange={(event) => setContent(event.target.value)} required />
        </label>
        <button className="btn btn-dark" type="submit" disabled={pending}>
          {pending ? "처리 중" : "저장 후 질문"}
        </button>
      </form>
      {error && (
        <p className="banner error" role="alert">
          {error}
        </p>
      )}
      {!answer && !error && <p className="empty">저장한 문서에 대한 답변이 아직 없습니다.</p>}
      {answer && (
        <article className="card">
          <h2>답변</h2>
          <p className="prose">{answer.answer || "답변 본문이 없습니다."}</p>
          <h3>출처</h3>
          {answer.sources?.length ? (
            <ul className="stack">
              {answer.sources.map((source) => (
                <li key={`${source.document_id}-${source.chunk_index}`}>
                  문서 {source.document_id} · 조각 {source.chunk_index}
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty">연결된 출처가 없습니다.</p>
          )}
        </article>
      )}
    </section>
  );
}

type WorkflowRow = { id: string; name: string; schedule_cron: string | null; is_active: boolean };

function Automation({ token }: { token: string }) {
  const [name, setName] = useState("월간 매출 보고");
  const [taskInput, setTaskInput] = useState("1월 100, 2월 130. 매출 보고서를 작성해줘");
  const [rows, setRows] = useState<WorkflowRow[] | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const page = PAGES.find((item) => item.id === "automation")!;

  const load = useCallback(async () => {
    const body = await request<WorkflowRow[]>("/workflows", {}, token);
    setRows(body);
  }, [token]);

  useEffect(() => {
    void load().catch((caught: unknown) => {
      setError(caught instanceof Error ? caught.message : "워크플로를 불러오지 못했습니다.");
    });
  }, [load]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    setStatus("");
    try {
      const created = await request<{ id: string }>(
        "/workflows",
        {
          method: "POST",
          body: JSON.stringify({
            name,
            description: "데이터 에이전트가 숫자를 읽고 문서 에이전트가 보고서를 씁니다.",
            schedule_cron: "0 9 * * 1",
            nodes: [
              { node_key: "analyze", node_type: "agent", config: { role: "data" } },
              { node_key: "write", node_type: "agent", config: { role: "document" } },
            ],
            edges: [{ source: "analyze", target: "write" }],
          }),
        },
        token,
      );
      const executed = await request<{ status: string }>(
        `/workflows/${created.id}/execute`,
        {
          method: "POST",
          body: JSON.stringify({ provider: "openai", model: "gpt-4.1", task_input: taskInput }),
        },
        token,
      );
      setStatus(executed.status);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "워크플로 실행에 실패했습니다.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section>
      <PageHeading title={page.label} description={page.description} />
      <form className="card form-card" onSubmit={submit}>
        <label className="field">
          <span>워크플로 이름</span>
          <input value={name} onChange={(event) => setName(event.target.value)} required />
        </label>
        <label className="field">
          <span>실행할 업무</span>
          <textarea value={taskInput} onChange={(event) => setTaskInput(event.target.value)} required />
        </label>
        <p className="meta">순서: 데이터 에이전트 → 문서 에이전트. 저장되는 일정은 매주 월요일 09:00입니다.</p>
        <button className="btn btn-dark" type="submit" disabled={pending}>
          {pending ? "실행 중" : "저장 후 실행"}
        </button>
      </form>
      {error && (
        <p className="banner error" role="alert">
          {error}
        </p>
      )}
      {status && <p className="meta">마지막 실행 상태 {status}</p>}
      {!rows && !error && <p className="empty">워크플로를 불러오는 중입니다.</p>}
      {rows && rows.length === 0 && <p className="empty">저장된 워크플로가 없습니다.</p>}
      {rows && rows.length > 0 && (
        <article className="card">
          <table>
            <thead>
              <tr>
                <th>이름</th>
                <th>일정</th>
                <th>상태</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>{row.name}</td>
                  <td>{row.schedule_cron || "없음"}</td>
                  <td>{row.is_active ? "사용" : "중지"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      )}
    </section>
  );
}

function NotFound({ onNavigate, signedIn }: { onNavigate: (path: string) => void; signedIn: boolean }) {
  return (
    <div className="auth-screen">
      <div className="auth-card">
        <p className="brand-name">SYLQENTRA</p>
        <h1>페이지를 찾을 수 없습니다</h1>
        <p className="lede">요청한 주소에 해당하는 화면이 없습니다.</p>
        <button className="btn btn-dark" type="button" onClick={() => onNavigate(signedIn ? "/dashboard" : "/")}>
          {signedIn ? "대시보드" : "로그인"}
        </button>
      </div>
    </div>
  );
}

function formatCount(value: number) {
  return Number.isFinite(value) ? value.toLocaleString("ko-KR") : "—";
}
