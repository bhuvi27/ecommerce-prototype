output "cloudfront_url" {
  description = "HTTPS URL for UI and API via CloudFront"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "alb_dns_name" {
  description = "ALB DNS (HTTP origin behind CloudFront)"
  value       = aws_lb.api.dns_name
}

output "rds_endpoint" {
  description = "PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.port}"
}

output "msk_bootstrap_brokers" {
  description = "MSK bootstrap brokers (TLS)"
  value       = aws_msk_cluster.kafka.bootstrap_brokers
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "cognito_app_client_id" {
  value = aws_cognito_user_pool_client.web.id
}

output "database_url_template" {
  description = "DATABASE_URL with __PASSWORD__ placeholder"
  value       = local.database_url_template
  sensitive   = true
}

output "ecr_repository_urls" {
  value = { for k, r in aws_ecr_repository.microservice : k => r.repository_url }
}

output "ui_bucket_name" {
  value = aws_s3_bucket.ui.id
}

output "products_bucket_name" {
  value = aws_s3_bucket.products.id
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.main.id
}

output "next_public_api_url" {
  description = "Set as NEXT_PUBLIC_API_URL for web build"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}/api/v1"
}

output "cors_origin" {
  value = "https://${aws_cloudfront_distribution.main.domain_name}"
}
