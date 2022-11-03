import json
import os
import shutil
import subprocess
import tempfile

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


def clone_repo(url, ref, path="."):
    if ref is None:
        subprocess.run(["git", "clone", "--depth", "1", url, path], check=True)
    else:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", ref, url, path], check=True
        )


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

    with open(f"{output_file}", "w") as tvars_file_output:
        tvars_file_output.write(tvars_content_rendered)
        tvars_file_output.close()

    if delete_original:
        os.remove(input_file)


def process(dest_dir, repo, repo_branch, module_name, templates, terraform_options):
    dest_jinja_dir = dest_dir + "/" + module_name

    if os.path.isdir(dest_jinja_dir):
        shutil.rmtree(dest_jinja_dir)

    clone_repo(repo, repo_branch, dest_jinja_dir)

    for t in templates:
        jinja_template = dest_jinja_dir + t[0]
        jinja_result = dest_jinja_dir + t[1]
        render_jinja_template(terraform_options, jinja_template, jinja_result, True)

    terraform_format(dest_jinja_dir)

