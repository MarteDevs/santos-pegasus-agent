provider "oci" {
  tenancy_ocid = var.tenancy_ocid
  region       = var.region
}

# --- Network (VCN) ---
resource "oci_core_vcn" "agent_vcn" {
  compartment_id = var.compartment_ocid
  cidr_block     = "10.0.0.0/16"
  display_name   = "santos_pegasus_vcn"
  dns_label      = "pegasusvcn"
}

resource "oci_core_internet_gateway" "agent_igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.agent_vcn.id
  display_name   = "santos_pegasus_igw"
  enabled        = true
}

resource "oci_core_default_route_table" "agent_route_table" {
  manage_default_resource_id = oci_core_vcn.agent_vcn.default_route_table_id

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.agent_igw.id
  }
}

# --- Security (Firewall Rules) ---
resource "oci_core_default_security_list" "agent_security_list" {
  manage_default_resource_id = oci_core_vcn.agent_vcn.default_security_list_id

  # Allow all outbound traffic
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # Allow inbound SSH (22)
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6" # TCP
    tcp_options {
      min = 22
      max = 22
    }
  }

  # Allow inbound Streamlit (8501)
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6" # TCP
    tcp_options {
      min = var.app_port
      max = var.app_port
    }
  }
}

# --- Subnet ---
resource "oci_core_subnet" "agent_subnet" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.agent_vcn.id
  cidr_block        = "10.0.1.0/24"
  display_name      = "santos_pegasus_subnet"
  dns_label         = "pegasussubnet"
  route_table_id    = oci_core_vcn.agent_vcn.default_route_table_id
  security_list_ids = [oci_core_vcn.agent_vcn.default_security_list_id]
}

# --- Find Ubuntu Image ---
data "oci_core_images" "ubuntu_images" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# --- Compute Instance ---
resource "oci_core_instance" "agent_instance" {
  # We just pick the first AD in the list
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_ocid
  display_name        = "santos-pegasus-agent"
  shape               = var.instance_shape

  source_details {
    source_id   = data.oci_core_images.ubuntu_images.images[0].id
    source_type = "image"
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.agent_subnet.id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data           = base64encode(templatefile("${path.module}/cloud-init.yaml.tpl", {
      google_api_key  = var.google_api_key
      github_repo_url = var.github_repo_url
      app_port        = var.app_port
    }))
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}
