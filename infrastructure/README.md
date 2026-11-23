# Infrastructure

Local dependencies are defined in the repository root `docker-compose.yml`:

- PostgreSQL 16 with pgvector
- Redis 7
- FastAPI container

`infrastructure/terraform` creates the Seoul (`ap-northeast-2`) stack:

- VPC with two public subnets and an internet gateway
- PostgreSQL 16 on RDS (`db.t4g.micro`), reachable only from the API tasks
- S3 object for the backend bundle, Secrets Manager for the database URL and JWT secret
- ECS Fargate service behind a public application load balancer on port 80

The database password and the platform admin password are generated during apply and are not stored in git. Terraform state contains them, so `*.tfstate` stays out of git.

```powershell
terraform -chdir=infrastructure/terraform init
terraform -chdir=infrastructure/terraform apply
```

AWS credentials must already be available to the standard AWS SDK chain (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`, or `%USERPROFILE%\.aws\credentials`).
