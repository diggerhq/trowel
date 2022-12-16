provider "aws" {
  region = "{{ aws_region }}"
}

{% for module in modules %}
  {% if module.type == "vpc" %}
    module "{{ module.module_name}}" {
      source = "./{{ module.module_name }}"
      network_name = "{{module.module_name}}"
      region = "{{ aws_region }}"
      {{ "enable_nat_gateway=" + module.enable_nat_gateway | lower if module.enable_nat_gateway is defined else '' }}
      {{ "one_nat_gateway_per_az=" + module.one_nat_gateway_per_az | lower if module.one_nat_gateway_per_az is defined else '' }}
      tags = {
        digger_identifier = "{{module.module_name}}"
      }
    }
  {% elif module.type == "container" %}
    module "{{ module.module_name }}" {
      source = "./{{ module.module_name }}"
      vpc_id = module.{{ network_module_name }}.vpc_id
      ecs_cluster_name = "{{module.aws_app_identifier}}"
      ecs_service_name = "{{module.aws_app_identifier}}"
      alb_subnet_ids = {{module.alb_subnet_ids}}
      ecs_subnet_ids = {{module.ecs_subnet_ids}}

      {% if module.enable_https_listener is defined and module.enable_https_listener and module.subdomain_name is defined %}
        lb_ssl_certificate_arn=aws_acm_certificate.{{ module.module_name }}_acm_certificate.arn
      {% endif %}

      {{ "container_port=" + module.container_port | lower if module.container_port is defined else '' }}
      {{ "task_cpu=" + module.task_cpu | lower if module.task_cpu is defined else '' }}
      {{ "task_memory=" + module.task_memory | lower if module.task_memory is defined else '' }}
      {{ "internal=" + module.internal | lower if module.internal is defined else '' }}
      {{ 'environment_variables=' + module.environment_variables if module.environment_variables is defined  else '' }}
      {{ 'secrets=local.secrets' if module.secrets is defined  else '' }}

      {{ "datadog_key_ssm_arn=aws_ssm_parameter.datadog_key.arn" if module.datadog_enabled is defined else '' }}

      region = "{{ aws_region }}"
      tags = {
        digger_identifier = "{{module.aws_app_identifier}}"
      }
    }
  {% elif module.type == "resource" and module.resource_type == "database" %}
    module "{{ module.module_name }}" {
      source = "./{{ module.module_name }}"
      vpc_id = module.{{ network_module_name }}.vpc_id
      identifier = "{{module.aws_app_identifier}}"
      aws_app_identifier = "{{module.aws_app_identifier}}"
      subnets = {{module.subnets}}

      {{ 'allocated_storage="' + module.allocated_storage + '"' if module.allocated_storage is defined else '' }}
      {{ 'storage_type="' + module.storage_type + '"' if module.storage_type is defined  else '' }}
      {{ 'engine="' + module.engine + '"' if module.engine is defined  else '' }}
      {{ 'ingress_port="' + module.ingress_port + '"' if module.ingress_port is defined  else '' }}
      {{ 'connection_schema="' + module.connection_schema + '"' if module.connection_schema is defined  else '' }}
      {{ 'engine_version="' + module.engine_version + '"' if module.engine_version is defined  else '' }}
      {{ 'instance_class="' + module.instance_class + '"' if module.instance_class is defined  else '' }}
      {{ 'database_name="' + module.database_name + '"' if module.database_name is defined  else '' }}
      {{ 'database_username="' + module.database_username + '"' if module.database_username is defined  else '' }}
      {{ 'publicly_accessible="' + module.publicly_accessible + '"' if module.publicly_accessible is defined  else '' }}
      {{ 'snapshot_identifier="' + module.snapshot_identifier + '"' if module.snapshot_identifier is defined  else '' }}
      {{ 'security_groups=' + module.security_groups if module.security_groups is defined  else '' }}

      tags = {
        digger_identifier = "{{module.aws_app_identifier}}"
      }
    }
  {% elif module.type == "resource" and module.resource_type == "redis" %}
    module "{{ module.module_name }}" {
      source = "./{{ module.module_name }}"
      vpc_id = module.{{ network_module_name }}.vpc_id
      cluster_id = "{{module.aws_app_identifier}}"
      private_subnets = {{module.private_subnets_ids}}
      cluster_description = "{{module.aws_app_identifier}}"

      {{ 'engine_version="' + module.redis_engine_version + '"' if module.redis_engine_version is defined  else '' }}
      {{ 'redis_node_type="' + module.redis_instance_class + '"' if module.redis_instance_class is defined  else '' }}
      {{ 'redis_number_nodes=' + module.redis_number_nodes | string if module.redis_number_nodes is defined  else '' }}
      {{ 'security_groups=' + module.security_groups if module.security_groups is defined  else '' }}
      tags = {
        digger_identifier = "{{module.aws_app_identifier}}"
      }
    }
    {% elif module.type == "resource" and module.resource_type == "docdb" %}
    module "{{ module.module_name }}" {
      source = "./{{ module.module_name }}"
      vpc_id = module.{{ network_module_name }}.vpc_id
      cluster_identifier = "{{module.aws_app_identifier}}"
      private_subnets = {{module.private_subnets_ids}}


      {{ 'engine_version="' + module.docdb_engine_version + '"' if module.docdb_engine_version is defined  else '' }}
      {{ 'instance_class="' + module.docdb_instance_class + '"' if module.docdb_instance_class is defined  else '' }}
      {{ 'instances_number=' + module.instances_number | string if module.instances_number is defined  else '' }}
      {{ 'security_groups=' + module.security_groups if module.security_groups is defined  else '' }}
      tags = {
        digger_identifier = "{{module.aws_app_identifier}}"
      }
    }
  {% elif module.type == "s3" %}
    module "{{ module.module_name }}" {
      source = "./{{ module.module_name }}"
    }
  {% elif module.type == "sqs" %}
    module "{{ module.module_name }}" {
      source = "./{{ module.module_name }}"
    }
  {% elif module.type == "api-gateway" %}
    module "{{ module.module_name }}" {
      source = "./{{ module.module_name }}"
      subnets = {{ module.subnets }}
      vpc_id = module.{{ network_module_name }}.vpc_id
    }
  {% endif %}
{% endfor %}



