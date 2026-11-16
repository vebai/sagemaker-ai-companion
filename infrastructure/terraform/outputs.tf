output "project_bucket" {
  value = aws_s3_bucket.project.bucket
}
output "workload_role_arn" {
  value = aws_iam_role.workload.arn
}
output "pipeline_role_arn" {
  value = aws_iam_role.pipeline.arn
}
output "github_delivery_role_arn" {
  value = aws_iam_role.github.arn
}
output "github_oidc_provider_arn" {
  value = data.aws_iam_openid_connect_provider.github.arn
}
