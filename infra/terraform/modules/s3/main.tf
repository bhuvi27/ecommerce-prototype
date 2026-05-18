resource "aws_s3_bucket" "products" {
  bucket = "${var.project_name}-products-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "products" {
  bucket                  = aws_s3_bucket.products.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_caller_identity" "current" {}

output "bucket_name" { value = aws_s3_bucket.products.bucket }
