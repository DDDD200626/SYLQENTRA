# Infrastructure

Local dependencies are defined in the repository root `docker-compose.yml`:

- PostgreSQL 16 with pgvector
- Redis 7
- FastAPI container

Terraform, ECS, and the rest of the AWS layout belong to Phase 15. Until then, develop against Docker locally and keep `AUTO_CREATE_TABLES=true` only for development.
