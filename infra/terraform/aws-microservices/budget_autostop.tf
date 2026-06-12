# Budget alert → SNS → Lambda: scale ECS to 0 + stop RDS when monthly spend hits limit.
# ALB + ElastiCache still incur charges (~$15–20/mo) until terraform destroy.

variable "budget_alert_email" {
  type        = string
  description = "Email for budget alerts"
  default     = "b.chouksey27@gmail.com"
}

variable "budget_monthly_limit_usd" {
  type        = number
  description = "Monthly usage budget (USD) before auto-stop; ~$70 spend ≈ $70 credits left on a $140 pool"
  default     = 70
}

variable "enable_budget_autostop" {
  type        = bool
  description = "Create budget + SNS + Lambda auto-stop"
  default     = true
}

variable "stop_monolith_ec2_name_tag" {
  type        = string
  description = "Substring match on EC2 Name tag for monolith stop (empty = skip)"
  default     = "beauty-store"
}

data "archive_file" "budget_stop_lambda" {
  count       = var.enable_budget_autostop ? 1 : 0
  type        = "zip"
  source_file = "${path.module}/lambda/budget_stop/handler.py"
  output_path = "${path.module}/lambda/budget_stop/handler.zip"
}

resource "aws_sns_topic" "budget_autostop" {
  count = var.enable_budget_autostop ? 1 : 0
  name  = "${local.name_prefix}-budget-autostop"
}

data "aws_iam_policy_document" "budget_sns_publish" {
  count = var.enable_budget_autostop ? 1 : 0

  statement {
    sid    = "AllowBudgetsToPublish"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["budgets.amazonaws.com"]
    }

    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.budget_autostop[0].arn]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "budget_autostop" {
  count  = var.enable_budget_autostop ? 1 : 0
  arn    = aws_sns_topic.budget_autostop[0].arn
  policy = data.aws_iam_policy_document.budget_sns_publish[0].json
}

resource "aws_iam_role" "budget_stop_lambda" {
  count = var.enable_budget_autostop ? 1 : 0
  name  = "${local.name_prefix}-budget-stop-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "budget_stop_lambda" {
  count = var.enable_budget_autostop ? 1 : 0
  name  = "${local.name_prefix}-budget-stop"
  role  = aws_iam_role.budget_stop_lambda[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:ListServices",
          "ecs:UpdateService",
          "ecs:DescribeServices",
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["rds:StopDBInstance", "rds:DescribeDBInstances"]
        Resource = aws_db_instance.postgres.arn
      },
      {
        Effect   = "Allow"
        Action   = ["ec2:StopInstances", "ec2:DescribeInstances"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
    ]
  })
}

resource "aws_lambda_function" "budget_stop" {
  count         = var.enable_budget_autostop ? 1 : 0
  function_name = "${local.name_prefix}-budget-stop"
  role          = aws_iam_role.budget_stop_lambda[0].arn
  handler       = "handler.handler"
  runtime       = "python3.12"
  timeout       = 120
  filename      = data.archive_file.budget_stop_lambda[0].output_path
  source_code_hash = data.archive_file.budget_stop_lambda[0].output_base64sha256

  environment {
    variables = {
      ECS_CLUSTER    = aws_ecs_cluster.main.name
      RDS_INSTANCE_ID = aws_db_instance.postgres.identifier
      STOP_EC2_TAG   = var.stop_monolith_ec2_name_tag
    }
  }
}

resource "aws_lambda_permission" "budget_sns" {
  count         = var.enable_budget_autostop ? 1 : 0
  statement_id  = "AllowBudgetSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.budget_stop[0].function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.budget_autostop[0].arn
}

resource "aws_sns_topic_subscription" "budget_stop_lambda" {
  count     = var.enable_budget_autostop ? 1 : 0
  topic_arn = aws_sns_topic.budget_autostop[0].arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.budget_stop[0].arn
}

resource "aws_cloudwatch_log_group" "budget_stop_lambda" {
  count             = var.enable_budget_autostop ? 1 : 0
  name              = "/aws/lambda/${aws_lambda_function.budget_stop[0].function_name}"
  retention_in_days = 14
}

resource "aws_budgets_budget" "credit_guard" {
  count        = var.enable_budget_autostop ? 1 : 0
  name         = "Credit-Guard-70-Remaining"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_monthly_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_types {
    include_credit             = false
    include_discount           = true
    include_other_subscription = true
    include_recurring          = true
    include_refund             = false
    include_subscription       = true
    include_support            = true
    include_tax                = true
    include_upfront            = true
    use_amortized              = false
    use_blended                = false
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold           = 90
    threshold_type      = "PERCENTAGE"
    notification_type   = "ACTUAL"

    subscriber_email_addresses = [var.budget_alert_email]
    subscriber_sns_topic_arns  = [aws_sns_topic.budget_autostop[0].arn]
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold           = 100
    threshold_type      = "PERCENTAGE"
    notification_type   = "ACTUAL"

    subscriber_email_addresses = [var.budget_alert_email]
    subscriber_sns_topic_arns  = [aws_sns_topic.budget_autostop[0].arn]
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold           = 100
    threshold_type      = "PERCENTAGE"
    notification_type   = "FORECASTED"

    subscriber_email_addresses = [var.budget_alert_email]
  }

}

output "budget_monthly_limit_usd" {
  value       = var.budget_monthly_limit_usd
  description = "Monthly spend limit that triggers auto-stop"
}

output "budget_autostop_sns_arn" {
  value       = var.enable_budget_autostop ? aws_sns_topic.budget_autostop[0].arn : null
  description = "SNS topic that receives budget alerts and triggers auto-stop Lambda"
}

output "budget_autostop_lambda_name" {
  value       = var.enable_budget_autostop ? aws_lambda_function.budget_stop[0].function_name : null
  description = "Lambda that scales ECS to 0 and stops RDS"
}
