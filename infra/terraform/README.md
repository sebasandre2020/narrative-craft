# Terraform Infrastructure Blueprint: Narrative-Craft

This directory contains the Infrastructure as Code (IaC) configuration for deploying Narrative-Craft to AWS ECS Fargate, Amazon RDS PostgreSQL, Amazon ElastiCache Redis, and Amazon S3.

## Topology Summary
- **Compute**: AWS ECS Fargate container running FastAPI with LangGraph in private application subnets.
- **Storage**:
  - Amazon S3 bucket with versioning and server-side encryption for world snapshots.
  - Amazon RDS PostgreSQL 16 Multi-AZ for the immutable event store and relational property graph.
  - Amazon ElastiCache Redis 7 for sub-millisecond active session graph caching.
- **Security & IAM**: Least-privilege ECS execution and task roles, KMS encryption, and AWS Secrets Manager integration.

## Usage
```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan -var="environment=staging" -var="image_tag=v0.1.0"

# Apply
terraform apply -var="environment=staging" -var="image_tag=v0.1.0"
```
