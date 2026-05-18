resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet"
  subnet_ids = var.subnet_ids
}

resource "aws_db_instance" "postgres" {
  identifier           = "${var.project_name}-postgres"
  engine               = "postgres"
  engine_version       = "16"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  db_name              = "beauty_store"
  username             = "beauty"
  password             = var.db_password
  db_subnet_group_name = aws_db_subnet_group.main.name
  skip_final_snapshot  = true
  publicly_accessible  = false
}

output "endpoint" { value = aws_db_instance.postgres.endpoint }
