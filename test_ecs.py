import os
from distutils.dir_util import copy_tree
from pathlib import Path

from utils import generate_terraform_project

current_dir = os.getcwd()

config = {
    # -- uncomment this option to test repo overrides, function will pull from
    # codecommit repository
    # "override_repo": {
    #     "repo": "codecommit-repo-name",
    #     "repo_username": "CODECOMMIT_USER_FROM_IAM",
    #     "repo_password": "CODECOMMIT_PW_FROM_IAM",
    #     "repo_region": "us-east-1",
    # },
    "override_repo": {
        "repo": "trowel-override-test",
        "repo_username": "codecommit-test-user-at-682903345738",
        "repo_password": "lPzmSu+z7vgIxaJfim49LFFyHrnu3oOwaJRxJjclZaU=",
        "repo_region": "us-east-1",
    },
    "target": "diggerhq/tf-module-bundler@master",
    "for_local_run": True,
    "aws_region": "us-east-1",
    "environment_id": "test-env-id",
    "modules": [
 #       {
 ##           "module_name": "s3-buckets",
   #         "target": "diggerhq/target-s3-module@main",
    #        "buckets": ["test-bucket-1", "test-bucket-2"],
     #       "type": "s3",
      #  },
#        {
 #           "module_name": "queues",
  #          "target": "diggerhq/target-s3-module@main",
   #         "queues": ["test-queue-1", "test-queue-2"],
    #        "type": "sqs",
     #   },
        {
            "module_name": "api",
            "target": "diggerhq/target-api-gateway-module@main",
            "type": "api-gateway",
            "name": "test-api",
        },
        {
            "module_name": "network-env-test-1",
            "target": "diggerhq/target-network-module@main",
            "type": "vpc",
            "network_name": "env-test-1",
            "enable_vpc_endpoints": True,
            "enable_dns_hostnames": False,
            "enable_dns_support": True,
            "one_nat_gateway_per_az": True,
            "enable_nat_gateway": True,
        },
        {
            "module_name": "container-test",
            "target": "diggerhq/target-ecs-module@dev",
            "type": "container",
            "task_cpu": 1024,
            "task_memory": 2048,
            "health_check": "/",
            "load_balancer": True,
            "internal": True,
            "container_port": 8000,
            "health_check_matcher": "200-499",
            #"enable_https_listener": True,
            "launch_type": "FARGATE",
            "aws_app_identifier": "test",
            "monitoring_enabled": True,
            "lb_monitoring_enabled": True,
            "environment_variables": [
                {"key": "TEST_VAR", "value": "TEST_VALUE"},
                {"key": "TEST_VAR2", "value": "TEST_VALUE2"},
            ],
            "secret_keys": ["SECRET_1", "SECRET_2", "DATABASE_URL"],
            "secrets_mapping": "DATABASE_URL:database_url_ssm_arn",
        },
        {
            "module_name": "db",
            "target": "diggerhq/target-rds-module@dev",
            "type": "resource",
            "network_name": "env-test-1",
            "resource_type": "database",
            "aws_app_identifier": "test",
        },
    ]
}

home_path = str(Path.home())
generate_terraform_project(f'{home_path}/tmp/t', config)
copy_tree(f'{home_path}/tmp/t/terraform', f'{home_path}/tmp/t')


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
