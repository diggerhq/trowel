variable "hosted_zone_name" {}
variable "aws_region" {}
variable "aws_account_id" {}
variable "tags" {}

{% for block in blocks %}
{% if block.subdomain_name is defined %}
variable "{{ block.name }}_subdomain_name" {}
{% endif %}
{% endfor %}

{% if shared_alb is defined and shared_alb %}
variable "shared_alb_name" {}
variable "shared_alb_port" {}
variable "shared_alb_protocol" {}
variable "shared_alb_ssl_protocol" {}
variable "shared_alb_ssl_port" {}
variable "shared_alb_deregistration_delay" {}
variable "shared_alb_health_check_enabled" {}
variable "shared_alb_health_check" {}
variable "shared_alb_health_check_matcher" {}
variable "shared_alb_health_check_interval" {}
variable "shared_alb_health_check_timeout" {}
variable "shared_alb_access_logs_expiration_days" {}
{% endif %}

{% if enable_bastion is defined and enable_bastion %}
variable "bastion_ssh_key_name" {}
variable "bastion_instance_name" {}
variable "bastion_allowed_hosts" {}
{% endif %}

{% if shared_ecs_cluster is defined and shared_ecs_cluster %}
variable "shared_ecs_cluster_name" {}
{% endif %}