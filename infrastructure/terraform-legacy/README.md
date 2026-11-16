# Archived Terraform foundation — not the book's canonical configuration

This directory preserves the earlier eight-resource implementation for migration and audit. It is **not** the Chapter 8 configuration and is not part of the reader's normal path.

Use the canonical [Chapter 8 Terraform directory](../terraform/README.md) and the book's resource import and ownership instructions for new reader exercises.

**Do not point this archived configuration and the canonical Chapter 8 configuration at the same Terraform backend key or workspace.** Never destroy an existing state without examining its actual resources, dependencies and shared OIDC ownership.

This archived configuration can still be checked offline:

```bash
terraform -chdir=infrastructure/terraform-legacy init -backend=false -input=false
terraform -chdir=infrastructure/terraform-legacy validate
```
