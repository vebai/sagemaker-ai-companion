
resource "aws_s3_bucket" "project" {
  bucket        = local.project_bucket
  force_destroy = false
}

resource "aws_iam_role" "workload" {
  name               = "SageMakerChurnExecutionRole"
  assume_role_policy = file("${path.module}/snapshots/workload-trust.json")
}

resource "aws_iam_role_policy" "workload" {
  name = "SageMakerChurnJobAccess"
  role = aws_iam_role.workload.id
  policy = templatefile("${path.module}/policies/workload-policy.json.tftpl", {
    account_id     = data.aws_caller_identity.current.account_id
    project_bucket = aws_s3_bucket.project.bucket
  })
}


resource "aws_iam_role" "pipeline" {
  name               = "SageMakerChurnPipelineRole"
  assume_role_policy = file("${path.module}/snapshots/pipeline-trust.json")
}

resource "aws_iam_role_policy" "pipeline" {
  name = "SageMakerChurnPipelineAccess"
  role = aws_iam_role.pipeline.id
  policy = templatefile("${path.module}/policies/pipeline-policy.json.tftpl", {
    account_id     = data.aws_caller_identity.current.account_id
    project_bucket = aws_s3_bucket.project.bucket
  })
}

data "aws_caller_identity" "current" {}

locals {
  project_bucket = "sagemaker-churn-${data.aws_caller_identity.current.account_id}-eu-west-2"
}
