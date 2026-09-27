output "ecs_cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "Name of the ECS Fargate cluster"
}

output "ecs_task_definition_arn" {
  value       = aws_ecs_task_definition.api.arn
  description = "ARN of the API task definition"
}

output "s3_snapshot_bucket" {
  value       = aws_s3_bucket.snapshots.id
  description = "S3 bucket for world snapshots and event archives"
}
