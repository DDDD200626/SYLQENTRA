output "api_url" {
  value = "http://${aws_lb.api.dns_name}"
}

output "admin_email" {
  value = "admin@sylqentra.local"
}

output "admin_password" {
  value     = random_password.admin.result
  sensitive = true
}
