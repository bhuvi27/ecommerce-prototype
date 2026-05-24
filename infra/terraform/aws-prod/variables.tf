variable "aws_region" {
  description = "AWS region (Mumbai for India latency)"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix for S3 and CloudFront resources"
  type        = string
  default     = "beauty-store-prod"
}

variable "ec2_origin_ip" {
  description = "Elastic IP of the EC2 instance running the FastAPI stack"
  type        = string
}

variable "ec2_api_port" {
  description = "Port the API listens on (docker-compose.prod.yml default)"
  type        = number
  default     = 3000
}

variable "cloudfront_price_class" {
  description = "CloudFront price class (PriceClass_100 = US/EU only, cheapest)"
  type        = string
  default     = "PriceClass_100"
}
