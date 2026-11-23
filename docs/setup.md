# Install tools on your workstation

**macOS (Homebrew).** If Homebrew is not installed, first follow https://brew.sh/ . In Terminal:

```bash
brew update
brew install git awscli python@3.11
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
git --version
aws --version
python3.11 --version
terraform version
```

**Ubuntu/Debian.** Install Git, basic prerequisites and AWS CLI v2; select the AWS CLI archive for your machine architecture (example below is x86_64; for ARM64 use `awscli-exe-linux-aarch64.zip`). See https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html .

```bash
sudo apt-get update
sudo apt-get install -y git curl unzip gnupg ca-certificates wget
curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscliv2.zip
(cd /tmp && unzip -q awscliv2.zip && sudo ./aws/install)
aws --version
git --version
```

Install **Python 3.11** with its `venv` support from your distribution's appropriate supported packages or Python's official installation instructions (https://www.python.org/downloads/). On systems where `python3.11` is provided by APT:

```bash
sudo apt-get install -y python3.11 python3.11-venv
python3.11 --version
```

Install Terraform from HashiCorp's signed APT repository (https://developer.hashicorp.com/terraform/install):

```bash
wget -qO- https://apt.releases.hashicorp.com/gpg | \
  gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(. /etc/os-release && echo "$VERSION_CODENAME") main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update
sudo apt-get install -y terraform
terraform version
```

For Fedora/RHEL, use the official HashiCorp and AWS CLI installation guides for `dnf`; verify Python 3.11 and `python3.11 -m venv` before continuing. **AWS CloudShell** already provides an authenticated AWS CLI in many accounts, but its Python/Terraform versions, storage persistence and installed packages must be checked; local Mac/Linux execution is the documented default.

[Continue with cloning and configuration](../README.md#3-clone-configure-python-and-verify-identity).
