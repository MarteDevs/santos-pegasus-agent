output "instance_public_ip" {
  description = "Public IP address of the deployed instance"
  value       = oci_core_instance.agent_instance.public_ip
}

output "app_url" {
  description = "URL to access the Streamlit application"
  value       = "http://${oci_core_instance.agent_instance.public_ip}:${var.app_port}"
}

output "ssh_command" {
  description = "Command to connect to the instance via SSH"
  value       = "ssh -i ${var.ssh_public_key_path} ubuntu@${oci_core_instance.agent_instance.public_ip}"
}
