terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, 2)

  microservices = toset([
    "auth",
    "catalog",
    "cart",
    "order",
    "payment",
    "notification",
  ])

  db_name     = "beauty_store"
  db_username = "beauty_admin"

  # Template for app DATABASE_URL (password injected at runtime from Secrets Manager)
  database_url_template = "postgresql://${local.db_username}:__PASSWORD__@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${local.db_name}?sslmode=require"
}
