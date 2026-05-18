variable "aws_region" { default = "ap-south-1" }
variable "project_name" { default = "beauty-store" }
variable "db_password" { sensitive = true }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "security_groups" { type = list(string) }
variable "api_image" { default = "beauty-store-api:latest" }
