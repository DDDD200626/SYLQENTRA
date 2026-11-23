# SYLQENTRA 아키텍처

기업 업무를 여러 에이전트가 나누어 처리하는 멀티테넌트 플랫폼이다. 아래는 저장소에 있는 구현과 그 경계를 적는다.

| 결과물 | 구현 | 코드 |
| --- | --- | --- |
| 웹 플랫폼 | 로그인, 현황, 문서, 에이전트, 실행, 시각적 워크플로, 요금제 | `frontend/src` |
| AI Engine | OpenAI, Claude, Gemini를 같은 응답 형식으로 호출 | `backend/app/ai_models` |
| Multi-Agent | 매니저, 조사, 데이터, 개발, 문서, 검토, 자동화 | `backend/app/agents` |
| Orchestration | 요청을 계획하고 역할별로 실행한 뒤 검토 | `backend/app/orchestration` |
| Workflow | 노드와 화살표를 저장하고 순서대로 실행 | `frontend/src/WorkflowBoard.tsx`, `backend/app/services/workflow_service.py` |
| MCP | 허용된 도구만 호출하는 클라이언트 | `backend/app/integrations` |
| RAG | txt, md, csv를 나누고 조직 안에서 검색 | `backend/app/rag` |
| Database | PostgreSQL 스키마. 테스트는 SQLite | `backend/app/models`, `docs/database/erd.md` |
| API | `/api/v1` | `docs/api/overview.md`, 실행 중 `GET /docs` |
| AWS | 서울 리전 Terraform. 이 환경에서는 계정 자격이 없어 적용하지 않음 | `infrastructure/terraform` |
| GitHub | 소스와 커밋 이력 | https://github.com/DDDD200626/SYLQENTRA |
| 공개 소개 페이지 | 요금과 제품 설명. API는 포함하지 않음 | https://dddd200626.github.io/SYLQENTRA/ |

## 요청이 지나가는 경로

1. 사용자가 실행 화면에 업무를 적는다.
2. 매니저 에이전트가 필요한 역할을 고른다.
3. 조사, 데이터, 개발, 문서 에이전트 중 계획에 있는 역할이 순서대로 실행된다.
4. 검토 에이전트가 결과를 확인한다.
5. 업무, 실행 기록, 토큰 사용량이 조직 ID와 함께 저장된다.

이메일과 Slack 도구는 승인 행이 생기고, 승인 전에는 외부로 보내지 않는다.

## 모델

`ModelManager`는 `openai`, `anthropic`, `google` 중 요청에 적힌 공급자만 만든다. 키는 `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`다. 테스트는 이 클래스를 대역으로 바꿔 네트워크를 호출하지 않는다.

## 데이터

조직마다 에이전트, 업무, 문서 조각, 워크플로, 사용량이 분리된다. 다른 조직의 업무 번호는 404다. 요금제는 `organizations.plan`이고, 월 한도는 `usage_limits`다. 화면에 적힌 원화는 안내 가격이며 결제 대행은 연결되어 있지 않다.

## 배포 경계

로컬 콘솔은 API와 함께 동작한다. GitHub Pages는 정적 소개 페이지만 제공한다. Terraform은 VPC, RDS, ECS, 로드밸런서를 서술하지만 `terraform apply`는 실행하지 않았다.
