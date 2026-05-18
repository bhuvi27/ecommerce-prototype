variable "project_name" { type = string }
variable "db_password" { type = string, sensitive = true }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }
