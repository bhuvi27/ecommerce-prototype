resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

locals {
  ecs_log_services = merge(
    { for s in local.microservices : s => s },
    { mongo = "mongo" }
  )

  ecs_alb_service_keys = keys(local.alb_services)
  ecs_internal_only    = toset(["notification"])
}

resource "aws_cloudwatch_log_group" "ecs" {
  for_each = local.ecs_log_services

  name              = "/ecs/${local.name_prefix}/${each.key}"
  retention_in_days = 7
}

locals {
  ecs_common_env = [
    { name = "AWS_REGION", value = var.aws_region },
    { name = "REDIS_HOST", value = aws_elasticache_cluster.redis.cache_nodes[0].address },
    { name = "REDIS_PORT", value = tostring(aws_elasticache_cluster.redis.port) },
    { name = "KAFKA_BOOTSTRAP_SERVERS", value = aws_msk_cluster.kafka.bootstrap_brokers },
    { name = "COGNITO_USER_POOL_ID", value = aws_cognito_user_pool.main.id },
    { name = "COGNITO_CLIENT_ID", value = aws_cognito_user_pool_client.web.id },
    { name = "MONGO_URI", value = "mongodb://mongo.${local.name_prefix}.local:27017/beauty" },
    { name = "PRODUCTS_BUCKET", value = aws_s3_bucket.products.id },
        { name = "CATALOG_SERVICE_URL", value = "http://${aws_lb.api.dns_name}" },
    { name = "CART_SERVICE_URL", value = "http://${aws_lb.api.dns_name}" },
    { name = "PAYMENT_SERVICE_URL", value = "http://${aws_lb.api.dns_name}" },
    { name = "ORDER_SERVICE_URL", value = "http://${aws_lb.api.dns_name}" },
    { name = "DATABASE_URL_TEMPLATE", value = local.database_url_template },
  ]
}

resource "aws_ecs_task_definition" "microservice" {
  for_each = merge(
    { for k in local.ecs_alb_service_keys : k => k },
    { for k in local.ecs_internal_only : k => k }
  )

  family                   = "${local.name_prefix}-${each.key}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = each.key
      image     = "${aws_ecr_repository.microservice[each.key].repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = concat(local.ecs_common_env, [
        { name = "SERVICE_NAME", value = each.key },
        { name = "PORT", value = "8000" },
      ])
      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.db_password.arn}:password::"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs[each.key].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = each.key
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "mongo" {
  family                   = "${local.name_prefix}-mongo"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "mongo"
      image     = "public.ecr.aws/docker/library/mongo:7"
      essential = true
      portMappings = [
        {
          containerPort = 27017
          hostPort      = 27017
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs["mongo"].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "mongo"
        }
      }
    }
  ])
}

resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${local.name_prefix}.local"
  description = "Private DNS for ECS services"
  vpc         = aws_vpc.main.id
}

resource "aws_service_discovery_service" "mongo" {
  name = "mongo"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    dns_records {
      ttl  = 10
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
}

resource "aws_ecs_service" "microservice_alb" {
  for_each = toset(local.ecs_alb_service_keys)

  name            = "${local.name_prefix}-${each.key}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.microservice[each.key].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.service[each.key].arn
    container_name   = each.key
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http]
}

resource "aws_ecs_service" "notification" {
  name            = "${local.name_prefix}-notification"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.microservice["notification"].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }
}

resource "aws_ecs_service" "mongo" {
  name            = "${local.name_prefix}-mongo"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.mongo.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.mongo.id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.mongo.arn
  }
}
