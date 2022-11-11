                             provider "aws" {
  region = "{{ aws_region }}"
}

{% for module in modules %}
  {% if module.type == "vpc" %}
    module "{{ module.module_name}}" {
      source = "./{{ module.module_name }}"
      network_name = "{{module.module_name}}"
      region = "{{ aws_region }}"
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

      ecs_task_policy_json = "{{module.ecs_task_policy_json}}"
      ecs_task_execution_policy_json = "{{module.ecs_task_execution_policy_json}}"
      private_subnets = module.{{ network_module_name }}.private_subnets
      public_subnets = module.{{ network_module_name }}.public_subnets
      alb_subnet_ids = {{module.alb_subnet_ids}}
      ecs_subnet_ids = {{module.ecs_subnet_ids}}
      container_port = {{module.container_port}}
      region = "{{ aws_region }}"
      alarms_sns_topic_arn = ""
      tags = {
        digger_identifier = "{{module.aws_app_identifier}}"
      }
    }
  {% elif module.type == "resource" %}
    module "{{ module.module_name }}" {
      source = "./{{ module.module_name }}"
      vpc_id = module.network.vpc_id
      private_subnets = module.network.private_subnets
      public_subnets = module.network.public_subnets
      security_groups = flatten({{ security_groups | join(", ") or []}})
      aws_app_identifier = "{{module.aws_app_identifier}}"
      region = "{{ aws_region }}"
      tags = {
        digger_identifier = "{{module.aws_app_identifier}}"
      }
    }
  {% endif %}
{% endfor %}

