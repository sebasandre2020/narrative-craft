variable "aws_region" {
  type        = string
  description = "AWS region for deployment"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Environment tier (development, staging, production)"
  default     = "staging"
}

variable "container_image" {
  type        = string
  description = "ECR image repository URI for narrative-craft-api"
  default     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/narrative-craft-api"
}

variable "image_tag" {
  type        = string
  description = "Docker image tag or git commit sha"
  default     = "latest"
}
