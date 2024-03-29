
hosted_zone_name = "{{ hosted_zone_name }}"
aws_region = "{{ aws_region }}"
aws_account_id = "{{ aws_account_id }}"

tags = {{ tags }}

{% for block in blocks %}
  {% if block.subdomain_name is defined %}
    {{ block.name }}_subdomain_name = "{{ block.subdomain_name}}"
  {% endif %}
{% endfor %}

{% if shared_alb is defined and shared_alb %}
  shared_alb_name =                       "{{ shared_alb_name }}"
  shared_alb_port                         = "80"
  shared_alb_protocol                     = "HTTP"
  shared_alb_ssl_protocol                 = "HTTPS"
  shared_alb_ssl_port                     = "443"
  shared_alb_deregistration_delay         = "30"
  shared_alb_health_check_enabled         = true
  shared_alb_health_check                 = "/"
  shared_alb_health_check_matcher         = "200-499"
  shared_alb_health_check_interval        = "30"
  shared_alb_health_check_timeout         = "30"
  shared_alb_access_logs_expiration_days  = "7"
{% endif %}

{% if enable_bastion is defined and enable_bastion %}
  bastion_ssh_key_name = "{{ bastion_ssh_key_name }}"
  bastion_instance_name = "{{ bastion_instance_name }}"
  bastion_allowed_hosts = {{ bastion_allowed_hosts }}
{% endif %}

{% if shared_ecs_cluster is defined and shared_ecs_cluster %}
  shared_ecs_cluster_name = "{{ shared_ecs_cluster_name }}"
{% endif %}