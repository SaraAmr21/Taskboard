variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "taskboard"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "ssh_public_key_path" {
  type    = string
  default = "~/.ssh/taskboard.pub"
}

variable "admin_cidr" {
  type = string

  validation {
    condition     = var.admin_cidr != "0.0.0.0/0"
    error_message = "Refusing to open SSH to the whole internet."
  }
}
