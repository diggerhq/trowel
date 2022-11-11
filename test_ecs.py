import os

from utils import generate_terraform_project

current_dir = os.getcwd()

config = payload = {
    "target": "diggerhq/tf-module-bundler@master",
    "for_local_run": True,
    "aws_region": "us-east-1",
    "aws_key": None,
    "aws_secret": None,
    "assume_role_arn": None,
    "assume_role_external_id": None,
    "modules": [
        {
            "module_name": "network-env-test-1",
            "target": "diggerhq/target-network-module@main",
            "type": "vpc",
            "network_name": "env-test-1",
            "enable_vpc_endpoints": False,
            "enable_dns_hostnames": False,
            "enable_dns_support": True,
            "one_nat_gateway_per_az": True,
            "enable_nat_gateway": False,
        },
        {
            "module_name": "container-test",
            "target": "diggerhq/target-ecs-module@feat/render-secrets",
            "type": "container",
            "task_cpu": 1024,
            "task_memory": 2048,
            "health_check": "/",
            "load_balancer": True,
            "internal": "true",
            "container_port": 8080,
            "health_check_matcher": "200",
            "launch_type": "FARGATE",
            "aws_app_identifier": "test",
            "monitoring_enabled": False,
            "environment_variables": [
                {"key": "TEST_VAR", "value": "TEST_VALUE"},
                {"key": "TEST_VAR2", "value": "TEST_VALUE2"},
            ],
            "secret_keys": ["SECRET_1", "SECRET_2"],
        },
    ],
    "security_groups": ["module.container-container-test.security_group_ids"],
}

generate_terraform_project(f'{current_dir}/terraform', config)


"""

# generate_ecs_task_execution_policy(
#    terraform_dir,
#    s3_bucket_arn_list=[],
#    ssm_list=["*"],
#    sqs_arn_list=[],
# )

# generate_ecs_task_policy(terraform_dir, use_ssm=True)


terraform_dir = "./terraform"
# vpc
vpc_terraform_dir = "./terraform/vpc"
vpc_repo = "git@github.com:diggerhq/target-network-module.git"
vpc_repo_branch = "main"

# ecs with public facing alb
ecs_terraform_dir = "./terraform/ecs"
ecs_repo = "git@github.com:diggerhq/target-ecs-module.git"
ecs_repo_branch = "dev"

terraform_options = {
    "environment_config": {},
    "aws_app_identifier": "test-app",
    "launch_type": "FARGATE",
    "load_balancer": "true",
    "internal": str(True).lower(),
    "is_monitoring_enabled": True,
}

process_vpc_module(
    dest_dir=vpc_terraform_dir,
    terraform_options=terraform_options,
    repo=vpc_repo,
    repo_branch=vpc_repo_branch,
)
process_ecs_module(
    dest_dir=ecs_terraform_dir,
    terraform_options=terraform_options,
    repo=ecs_repo,
    repo_branch=ecs_repo_branch,
)

network_module_name = "myvpc"
ecs_module_name = "ecs"
app_name = "myapp"

main_tf_options = {
    "aws_region": "us-east-1",
    "modules": [
        {"type": "vpc", "source": "./vpc", "name": network_module_name},
        {
            "type": "container",
            "name": ecs_module_name,
            "source": "./ecs",
            "aws_app_identifier": app_name,
            "container_port": "8000",
            "container_name": app_name,
            "ecs_task_execution_policy_json": "{}",
            "ecs_task_policy_json": "{}",
            "alb_subnet_ids": f"module.{network_module_name}.public_subnets",
            "ecs_subnet_ids": f"module.{network_module_name}.private_subnets",
        },
    ],
    "network_module_name": network_module_name,
}

process_main_tf(
    dest_dir=terraform_dir,
    terraform_options=main_tf_options,
    main_template_file_path="./main.template.tf",
)
"""
