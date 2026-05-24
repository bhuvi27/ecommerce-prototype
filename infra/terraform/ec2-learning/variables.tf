variable "aws_region" {
  description = "AWS region (Mumbai for India latency)"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix for EC2 and security group resources"
  type        = string
  default     = "beauty-store-learning"
}

variable "instance_type" {
  description = "EC2 instance type (t3.micro is Free Tier eligible)"
  type        = string
  default     = "t3.micro"
}

variable "create_ssh_key" {
  description = "Generate SSH key pair via Terraform (recommended)"
  type        = bool
  default     = true
}

variable "ssh_key_name" {
  description = "Existing EC2 key pair name (only if create_ssh_key is false)"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidr" {
  description = "Your public IP in CIDR form, e.g. 203.0.113.10/32"
  type        = string
}

variable "allowed_api_cidr" {
  description = "CIDR allowed to reach API port 3000"
  type        = string
  default     = "0.0.0.0/0"
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 30
}

variable "github_repo_url" {
  description = "Public Git repo to clone on EC2"
  type        = string
  default     = "https://github.com/bhuvi27/shamit-beauty-store.git"
}

variable "github_pages_origin" {
  description = "GitHub Pages origin for CORS (no path suffix)"
  type        = string
  default     = "https://bhuvi27.github.io"
}
