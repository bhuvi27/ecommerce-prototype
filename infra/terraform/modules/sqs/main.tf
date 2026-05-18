resource "aws_sqs_queue" "events" {
  name                      = "${var.project_name}-events"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 1209600
}

resource "aws_sqs_queue" "dlq" {
  name = "${var.project_name}-events-dlq"
}

output "queue_url" { value = aws_sqs_queue.events.url }
