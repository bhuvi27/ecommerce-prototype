output "cloudfront_domain" {
  description = "CloudFront distribution domain (use as public shop URL)"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "cloudfront_url" {
  description = "HTTPS shop URL"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "Use for cache invalidation after UI deploy"
  value       = aws_cloudfront_distribution.main.id
}

output "s3_bucket_name" {
  description = "S3 bucket for static UI uploads"
  value       = aws_s3_bucket.ui.id
}

output "next_public_api_url" {
  description = "Set as NEXT_PUBLIC_API_URL when building the web app for AWS"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}/api/v1"
}

output "cors_origin" {
  description = "Add to CORS_ORIGINS on EC2 apps/api/.env.aws"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}
