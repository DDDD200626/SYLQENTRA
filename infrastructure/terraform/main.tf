data "aws_caller_identity" "current" {}

data "aws_rds_engine_version" "postgres" {
  engine  = "postgres"
  version = "16"
  latest  = true
}

resource "random_password" "db" {
  length  = 24
  special = false
}

resource "random_password" "jwt" {
  length  = 48
  special = false
}

resource "random_password" "admin" {
  length  = 20
  special = false
}

resource "aws_vpc" "main" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = { Name = "${var.project}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project}-igw" }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.20.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project}-public-a" }
}

resource "aws_subnet" "public_c" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.20.2.0/24"
  availability_zone       = "${var.aws_region}c"
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project}-public-c" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "${var.project}-public" }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_c" {
  subnet_id      = aws_subnet.public_c.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "alb" {
  name   = "${var.project}-alb"
  vpc_id = aws_vpc.main.id

  ingress {
    description = "HTTP from the internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "api" {
  name   = "${var.project}-api"
  vpc_id = aws_vpc.main.id

  ingress {
    description     = "API from the load balancer"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db" {
  name   = "${var.project}-db"
  vpc_id = aws_vpc.main.id

  ingress {
    description     = "Postgres from the API tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_c.id]
}

resource "aws_db_instance" "postgres" {
  identifier              = "${var.project}-postgres"
  engine                  = "postgres"
  engine_version          = data.aws_rds_engine_version.postgres.version
  instance_class          = "db.t4g.micro"
  allocated_storage       = 20
  db_name                 = "sylqentra"
  username                = "sylqentra"
  password                = random_password.db.result
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  publicly_accessible     = false
  storage_encrypted       = true
  backup_retention_period = 1
  skip_final_snapshot     = true
}

resource "aws_s3_bucket" "app" {
  bucket        = "${var.project}-app-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "app" {
  bucket                  = aws_s3_bucket.app.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "archive_file" "backend" {
  type        = "zip"
  source_dir  = "${path.module}/../../backend"
  output_path = "${path.module}/build/backend.zip"
  excludes = [
    "tests",
    "tests/**",
    "__pycache__",
    "**/__pycache__/**",
    ".pytest_cache",
    "**/.pytest_cache/**",
  ]
}

resource "aws_s3_object" "backend" {
  bucket = aws_s3_bucket.app.id
  key    = "backend.zip"
  source = data.archive_file.backend.output_path
  etag   = data.archive_file.backend.output_md5
}

resource "aws_secretsmanager_secret" "app" {
  name = "${var.project}/app"
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    DATABASE_URL             = "postgresql+psycopg://${aws_db_instance.postgres.username}:${random_password.db.result}@${aws_db_instance.postgres.address}:5432/${aws_db_instance.postgres.db_name}"
    JWT_SECRET               = random_password.jwt.result
    BOOTSTRAP_ADMIN_PASSWORD = random_password.admin.result
  })
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project}-api"
  retention_in_days = 7
}

resource "aws_iam_role" "execution" {
  name               = "${var.project}-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets" {
  role = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.app.arn]
    }]
  })
}

resource "aws_iam_role" "task" {
  name               = "${var.project}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy" "task_bundle" {
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = ["${aws_s3_bucket.app.arn}/backend.zip"]
    }]
  })
}

resource "aws_ecs_cluster" "main" {
  name = "${var.project}-cluster"
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn
  container_definitions = jsonencode([
    {
      name         = "api"
      image        = "public.ecr.aws/docker/library/python:3.12-slim"
      essential    = true
      portMappings = [{ containerPort = 8000, protocol = "tcp" }]
      entryPoint   = ["sh", "-c"]
      command = [join("\n", [
        "set -eu",
        "pip install --no-cache-dir awscli",
        "aws s3 cp s3://${aws_s3_bucket.app.id}/backend.zip /tmp/backend.zip",
        "python -m zipfile -e /tmp/backend.zip /app",
        "pip install --no-cache-dir -r /app/requirements.txt",
        "cd /app",
        "export PYTHONPATH=/app",
        "exec uvicorn app.main:app --host 0.0.0.0 --port 8000",
      ])]
      environment = [
        { name = "ENVIRONMENT", value = "production" },
        { name = "AUTO_CREATE_TABLES", value = "true" },
        { name = "REDIS_URL", value = "disabled" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region },
        { name = "BOOTSTRAP_ADMIN_EMAIL", value = "admin@sylqentra.local" },
        { name = "CORS_ORIGINS", value = "http://${aws_lb.api.dns_name}" },
        { name = "APP_BUNDLE_ETAG", value = data.archive_file.backend.output_md5 },
      ]
      secrets = [
        { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.app.arn}:DATABASE_URL::" },
        { name = "JWT_SECRET", valueFrom = "${aws_secretsmanager_secret.app.arn}:JWT_SECRET::" },
        { name = "BOOTSTRAP_ADMIN_PASSWORD", valueFrom = "${aws_secretsmanager_secret.app.arn}:BOOTSTRAP_ADMIN_PASSWORD::" },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "api"
        }
      }
    }
  ])
}

resource "aws_lb" "api" {
  name               = "${var.project}-alb"
  load_balancer_type = "application"
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_c.id]
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_lb_target_group" "api" {
  name        = "${var.project}-api"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    path                = "/api/v1/health"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 5
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_ecs_service" "api" {
  name                               = "${var.project}-api"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.api.arn
  desired_count                      = 1
  launch_type                        = "FARGATE"
  health_check_grace_period_seconds  = 420
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_c.id]
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http, aws_s3_object.backend, aws_secretsmanager_secret_version.app]
}
