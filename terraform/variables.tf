variable "tenancy_ocid" {
  description = "OCID of the OCI Tenancy"
  type        = string
}

variable "compartment_ocid" {
  description = "OCID of the compartment where resources will be created"
  type        = string
}

variable "region" {
  description = "OCI region"
  type        = string
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key for instance access"
  type        = string
}

variable "instance_shape" {
  description = "Compute instance shape"
  type        = string
  default     = "VM.Standard.E2.1.Micro"
}

variable "google_api_key" {
  description = "Google Gemini API Key for the AI Agent"
  type        = string
  sensitive   = true
}

variable "github_repo_url" {
  description = "URL of the GitHub repository containing the agent code"
  type        = string
}

variable "app_port" {
  description = "Port where Streamlit application runs"
  type        = number
  default     = 8501
}
