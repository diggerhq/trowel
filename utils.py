import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
from pprint import pprint

from jinja2 import Template


def generate_ecs_task_execution_policy(
    path, s3_bucket_arn_list, ssm_list, sqs_arn_list
):
    result = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                "Resource": "*",
            }
        ],
    }

    if s3_bucket_arn_list:
        s3_statement = {
            "Sid": "s3",
            "Action": "s3:*",
            "Effect": "Allow",
            "Resource": s3_bucket_arn_list,
        }
        result["Statement"].append(s3_statement)
    if ssm_list:
        ssm_statement = {
            "Sid": "SSM",
            "Effect": "Allow",
            "Action": "ssm:*",
            "Resource": ssm_list,
        }
        result["Statement"].append(ssm_statement)
    if sqs_arn_list:
        sqs_statement = {
            "Sid": "SQS",
            "Effect": "Allow",
            "Action": "sqs:*",
            "Resource": sqs_arn_list,
        }
        result["Statement"].append(sqs_statement)

    s = json.dumps(
        result,
        sort_keys=False,
        indent=2,
    )
    print(s)

    with open(f"{path}/ecs_task_execution_policy.json", "w") as f:
        f.write(s)


def generate_ecs_task_policy(path, use_ssm=False):
    result = {"Version": "2012-10-17", "Statement": []}

    ecr_statement = {
        "Sid": "ECR",
        "Effect": "Allow",
        "Action": [
            "ecr:GetAuthorizationToken",
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
        ],
        "Resource": "*",
    }
    result["Statement"].append(ecr_statement)

    logs_statement = {
        "Sid": "CloudWatch",
        "Effect": "Allow",
        "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
        "Resource": "*",
    }
    result["Statement"].append(logs_statement)

    if use_ssm:
        ssm_statement = {
            "Sid": "SSM",
            "Effect": "Allow",
            "Action": ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
            "Resource": "*",
        }
        result["Statement"].append(ssm_statement)

    s = json.dumps(
        result,
        sort_keys=False,
        indent=2,
    )
    print(s)

    with open(f"{path}/ecs_task_policy.json", "w") as f:
        f.write(s)


def clone_public_github_repo(repo, ref, path="."):
    url = f'https://github.com/diggerhq/{repo}'
    try:
        if ref is None:
            subprocess.run(["git", "clone", "--depth", "1", url, path], check=True)
        else:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", ref, url, path], check=True
            )
    except subprocess.CalledProcessError as cpe:
        print(cpe)
        raise


def terraform_format(path="."):
    subprocess.run(["terraform", "fmt"], cwd=path, check=True)


def strip_new_lines(text):
    result = ""
    for line in text.splitlines():
        if line and not line.isspace():
            result += line + "\n"
        if line == "}":
            result += "\n"
    return result


def render_jinja_template(
    terraform_options, input_file, output_file, delete_original=False
):
    with open(input_file) as tvars_file:
        tvars_content = tvars_file.read()
        tvars_template = Template(tvars_content)
        tvars_content_rendered = tvars_template.render(terraform_options)
        tvars_content_rendered = strip_new_lines(tvars_content_rendered)

    # print(f'{input_file}: {len(tvars_content_rendered)}')

    # skip empty files
    if len(tvars_content_rendered) > 0:
        with open(output_file, "w") as tvars_file_output:
            tvars_file_output.write(tvars_content_rendered)

    if delete_original:
        os.remove(input_file)


def process(dest_dir, repo, repo_branch, module_name, templates, terraform_options):
    dest_jinja_dir = dest_dir + "/" + module_name

    if os.path.isdir(dest_jinja_dir):
        shutil.rmtree(dest_jinja_dir)

    clone_public_github_repo(repo, repo_branch, dest_jinja_dir)

    for t in templates:
        jinja_template = dest_jinja_dir + t[0]
        jinja_result = dest_jinja_dir + t[1]
        render_jinja_template(terraform_options, jinja_template, jinja_result, True)

    terraform_format(dest_jinja_dir)


def process_vpc_module(dest_dir, terraform_options, repo, repo_branch):

    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)

    os.makedirs(os.path.abspath(dest_dir))

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        clone_public_github_repo(repo, repo_branch, tmp_dir_name)

        jinja_template_files = [
            f for f in os.listdir(tmp_dir_name) if re.match(r"^.*\.template\..", f)
        ]
        jinja_templates = []
        for j in jinja_template_files:
            jinja_templates.append((j, j.replace(".template", "")))

        for t in jinja_templates:
            jinja_template = f"{tmp_dir_name}/{t[0]}"
            jinja_result = f"{tmp_dir_name}/{t[1]}"
            render_jinja_template(terraform_options, jinja_template, jinja_result, True)
        terraform_format(tmp_dir_name)

        # copy generated files from tmp dir to dest_dir
        files = [f for f in os.listdir(tmp_dir_name) if re.match(r"^.*\.tf", f)]
        for f in files:
            print(f)
            shutil.copy2(os.path.join(tmp_dir_name, f), dest_dir)

    jinja_vars_file = f"{dest_dir}/jinja.vars"
    with open(jinja_vars_file, "w") as jinja_vars_file:
        jinja_vars_file.write(json.dumps(terraform_options, indent=2))


def process_ecs_module(dest_dir, terraform_options, repo, repo_branch):
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)

    os.makedirs(os.path.abspath(dest_dir))

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        clone_public_github_repo(repo, repo_branch, tmp_dir_name)

        jinja_template_files = [
            f for f in os.listdir(tmp_dir_name) if re.match(r"^.*\.template\..", f)
        ]
        jinja_templates = []
        for j in jinja_template_files:
            jinja_templates.append((j, j.replace(".template", "")))

        for t in jinja_templates:
            jinja_template = f"{tmp_dir_name}/{t[0]}"
            jinja_result = f"{tmp_dir_name}/{t[1]}"
            render_jinja_template(terraform_options, jinja_template, jinja_result, True)
        terraform_format(tmp_dir_name)

        # copy generated files from tmp dir to dest_dir
        files = [f for f in os.listdir(tmp_dir_name) if re.match(r"^.*\.tf", f)]
        for f in files:
            print(f)
            shutil.copy2(os.path.join(tmp_dir_name, f), dest_dir)

    jinja_vars_file = f"{dest_dir}/jinja.vars"
    with open(jinja_vars_file, "w") as jinja_vars_file:
        jinja_vars_file.write(json.dumps(terraform_options, indent=2))


def process_main_tf(dest_dir, terraform_options, main_template_file_path):
    # if os.path.isdir(dest_dir):
    #    shutil.rmtree(dest_dir)

    # os.makedirs(os.path.abspath(dest_dir))

    jinja_template = main_template_file_path
    jinja_result = f"{dest_dir}/main.tf"
    render_jinja_template(terraform_options, jinja_template, jinja_result, False)
    terraform_format(dest_dir)

    jinja_vars_file = f"{dest_dir}/jinja.vars"
    with open(jinja_vars_file, "w") as jinja_vars_file:
        jinja_vars_file.write(json.dumps(terraform_options, indent=2))


def generate_terraform_project(terraform_project_dir, config):
    terraform_dir = f"{terraform_project_dir}/terraform"

    if os.path.isdir(terraform_dir):
        shutil.rmtree(terraform_dir)
    os.makedirs(os.path.abspath(terraform_dir))
    network_module_name = None
    alb_subnet_ids = None
    ecs_subnet_ids = None

    updated_config = {'modules': []}

    for m in config['modules']:
        if m['type'] == 'vpc':
            network_module_name = m['module_name']
            alb_subnet_ids = f"module.{network_module_name}.public_subnets"
            ecs_subnet_ids = f"module.{network_module_name}.private_subnets"

            vpc_terraform_dir = f"{terraform_dir}/{m['module_name']}"
            vpc_repo = "target-network-module"  # todo: parse m['target']
            vpc_repo_branch = "main"            # todo: parse m['target']

            terraform_options = m   # todo: move to a separate dict

            process_vpc_module(
                dest_dir=vpc_terraform_dir,
                terraform_options=terraform_options,
                repo=vpc_repo,
                repo_branch=vpc_repo_branch,
            )
            updated_config['modules'].append(m)

    for m in config['modules']:
        if m['type'] == 'container':
            ecs_terraform_dir = f"{terraform_dir}/{m['module_name']}"
            ecs_repo = "target-ecs-module"      # todo: parse m['target']
            ecs_repo_branch = "dev"             # todo: parse m['target']


            m['alb_subnet_ids'] = alb_subnet_ids
            m['ecs_subnet_ids'] = ecs_subnet_ids
            terraform_options = m  # todo: move to a separate dict

            """
            terraform_options = {
                "environment_config": {},
                "aws_app_identifier": "test-app",
                "launch_type": "FARGATE",
                "load_balancer": "true",
                "internal": str(True).lower(),
                "is_monitoring_enabled": True,
            }"""

            process_ecs_module(
                dest_dir=ecs_terraform_dir,
                terraform_options=terraform_options,
                repo=ecs_repo,
                repo_branch=ecs_repo_branch,
            )
            updated_config['modules'].append(m)

        """
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
        """

    pprint(f'updated_config: {updated_config}')
    main_tf_options = config
    main_tf_options['network_module_name'] = network_module_name
    process_main_tf(
        dest_dir=terraform_dir,
        terraform_options=main_tf_options,
        main_template_file_path="./main.template.tf",
    )

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        name = "terraform"
        extension = "zip"

        # it's important to not to change current dir in lambda otherwise it will blow up on the next request
        current_dir = os.getcwd()
        try:
            os.chdir(terraform_dir)
            shutil.make_archive(base_name=name, format=extension, root_dir=terraform_dir)
            shutil.move(f"{name}.{extension}", tmp_dir_name)
        finally:
            os.chdir(current_dir)

        with open(f"{tmp_dir_name}/{name}.{extension}", "rb") as terraform_zip:
            zip = terraform_zip.read()
            encoded_zip = base64.encodebytes(zip)

            return {
                "headers": {"Content-Type": "application/zip"},
                "statusCode": 200,
                "body": encoded_zip,
                "isBase64Encoded": True,
            }
