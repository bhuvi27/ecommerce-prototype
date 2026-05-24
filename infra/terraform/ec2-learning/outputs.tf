output "elastic_ip" {
  description = "Public IP — use in NEXT_PUBLIC_API_URL and CORS setup"
  value       = aws_eip.api.public_ip
}

output "api_url" {
  description = "FastAPI base URL after deploy"
  value       = "http://${aws_eip.api.public_ip}:3000/api/v1"
}

output "health_url" {
  description = "Readiness check URL"
  value       = "http://${aws_eip.api.public_ip}:3000/health/ready"
}

output "ssh_command" {
  description = "SSH into the instance"
  value       = var.create_ssh_key ? "ssh -i ${path.module}/${var.project_name}.pem ec2-user@${aws_eip.api.public_ip}" : "ssh -i ~/.ssh/YOUR_KEY.pem ec2-user@${aws_eip.api.public_ip}"
}

output "ssh_key_file" {
  description = "Path to generated private key (when create_ssh_key is true)"
  value       = var.create_ssh_key ? "${path.module}/${var.project_name}.pem" : null
}

output "instance_id" {
  value = aws_instance.api.id
}

output "github_pages_api_url" {
  description = "Use this as api_url when running Deploy GitHub Pages workflow"
  value       = "http://${aws_eip.api.public_ip}:3000/api/v1"
}
