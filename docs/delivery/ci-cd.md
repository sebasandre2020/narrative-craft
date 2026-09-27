# CI/CD Pipeline Blueprint: Narrative-Craft

## 1. Pipeline Principles
Narrative-Craft enforces a strict, multi-stage **Continuous Integration and Continuous Delivery (CI/CD)** pipeline using GitHub Actions:
- **Fast Feedback**: Linting and schema validation run in parallel under 60 seconds.
- **Contract Parity**: OpenAPI 3.1 specifications and JSON schemas are validated against test fixtures on every pull request.
- **Immutable Container Images**: Container images are tagged with the Git commit SHA, ensuring auditable traceability.
- **Zero-Downtime Deployment**: ECS Fargate executes rolling blue/green updates, verifying `/health/live` before draining older tasks.

## 2. Pipeline Execution Stages

```mermaid
flowchart LR
  PR[GitHub Pull Request] --> Lint[Stage 1: Lint & Format Check (Ruff)]
  PR --> Contract[Stage 2: Schema & Contract Validator]
  PR --> Test[Stage 3: PyTest Unit & Rule Tests]
  
  Lint & Contract & Test --> Merge[Merge to Main]
  
  Merge --> Build[Stage 4: Docker Multi-Stage Build]
  Build --> Scan[Stage 5: Trivy Security Scan]
  Scan --> Push[Stage 6: Push to AWS ECR]
  Push --> Deploy[Stage 7: Terraform Apply & ECS Deploy]
  Deploy --> Smoke[Stage 8: Production Smoke Tests]
```

## 3. Deployment Gates & Quality Thresholds
1. **Linting Gate**: Ruff must exit 0 with zero warnings.
2. **Schema Gate**: `scripts/validate_scaffold.py` must verify all JSON payloads and OpenAPI routes.
3. **Test Gate**: All unit and rule validation tests must pass with 100% assertion success.
4. **Vulnerability Gate**: Trivy must report 0 CRITICAL or HIGH vulnerabilities in the container base image.
5. **Rollout Health Gate**: ECS service must achieve healthy state within 180 seconds or trigger automatic rollback.
