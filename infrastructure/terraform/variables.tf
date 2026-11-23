variable "aws_region" {
  type    = string
  default = "ap-northeast-2"
}

variable "project" {
  type    = string
  default = "sylqentra"
}

variable "db_password" {
  type      = string
  sensitive = true
}
