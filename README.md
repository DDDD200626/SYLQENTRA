# SYLQENTRA

기업의 업무 요청을 나누어 여러 AI Agent가 처리하는 멀티테넌트 자동화 플랫폼이다.

| Phase | 결과 |
| --- | --- |
| 01–04 | 환경, FastAPI, PostgreSQL 스키마, JWT와 RBAC |
| 05–06 | OpenAI, Claude, Gemini 호출과 7개 전문 Agent |
| 07–08 | 업무 오케스트레이션과 Workflow, cron 판단 |
| 09–10 | GitHub, Slack 연동과 문서 검색 |
| 11–12 | React 작업 화면, 승인, 요청 제한 |
| 13–16 | 지표, 시나리오 테스트, AWS 구성과 CI, 요금제 |

조직을 만들면 Manager, Research, Data, Developer, Document, Review, Automation Agent가 생긴다. 모델 API 키는 `.env`에만 둔다. 키가 없으면 테스트용 대역이 응답한다. email과 Slack 도구는 승인 전에는 보내지 않는다. 요금제는 free, starter, team, business, enterprise이며 월 토큰 한도를 바꾼다. Terraform은 적용하지 않은 설계 파일이다.

## 로컬 실행

Python 3.12 가상환경이 저장소 루트의 `.venv`에 있다.

```powershell
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

Docker Desktop이 설치된 경우 PostgreSQL과 Redis를 올린다.

```powershell
docker compose up -d postgres redis
```

`.env`의 `DATABASE_URL`은 `localhost`를 가리킨다. API까지 컨테이너로 실행하려면 `docker compose up --build`를 사용한다. 컨테이너 안에서는 Compose가 DB 호스트를 `postgres`로 바꾼다.

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload
```

서버 주소는 `http://127.0.0.1:8000`이고, 문서는 `http://127.0.0.1:8000/docs`이다. IntelliJ에서는 루트 `main.py`를 실행해도 같은 앱이 시작된다.

운영 환경에서는 `AUTO_CREATE_TABLES=false`로 두고 마이그레이션을 사용한다.

```powershell
.\.venv\Scripts\alembic -c backend\alembic.ini upgrade head
```

## 테스트

Docker가 없어도 테스트는 메모리 SQLite로 실행된다. 애플리케이션이 지원하는 데이터베이스는 PostgreSQL이다.

```powershell
.\.venv\Scripts\python -m pytest
```

## 권한

| 역할 | 범위 |
| --- | --- |
| super_admin | 플랫폼 관리자. `BOOTSTRAP_ADMIN_EMAIL`로 생성하며 조직 헤더로 기업 데이터에 접근 |
| organization_admin | 회원가입 시 생성되는 기업 관리자 |
| manager | 업무, Agent, 구성원 조회 |
| employee | 업무 요청과 조회 |
| viewer | 조회만 가능 |

사용자가 조직에 둘 이상 속해 있으면 `X-Organization-Id` 헤더가 필요하다. 다른 회사의 업무 번호로 조회하면 404를 반환한다.

## 디렉터리

```text
backend/app/api          HTTP 라우터
backend/app/core         설정, 보안, 권한, 예외
backend/app/database     엔진, 시드, Alembic 대상 모델
backend/app/models       테이블
backend/app/repositories 조회와 저장
backend/app/services     인증, 조직, 업무, 대시보드
backend/tests            pytest
frontend                 React 작업 화면
infrastructure           Docker Compose와 Terraform
docs                     ERD와 API 개요
```
