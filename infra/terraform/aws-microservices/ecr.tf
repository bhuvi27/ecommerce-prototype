resource "aws_ecr_repository" "microservice" {
  for_each = local.microservices

  name                 = "${local.name_prefix}/${each.key}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}
