terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "rds" {
  source          = "./modules/rds"
  project_name    = var.project_name
  db_password     = var.db_password
  vpc_id          = var.vpc_id
  subnet_ids      = var.subnet_ids
}

module "s3" {
  source       = "./modules/s3"
  project_name = var.project_name
}

module "sqs" {
  source       = "./modules/sqs"
  project_name = var.project_name
}

module "ecs" {
  source          = "./modules/ecs"
  project_name    = var.project_name
  image           = var.api_image
  subnet_ids      = var.subnet_ids
  security_groups = var.security_groups
}

output "rds_endpoint" { value = module.rds.endpoint }
output "s3_bucket" { value = module.s3.bucket_name }
output "sqs_queue_url" { value = module.sqs.queue_url }
output "ecs_cluster" { value = module.ecs.cluster_name }
