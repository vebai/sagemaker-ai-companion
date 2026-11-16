variable "aws_region" {
  description = "AWS Region for the workload."
  type        = string
  default     = "eu-west-2"
}
variable "project_name" {
  description = "Canonical project name."
  type        = string
  default     = "sagemaker-churn"
}
variable "environment" {
  description = "Environment represented by this Terraform state."
  type        = string
  default     = "dev"
  validation {
    condition = contains(
      ["dev", "staging", "prod"],
      var.environment
    )
    error_message = "environment must be dev, staging or prod."
  }
}
variable "github_oidc_subject" {
  description = "Exact GitHub OIDC subject authorised to assume the delivery role."
  type        = string
}
