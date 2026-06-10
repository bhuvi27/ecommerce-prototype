resource "aws_lb" "api" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "${local.name_prefix}-alb"
  }
}

locals {
  alb_services = {
    auth = {
      path_pattern = "/api/v1/auth/*"
      priority     = 100
      port         = 8000
      health_path  = "/health"
    }
    catalog = {
      path_pattern = "/api/v1/catalog/*"
      priority     = 110
      port         = 8000
      health_path  = "/health"
    }
    cart = {
      path_pattern = "/api/v1/cart/*"
      priority     = 120
      port         = 8000
      health_path  = "/health"
    }
    order = {
      path_pattern = "/api/v1/orders/*"
      priority     = 130
      port         = 8000
      health_path  = "/health"
    }
    payment = {
      path_pattern = "/api/v1/payments/*"
      priority     = 140
      port         = 8000
      health_path  = "/health"
    }
  }
}

resource "aws_lb_target_group" "service" {
  for_each = local.alb_services

  name        = substr("${local.name_prefix}-${each.key}", 0, 32)
  port        = each.value.port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = each.value.health_path
    matcher             = "200-399"
  }

  tags = {
    Name = "${local.name_prefix}-tg-${each.key}"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }
}

resource "aws_lb_listener_rule" "service" {
  for_each = local.alb_services

  listener_arn = aws_lb_listener.http.arn
  priority     = each.value.priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service[each.key].arn
  }

  condition {
    path_pattern {
      values = [each.value.path_pattern]
    }
  }
}

resource "aws_lb_listener_rule" "catalog_admin" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 115

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service["catalog"].arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/admin/*"]
    }
  }
}

resource "aws_lb_listener_rule" "health_auth" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 155

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service["auth"].arn
  }

  condition {
    path_pattern {
      values = ["/health/*"]
    }
  }
}
