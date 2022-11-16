import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
from pprint import pprint

from jinja2 import Template

from exceptions import PayloadValidationException, GitHubError


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

    with open(f"{path}/ecs_task_policy.json", "w") as f:
        f.write(s)


def clone_public_github_repo(repo, ref, path="."):
    print(f"clone_public_github_repo: {repo}, {ref}")
    url = f"https://github.com/diggerhq/{repo}"
    try:
        if ref is None:
            subprocess.run(["git", "clone", "--depth", "1", url, path], check=True)
        else:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", ref, url, path], check=True
            )
    except subprocess.CalledProcessError as cpe:
        print(f"clone_public_github_repo exception: {cpe}")
        raise GitHubError(f"Failed to clone {repo}, branch: {ref}")


def terraform_format(path="."):
    subprocess.run(["terraform", "fmt"], cwd=path, check=True)


def strip_new_lines(text):
    result = ""
    for line in text.splitlines():
        if line and not line.isspace():
            result += line + "\n"
        if line and line[0] == "}":
            result += "\n"
    return result


def format_generated_terraform(terraform_dir):
    # run 'terraform fmt' first
    terraform_format(terraform_dir)

    # and then delete all empty lines in tf files
    files = [f for f in os.listdir(terraform_dir) if re.match(r"^.*\.tf", f)]
    for f in files:
        with open(f"{terraform_dir}/{f}", "r") as tf_file:
            tf_content = tf_file.read()
            tf_content = strip_new_lines(tf_content)

        with open(f"{terraform_dir}/{f}", "w") as tf_file:
            tf_file.write(tf_content)


def render_jinja_template(
    terraform_options, input_file, output_file, delete_original=False
):
    with open(input_file) as template_file:
        template_content = template_file.read()
        template = Template(template_content)
        template_rendered = template.render(terraform_options)
        template_rendered = strip_new_lines(template_rendered)

    # skip empty files
    if len(template_rendered) > 0:
        with open(output_file, "w") as template_file_output:
            template_file_output.write(template_rendered)

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


def process_vpc_module(dest_dir, terraform_options, repo, repo_branch, debug=False):
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

        format_generated_terraform(tmp_dir_name)

        # copy generated files from tmp dir to dest_dir
        files = [f for f in os.listdir(tmp_dir_name) if re.match(r"^.*\.tf", f)]
        for f in files:
            shutil.copy2(os.path.join(tmp_dir_name, f), dest_dir)

    if debug:
        jinja_vars_file = f"{dest_dir}/jinja.vars"
        with open(jinja_vars_file, "w") as jinja_vars_file:
            jinja_vars_file.write(json.dumps(terraform_options, indent=2))


def process_ecs_module(dest_dir, terraform_options, repo, repo_branch, debug=False):
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
        format_generated_terraform(tmp_dir_name)

        # copy generated files from tmp dir to dest_dir
        files = [f for f in os.listdir(tmp_dir_name) if re.match(r"^.*\.tf", f)]
        for f in files:
            shutil.copy2(os.path.join(tmp_dir_name, f), dest_dir)

    if debug:
        jinja_vars_file = f"{dest_dir}/jinja.vars"
        with open(jinja_vars_file, "w") as jinja_vars_file:
            jinja_vars_file.write(json.dumps(terraform_options, indent=2))


def process_resource_module(
    dest_dir, terraform_options, repo, repo_branch, debug=False
):
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

        format_generated_terraform(tmp_dir_name)

        # copy generated files from tmp dir to dest_dir
        files = [f for f in os.listdir(tmp_dir_name) if re.match(r"^.*\.tf", f)]
        for f in files:
            shutil.copy2(os.path.join(tmp_dir_name, f), dest_dir)

    if debug:
        jinja_vars_file = f"{dest_dir}/jinja.vars"
        with open(jinja_vars_file, "w") as jinja_vars_file:
            jinja_vars_file.write(json.dumps(terraform_options, indent=2))


def process_main_tf(dest_dir, terraform_options, main_template_file_path, debug=False):
    jinja_template = main_template_file_path
    jinja_result = f"{dest_dir}/main.tf"
    render_jinja_template(terraform_options, jinja_template, jinja_result, False)
    format_generated_terraform(dest_dir)

    if debug:
        jinja_vars_file = f"{dest_dir}/jinja.vars"
        with open(jinja_vars_file, "w") as jinja_vars_file:
            jinja_vars_file.write(json.dumps(terraform_options, indent=2))


def parse_module_target(target):
    """
    parse module's target and return repo name and branch name
    for example for diggerhq/target-network-module@main it should return ('target-network-module', 'main')
    :param target:
    :return:
    """

    target_regex = r"diggerhq\/([a-zA-Z-_]+)@([a-zA-Z-_/]+)"
    result = re.search(target_regex, target)
    if result and len(result.groups()) == 2:
        groups = result.groups()
        return groups[0], groups[1]
    else:
        raise PayloadValidationException(f"Target {target} is in a wrong format.")


def generate_terraform_project(terraform_project_dir, config):
    debug = False
    if "debug" in config and config["debug"]:
        debug = True
    if "modules" not in config:
        raise PayloadValidationException(
            '"modules" key is missing in provided configuration.'
        )
    terraform_dir = f"{terraform_project_dir}/terraform"

    if os.path.isdir(terraform_dir):
        shutil.rmtree(terraform_dir)
    os.makedirs(os.path.abspath(terraform_dir))
    network_module_name = None
    ecs_security_groups_list = []

    updated_config = {"modules": []}

    for m in config["modules"]:
        if m["type"] == "vpc":
            network_module_name = m["module_name"]
            repo, branch = parse_module_target(m["target"])
            vpc_terraform_dir = f"{terraform_dir}/{m['module_name']}"
            terraform_options = m  # todo: move to a separate dict

            process_vpc_module(
                dest_dir=vpc_terraform_dir,
                terraform_options=terraform_options,
                repo=repo,
                repo_branch=branch,
                debug=debug,
            )
            updated_config["modules"].append(m)

    for m in config["modules"]:
        if m["type"] == "container":
            ecs_security_groups_list.append(f"module.{m['module_name']}.ecs_task_security_group_id")
            ecs_terraform_dir = f"{terraform_dir}/{m['module_name']}"
            repo, branch = parse_module_target(m["target"])
            public_subnets_ids = f"module.{network_module_name}.public_subnets"
            private_subnets_ids = f"module.{network_module_name}.private_subnets"

            if "internal" in m and m["internal"]:
                m["ecs_subnet_ids"] = private_subnets_ids
            else:
                m["ecs_subnet_ids"] = public_subnets_ids
            if "alb_internal" in m and m["alb_internal"]:
                m["alb_subnet_ids"] = private_subnets_ids
            else:
                m["alb_subnet_ids"] = public_subnets_ids

            terraform_options = m  # todo: move to a separate dict

            process_ecs_module(
                dest_dir=ecs_terraform_dir,
                terraform_options=terraform_options,
                repo=repo,
                repo_branch=branch,
                debug=debug,
            )
            generate_ecs_task_execution_policy(
                ecs_terraform_dir,
                s3_bucket_arn_list=[],
                ssm_list=["*"],
                sqs_arn_list=[],
            )

            generate_ecs_task_policy(ecs_terraform_dir, use_ssm=True)
            updated_config["modules"].append(m)

    ecs_security_groups = f'[{",".join(ecs_security_groups_list)}]'
    print(f"ecs_security_groups: {ecs_security_groups}")
    for m in config["modules"]:
        if m["type"] == "resource":
            repo, branch = parse_module_target(m["target"])
            resource_terraform_dir = f"{terraform_dir}/{m['module_name']}"
            public_subnets_ids = f"module.{network_module_name}.public_subnets"
            private_subnets_ids = f"module.{network_module_name}.private_subnets"

            if "publicly_accessible" in m and m["publicly_accessible"]:
                m["subnets"] = public_subnets_ids
            else:
                m["subnets"] = private_subnets_ids
            m['security_groups'] = ecs_security_groups

            terraform_options = m  # todo: move to a separate dict

            process_resource_module(
                dest_dir=resource_terraform_dir,
                terraform_options=terraform_options,
                repo=repo,
                repo_branch=branch,
                debug=debug,
            )
            updated_config["modules"].append(m)

    # pprint(f"updated_config: {updated_config}")
    main_tf_options = config
    main_tf_options["network_module_name"] = network_module_name
    process_main_tf(
        dest_dir=terraform_dir,
        terraform_options=main_tf_options,
        main_template_file_path="./main.template.tf",
        debug=debug,
    )

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        name = "terraform"
        extension = "zip"

        # it's important to not to change current dir in lambda otherwise it will blow up on the next request
        current_dir = os.getcwd()
        try:
            os.chdir(terraform_dir)
            shutil.make_archive(
                base_name=name, format=extension, root_dir=terraform_dir
            )
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
