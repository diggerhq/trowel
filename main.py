"""
from utils import generate_ecs_task_execution_policy, generate_ecs_task_policy, process

generate_ecs_task_execution_policy(
    "/tmp/tf-gen",
    s3_bucket_arn_list=["arn:aws:s3:::digger-terraform-projects-dev"],
    ssm_list=["*"],
    sqs_arn_list=[],
)

generate_ecs_task_policy("/tmp/tf-gen", use_ssm=True)


repo = "git@github.com:diggerhq/target-network-module.git"
repo_branch = "main"
module_name = "target-network-module-tmp"
templates = [("/vpc.template.tf", "/vpc.tf")]
terraform_options = {"enable_vpc_endpoints": True}
process("/tmp/tf-gen", repo, repo_branch, module_name, templates, terraform_options)


# ecs with public facing alb
repo = "git@github.com:diggerhq/target-ecs-module.git"
repo_branch = "dev"
module_name = "target-ecs-module-tmp"
templates = [("/service.template.tf", "/service.tf")]
terraform_options = {
    "environment_config": {},
    "aws_app_identifier": "test-app",
    "launch_type": "FARGATE",
    "load_balancer": "true",
    "internal": "true",
}
process("/tmp/tf-gen", repo, repo_branch, module_name, templates, terraform_options)

# ecs with public facing alb
repo = "git@github.com:diggerhq/target-ecs-module.git"
repo_branch = "dev"
module_name = "target-ecs-private-alb-module-tmp"
templates = [("/service.template.tf", "/service.tf")]
terraform_options = {
    "environment_config": {},
    "aws_app_identifier": "test-app",
    "launch_type": "FARGATE",
    "load_balancer": "true",
    "internal": "true",
    "alb_internal": "true",
}
process("/tmp/tf-gen", repo, repo_branch, module_name, templates, terraform_options)

repo = "git@github.com:diggerhq/target-rds-module.git"
repo_branch = "dev"
module_name = "target-rds-tmp"
templates = [("/terraform.template.tfvars", "/terraform.tfvars")]
terraform_options = {
    "resource_type": "database",
    "db_name": "testdb",
    "rds_engine": "postgres",
    "aws_app_identifier": "dddd",
}
process("/tmp/tf-gen", repo, repo_branch, module_name, templates, terraform_options)

""
module_name = "target-resource-redis-tmp"
terraform_options = {
    "resource_type": "redis",
    "db_name": "testdb",
    "aws_app_identifier": "dddd",
    "redis_engine_version": "1.4.14",
}
process("/tmp/tf-gen", repo, repo_branch, module_name, templates, terraform_options)

module_name = "target-resource-docdb-tmp"
terraform_options = {
    "resource_type": "docdb",
    "db_name": "testdb",
    "aws_app_identifier": "dddd",
}


process("/tmp/tf-gen", repo, repo_branch, module_name, templates, terraform_options)
"""
