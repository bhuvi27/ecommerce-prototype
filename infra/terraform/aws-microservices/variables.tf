variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "beauty-ms"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "db_password" {
  type      = string
  sensitive = true
  default   = null
}

variable "jwt_access_secret" {
  type      = string
  sensitive = true
  default   = ""
}

variable "jwt_refresh_secret" {
  type      = string
  sensitive = true
  default   = ""
}

variable "cloudfront_price_class" {
  type    = string
  default = "PriceClass_200"
}

variable "cors_origins" {
  type    = string
  default = "http://localhost:3001"
}
