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

## 배포 전 운영 조건

기업별 데이터는 `organization_id`로 갈라져 있고, 다른 회사의 업무는 404다. 에이전트 실행은 `agent_runs`에 입력, 출력, 상태를 남긴다. 이메일과 Slack은 승인 전에는 나가지 않는다. 모델별 토큰과 예상 비용은 `model_usage`에 쌓이고, 요금제가 월 한도를 정한다. 오케스트레이션은 대기 상태로 저장된 뒤 최대 3번 다시 시도한다. 테스트 환경에서는 같은 요청 안에서 끝내고, 그 외에는 서버 안의 백그라운드 작업으로 실행한다. 이 큐는 아직 SQS가 아니다.

유료 모델 키를 넣지 않으면 외부 AI 호출은 일어나지 않는다.

## 최종 AWS 목표

지금 적용하지 않은 목표 구조다. `terraform apply`는 실행하지 않았고, 비용이 발생하는 AWS 자원은 만들지 않았다.

| 서비스 | 역할 |
| --- | --- |
| Route 53 | 도메인 |
| CloudFront | 웹 배포 |
| S3 | 프론트엔드와 문서 |
| ECS Fargate | FastAPI와 에이전트 |
| RDS PostgreSQL | 사용자, 기업, 업무 |
| ElastiCache Redis | 상태와 캐시 |
| SQS | 긴 AI 작업 대기열 |
| Secrets Manager | API 키와 비밀번호 |
| CloudWatch | 로그 |
| ACM | HTTPS 인증서 |

현재 Terraform은 VPC, RDS, ECS, 로드밸런서, Secrets Manager, CloudWatch 로그만 서술한다. Route 53, CloudFront, ElastiCache, SQS, ACM은 도메인과 운영 트래픽이 생긴 뒤에 붙인다.

## 배포 경계

로컬 콘솔은 API와 함께 동작한다. GitHub Pages는 정적 소개 페이지만 제공한다.
