import { FormEvent, PointerEvent, useCallback, useEffect, useState } from "react";
import { request } from "./api";

const ROLES = ["research", "data", "developer", "document", "review", "automation", "manager"] as const;

type Role = (typeof ROLES)[number];

type BoardNode = { key: string; role: Role; x: number; y: number };

type BoardEdge = { source: string; target: string };

type WorkflowSummary = { id: string; name: string; schedule_cron: string | null; is_active: boolean };

type WorkflowDetail = WorkflowSummary & {
  description: string;
  nodes: { node_key: string; config: { role?: string }; position?: { x?: number; y?: number } }[];
  edges: BoardEdge[];
};

const ROLE_LABEL: Record<Role, string> = {
  research: "조사",
  data: "데이터",
  developer: "개발",
  document: "문서",
  review: "검토",
  automation: "자동화",
  manager: "매니저",
};

export function WorkflowBoard({ token }: { token: string }) {
  const [name, setName] = useState("월간 매출 보고");
  const [taskInput, setTaskInput] = useState("1월 100, 2월 130. 매출 보고서를 작성해줘");
  const [nodes, setNodes] = useState<BoardNode[]>([
    { key: "analyze", role: "data", x: 40, y: 80 },
    { key: "write", role: "document", x: 280, y: 80 },
  ]);
  const [edges, setEdges] = useState<BoardEdge[]>([{ source: "analyze", target: "write" }]);
  const [selected, setSelected] = useState<string | null>(null);
  const [saved, setSaved] = useState<WorkflowSummary[] | null>(null);
  const [activeId, setActiveId] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const load = useCallback(async () => {
    const body = await request<WorkflowSummary[]>("/workflows", {}, token);
    setSaved(body);
  }, [token]);

  useEffect(() => {
    void load().catch((caught: unknown) => {
      setError(caught instanceof Error ? caught.message : "워크플로를 불러오지 못했습니다.");
    });
  }, [load]);

  function addRole(role: Role) {
    const key = `${role}-${nodes.length + 1}`;
    setNodes((current) => [...current, { key, role, x: 40 + (current.length % 4) * 180, y: 40 + Math.floor(current.length / 4) * 110 }]);
  }

  function choose(key: string) {
    if (selected && selected !== key) {
      setEdges((current) =>
        current.some((edge) => edge.source === selected && edge.target === key) ? current : [...current, { source: selected, target: key }],
      );
      setSelected(null);
      return;
    }
    setSelected(key);
  }

  function move(key: string, event: PointerEvent<HTMLButtonElement>) {
    const board = event.currentTarget.parentElement?.getBoundingClientRect();
    if (!board) return;
    const x = Math.max(8, event.clientX - board.left - 60);
    const y = Math.max(8, event.clientY - board.top - 22);
    setNodes((current) => current.map((node) => (node.key === key ? { ...node, x, y } : node)));
  }

  async function openSaved(id: string) {
    setError("");
    const detail = await request<WorkflowDetail>(`/workflows/${id}`, {}, token);
    setActiveId(id);
    setName(detail.name);
    setNodes(
      detail.nodes.map((node, index) => ({
        key: node.node_key,
        role: (ROLES.includes(node.config.role as Role) ? node.config.role : "data") as Role,
        x: node.position?.x ?? 40 + index * 180,
        y: node.position?.y ?? 80,
      })),
    );
    setEdges(detail.edges);
    setSelected(null);
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (nodes.length === 0) {
      setError("에이전트 노드를 하나 이상 놓으세요.");
      return;
    }
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
            description: "화면에서 배치한 에이전트 순서",
            schedule_cron: null,
            nodes: nodes.map((node) => ({
              node_key: node.key,
              node_type: "agent",
              config: { role: node.role },
              position: { x: node.x, y: node.y },
            })),
            edges,
          }),
        },
        token,
      );
      setActiveId(created.id);
      const executed = await request<{ status: string }>(
        `/workflows/${created.id}/execute`,
        { method: "POST", body: JSON.stringify({ provider: "openai", model: "gpt-4.1", task_input: taskInput }) },
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
    <form onSubmit={save}>
      <div className="palette">
        {ROLES.map((role) => (
          <button key={role} className="btn" type="button" onClick={() => addRole(role)}>
            {ROLE_LABEL[role]}
          </button>
        ))}
      </div>
      <p className="meta">노드를 누른 뒤 다른 노드를 누르면 화살표가 연결됩니다. 노드를 드래그하면 위치가 저장됩니다.</p>
      <div className="board" aria-label="워크플로 캔버스">
        <svg className="board-lines">
          {edges.map((edge) => {
            const source = nodes.find((node) => node.key === edge.source);
            const target = nodes.find((node) => node.key === edge.target);
            if (!source || !target) return null;
            return (
              <line
                key={`${edge.source}-${edge.target}`}
                x1={source.x + 64}
                y1={source.y + 24}
                x2={target.x + 64}
                y2={target.y + 24}
              />
            );
          })}
        </svg>
        {nodes.map((node) => (
          <button
            key={node.key}
            type="button"
            className={selected === node.key ? "flow-node selected" : "flow-node"}
            style={{ left: node.x, top: node.y }}
            onClick={() => choose(node.key)}
            onPointerDown={(event) => event.currentTarget.setPointerCapture(event.pointerId)}
            onPointerMove={(event) => {
              if (event.currentTarget.hasPointerCapture(event.pointerId)) move(node.key, event);
            }}
          >
            {ROLE_LABEL[node.role]}
          </button>
        ))}
      </div>
      <div className="card form-card">
        <label className="field">
          <span>워크플로 이름</span>
          <input value={name} onChange={(event) => setName(event.target.value)} required />
        </label>
        <label className="field">
          <span>실행할 업무</span>
          <textarea value={taskInput} onChange={(event) => setTaskInput(event.target.value)} required />
        </label>
        <button className="btn btn-dark" type="submit" disabled={pending}>
          {pending ? "실행 중" : "저장 후 실행"}
        </button>
        {activeId && <p className="meta">선택한 워크플로 {activeId}</p>}
      </div>
      {error && (
        <p className="banner error" role="alert">
          {error}
        </p>
      )}
      {status && <p className="meta">마지막 실행 상태 {status}</p>}
      {saved && saved.length > 0 && (
        <article className="card">
          <h2>저장된 워크플로</h2>
          <ul className="stack">
            {saved.map((row) => (
              <li key={row.id}>
                <button className="btn" type="button" onClick={() => void openSaved(row.id)}>
                  {row.name}
                </button>
              </li>
            ))}
          </ul>
        </article>
      )}
    </form>
  );
}
