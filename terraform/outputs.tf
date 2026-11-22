output "public_ip" {
  description = "Elastic IP of the server"
  value       = aws_eip.app.public_ip
}

output "ssh_command" {
  description = "Ready-to-paste SSH command"
  value       = "ssh -i ~/.ssh/taskboard ubuntu@${aws_eip.app.public_ip}"
}

output "app_url" {
  description = "Where the app will be reachable"
  value       = "http://${aws_eip.app.public_ip}"
}
