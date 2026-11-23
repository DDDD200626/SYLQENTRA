# API v1

Base path: `/api/v1`

| Method | Path | Auth | Permission |
| --- | --- | --- | --- |
| GET | `/health` | Public | - |
| POST | `/auth/register` | Public | Creates an organization admin |
| POST | `/auth/login` | Public | - |
| POST | `/auth/refresh` | Refresh token | Rotates the refresh token |
| POST | `/auth/logout` | Refresh token | Revokes that refresh token |
| GET | `/auth/me` | Access token | - |
| PATCH | `/auth/me` | Access token | - |
| POST | `/auth/change-password` | Access token | Revokes all refresh tokens |
| GET | `/organizations` | Access token | Own organizations, or all for a platform admin |
| POST | `/organizations` | Access token | Platform admin |
| GET | `/organizations/current` | Access token | Membership or platform admin header |
| PATCH | `/organizations/current` | Access token | `organizations:manage` |
| GET | `/organizations/members` | Access token | `users:read` |
| POST | `/organizations/members` | Access token | `users:manage` |
| PATCH | `/organizations/members/{user_id}` | Access token | `users:manage` |
| GET | `/dashboard` | Access token | `dashboard:read` |
| POST | `/tasks` | Access token | `tasks:write` |
| GET | `/tasks` | Access token | `tasks:read` |
| GET | `/tasks/{id}` | Access token | `tasks:read` |
| GET | `/agents` | Access token | `agents:read` |

| POST | `/agents/{role}/run` | Access token | `tasks:write` |
| POST | `/ai/generate` | Access token | `agents:write` |
| GET | `/ai/usage` | Access token | `dashboard:read` |
| PUT | `/ai/usage-limit` | Access token | `organizations:manage` |
| GET | `/plans` | Public | - |
| PUT | `/organizations/current/plan` | Access token | `organizations:manage` |
| POST | `/orchestrations` | Access token | `tasks:write` |
| GET | `/workflows` | Access token | `tasks:read` |
| POST | `/workflows` | Access token | `tasks:write` |
| GET | `/workflows/{id}` | Access token | `tasks:read` |
| POST | `/workflows/{id}/execute` | Access token | `tasks:write` |
| GET | `/approvals` | Access token | `approvals:read` |
| POST | `/approvals/{id}/decide` | Access token | `approvals:manage` |
| POST | `/integrations/github/issues` | Access token | `tasks:write`, header `X-Integration-Token` |
| POST | `/integrations/slack/messages` | Access token | `tasks:write`, header `X-Integration-Token` |
| GET | `/knowledge/documents` | Access token | `tasks:read` |
| POST | `/knowledge/documents` | Access token | `tasks:write` |
| POST | `/knowledge/ask` | Access token | `tasks:write` |
| GET | `/metrics` | Access token | `dashboard:read` |

Interactive schema: `GET /docs` on a running API.

A user who belongs to more than one organization, and a platform admin who is opening an organization they have not joined, send `X-Organization-Id`.

Errors use this body:

```json
{"error": {"code": "FORBIDDEN", "message": "Insufficient permissions"}}
```

Task reads in another organization return `404`, so the response does not reveal that the task exists.
