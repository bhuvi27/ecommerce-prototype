resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  container_definitions = jsonencode([{
    name  = "api"
    image = var.image
    portMappings = [{ containerPort = 3000, protocol = "tcp" }]
  }])
}

output "cluster_name" { value = aws_ecs_cluster.main.name }
