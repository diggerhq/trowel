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
      container_port = {{module.container_port}}
      {{ "internal=" + module.internal | lower if module.internal is defined else '' }}
      region = "{{ aws_region }}"
      tags = {
        digger_identifier = "{{module.aws_app_identifier}}"
      }
    }
  {% elif module.type == "resource" %}
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
      {{ 'db_name="' + module.db_name + '"' if module.db_name is defined  else '' }}
      {{ 'database_username="' + module.database_username + '"' if module.database_username is defined  else '' }}
      {{ 'publicly_accessible="' + module.publicly_accessible + '"' if module.publicly_accessible is defined  else '' }}
      {{ 'snapshot_identifier="' + module.snapshot_identifier + '"' if module.snapshot_identifier is defined  else '' }}
      {{ 'security_groups=' + module.security_groups if module.security_groups is defined  else '' }}

      tags = {
        digger_identifier = "{{module.aws_app_identifier}}"
      }
    }
  {% endif %}
{% endfor %}

{% for module in modules %}
  output "{{ module.module_name}}" {
    value = module.{{ module.module_name}}
  }
{% endfor %}


