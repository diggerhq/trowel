provider "aws" {
  region = "{{ aws_region }}"
}

{% for block in blocks %}
  {% if block.type == "vpc" %}
    module "{{ block.name}}" {
      source = "./{{ block.name }}"
      network_name = "{{block.name}}"
      region = "{{ aws_region }}"
      {{ "enable_nat_gateway=" + block.enable_nat_gateway | lower if block.enable_nat_gateway is defined else '' }}
      {{ "one_nat_gateway_per_az=" + block.one_nat_gateway_per_az | lower if block.one_nat_gateway_per_az is defined else '' }}
      tags = {
        digger_identifier = "{{block.name}}"
      }
    }
  {% elif block.type == "container" %}
    module "{{ block.name }}" {
      source = "./{{ block.name }}"
      vpc_id = module.{{ network_module_name }}.vpc_id
      ecs_cluster_name = "{{block.aws_app_identifier}}"
      ecs_service_name = "{{block.aws_app_identifier}}"
      alb_subnet_ids = {{block.alb_subnet_ids}}
      ecs_subnet_ids = {{block.ecs_subnet_ids}}

      {% if block.enable_https_listener is defined and block.enable_https_listener and block.subdomain_name is defined %}
        lb_ssl_certificate_arn=aws_acm_certificate.{{ block.name }}_acm_certificate.arn
      {% endif %}

      {{ "container_port=" + block.container_port | lower if block.container_port is defined else '' }}
      {{ "task_cpu=" + block.task_cpu | lower if block.task_cpu is defined else '' }}
      {{ "task_memory=" + block.task_memory | lower if block.task_memory is defined else '' }}
      {{ "internal=" + block.internal | lower if block.internal is defined else '' }}
      {{ 'environment_variables=' + block.environment_variables if block.environment_variables is defined  else '' }}
      {{ 'secrets=local.' + block.name | underscorify + '_secrets' if block.secrets is defined  else '' }}

      {{ "datadog_key_ssm_arn=aws_ssm_parameter.datadog_key.arn" if block.datadog_enabled is defined else '' }}

      region = "{{ aws_region }}"
      tags = {
        digger_identifier = "{{block.aws_app_identifier}}"
      }
    }
  {% elif block.type == "resource" and block.resource_type == "database" %}
    module "{{ block.name }}" {
      source = "./{{ block.name }}"
      vpc_id = module.{{ network_module_name }}.vpc_id
      identifier = "{{block.aws_app_identifier}}"
      aws_app_identifier = "{{block.aws_app_identifier}}"
      subnets = {{block.subnets}}

      {{ 'allocated_storage="' + block.allocated_storage + '"' if block.allocated_storage is defined else '' }}
      {{ 'storage_type="' + block.storage_type + '"' if block.storage_type is defined  else '' }}
      {{ 'engine="' + block.engine + '"' if block.engine is defined  else '' }}
      {{ 'ingress_port="' + block.ingress_port + '"' if block.ingress_port is defined  else '' }}
      {{ 'connection_schema="' + block.connection_schema + '"' if block.connection_schema is defined  else '' }}
      {{ 'engine_version="' + block.engine_version + '"' if block.engine_version is defined  else '' }}
      {{ 'instance_class="' + block.instance_class + '"' if block.instance_class is defined  else '' }}
      {{ 'database_name="' + block.database_name + '"' if block.database_name is defined  else '' }}
      {{ 'database_username="' + block.database_username + '"' if block.database_username is defined  else '' }}
      {{ 'publicly_accessible="' + block.publicly_accessible + '"' if block.publicly_accessible is defined  else '' }}
      {{ 'snapshot_identifier="' + block.snapshot_identifier + '"' if block.snapshot_identifier is defined  else '' }}
      {{ 'security_groups=' + block.security_groups if block.security_groups is defined  else '' }}

      tags = {
        digger_identifier = "{{block.aws_app_identifier}}"
      }
    }
  {% elif block.type == "resource" and block.resource_type == "redis" %}
    module "{{ block.name }}" {
      source = "./{{ block.name }}"
      vpc_id = module.{{ network_module_name }}.vpc_id
      cluster_id = "{{block.aws_app_identifier}}"
      private_subnets = {{block.private_subnets_ids}}
      cluster_description = "{{block.aws_app_identifier}}"

      {{ 'engine_version="' + block.redis_engine_version + '"' if block.redis_engine_version is defined  else '' }}
      {{ 'redis_node_type="' + block.redis_instance_class + '"' if block.redis_instance_class is defined  else '' }}
      {{ 'redis_number_nodes=' + block.redis_number_nodes | string if block.redis_number_nodes is defined  else '' }}
      {{ 'security_groups=' + block.security_groups if block.security_groups is defined  else '' }}
      tags = {
        digger_identifier = "{{block.aws_app_identifier}}"
      }
    }
    {% elif block.type == "resource" and block.resource_type == "docdb" %}
    module "{{ block.name }}" {
      source = "./{{ block.name }}"
      vpc_id = module.{{ network_module_name }}.vpc_id
      cluster_identifier = "{{block.aws_app_identifier}}"
      private_subnets = {{block.private_subnets_ids}}


      {{ 'engine_version="' + block.docdb_engine_version + '"' if block.docdb_engine_version is defined  else '' }}
      {{ 'instance_class="' + block.docdb_instance_class + '"' if block.docdb_instance_class is defined  else '' }}
      {{ 'instances_number=' + block.instances_number | string if block.instances_number is defined  else '' }}
      {{ 'security_groups=' + block.security_groups if block.security_groups is defined  else '' }}
      tags = {
        digger_identifier = "{{block.aws_app_identifier}}"
      }
    }
  {% elif block.type == "s3" %}
    module "{{ block.name }}" {
      source = "./{{ block.name }}"
    }
  {% elif block.type == "sqs" %}
    module "{{ block.name }}" {
      source = "./{{ block.name }}"
    }
  {% elif block.type == "api-gateway" %}
    module "{{ block.name }}" {
      source = "./{{ block.name }}"
      subnets = {{ block.subnets }}
      vpc_id = module.{{ network_module_name }}.vpc_id
    }
  {% endif %}
{% endfor %}



