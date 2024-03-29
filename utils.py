import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
from urllib.parse import quote
from jinja2 import Template
from jinja2.filters import FILTERS

from exceptions import (
    PayloadValidationException,
    GitHubError,
    TerraformFormatError,
    ValidationError,
)
from hcl import (
    convert_string_to_hcl,
    convert_dict_to_hcl,
    convert_config_parameters_to_hcl,
    convert_secrets_list_to_hcl,
    replace_terraform_parameters,
)
from validators import validate_bastion_parameters


def add_debug_info(dest_dir, terraform_options):
    jinja_vars_file = f"{dest_dir}/jinja.vars"
    with open(jinja_vars_file, "w") as jinja_vars_file:
        jinja_vars_file.write(json.dumps(terraform_options, indent=2))


def recreate_dir(dest_dir):
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(os.path.abspath(dest_dir))


def run_jinja_for_dir(repo, repo_branch, terraform_options, dest_dir):
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


def generate_ecs_task_execution_policy(
    path, s3_bucket_arn_list, ssm_list, sqs_arn_list, datadog_enabled
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

    if datadog_enabled:
        datadog_statement = {
            "Sid": "DataDogFireHose",
            "Effect": "Allow",
            "Action": "firehose:PutRecordBatch",
            "Resource": ["*"],
        }
        result["Statement"].append(datadog_statement)

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


def clone_codecommit_repo(
    repo, repo_user, repo_password, repo_region="us-east-2", ref=None, path="."
):
    print(f"clone_codecommit_repo: {repo}")
    repo_password = quote(repo_password, safe="")
    url = f"https://{repo_user}:{repo_password}@git-codecommit.{repo_region}.amazonaws.com/v1/repos/{repo}"
    try:
        if ref is None:
            subprocess.run(["git", "clone", "--depth", "1", url, path], check=True)
        else:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", ref, url, path], check=True
            )
    except subprocess.CalledProcessError as cpe:
        print(f"clone_codecommit_repo exception: {cpe}")
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
    try:
        terraform_format(terraform_dir)
    except subprocess.CalledProcessError:
        print("Failed to format terraform project.")
        # raise TerraformFormatError("Failed to format terraform project.")

    # and then delete all empty lines in tf files
    files = [f for f in os.listdir(terraform_dir) if re.match(r"^.*\.tf", f)]
    for f in files:
        with open(f"{terraform_dir}/{f}", "r") as tf_file:
            tf_content = tf_file.read()
            tf_content = strip_new_lines(tf_content)

        with open(f"{terraform_dir}/{f}", "w") as tf_file:
            tf_file.write(tf_content)


def dashify(value, attribute=None):
    return str(value).replace("_", "-")


def underscorify(value, attribute=None):
    return str(value).replace("-", "_")


FILTERS["dashify"] = dashify
FILTERS["underscorify"] = underscorify


def render_jinja_template(
    terraform_options, input_file, output_file, delete_original=False
):
    print(f"input_file:{input_file},terraform_options:{terraform_options}")
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


def process_terraform_overrides(
    dest_dir,
    override_repo_name,
    override_repo_username,
    override_repo_password,
    override_repo_region,
    override_repo_branch=None,
):
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        overrides_dir = os.path.join(tmp_dir_name, "overrides")
        clone_codecommit_repo(
            override_repo_name,
            override_repo_username,
            override_repo_password,
            override_repo_region,
            ref=override_repo_branch,
            path=tmp_dir_name,
        )

        # copy files from overrides dir if it does exist
        if os.path.exists(overrides_dir):
            # copy generated files from tmp dir to dest_dir
            files = [f for f in os.listdir(overrides_dir) if re.match(r"^.*\.tf", f)]
            for f in files:
                shutil.copy2(os.path.join(overrides_dir, f), dest_dir)


def process_custom_terraform(dest_dir, custom_terraform: str):
    print(f"process_custom_terraform:")
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        file_name = "overrides.tf"
        decoded_content = base64.b64decode(custom_terraform)
        with open(os.path.join(dest_dir, file_name), "wb") as f:
            f.write(decoded_content)

        # copy generated files from tmp dir to dest_dir
        files = [f for f in os.listdir(tmp_dir_name) if re.match(r"^.*\.tf", f)]
        for f in files:
            shutil.copy2(os.path.join(tmp_dir_name, f), dest_dir)


def process_vpc_module(dest_dir, terraform_options, repo, repo_branch, debug=False):
    print(f"process_vpc_module, dest_dir: {dest_dir}")
    recreate_dir(dest_dir)
    run_jinja_for_dir(repo, repo_branch, terraform_options, dest_dir)
    if debug:
        add_debug_info(dest_dir, terraform_options)


def process_secrets_mapping(mappings: list):
    result = []
    for i in mappings:
        item = {}
        name, block_ssm = i.split(":")
        # block_name, ssm = block_ssm.split(".")
        # print(f"name: {name}, block: {block_name}, ssm: {ssm}")
        item["key"] = name
        item["value"] = "module." + block_ssm

        result.append(item)
    return result


def process_ecs_module(
    terraform_dir,
    block_options: dict,
    digger_config: dict,
    repo,
    repo_branch,
    debug=False,
    datadog_enabled=False,
    config_dir=None,
):
    if (
        "shared_terraform_module" in block_options
        and block_options["shared_terraform_module"]
    ):
        ecs_terraform_dir = (
            f"{terraform_dir}/{block_options['shared_terraform_module_name']}"
        )
    else:
        ecs_terraform_dir = f"{terraform_dir}/{block_options['name']}"
    print(f"process_ecs_module, dest_dir: {ecs_terraform_dir}")
    recreate_dir(ecs_terraform_dir)

    env_secrets = None
    # read secrets and envs from file if it does exist
    if config_dir and os.path.isfile(config_dir + "/envs/" + block_options["name"]):
        with open(config_dir + "/envs/" + block_options["name"], "r") as fp:
            env_secrets = json.load(fp)

            env_params = {
                "qa": {
                    "$APP_ENV": "QA",
                    "$CACHE_HOST": "https://olaclick.dev/ms-cache",
                    "$DB_CONNECTION": "mysql",
                    "$DEBUGBAR_ENABLED": "true",
                    "$AWS_DEFAULT_REGION": "us-east-1",
                },
                "prod": {},
            }

            print(f"name: {block_options['name']}")
            for e in env_secrets["environment"]:
                if e["value"] in env_params["qa"].keys():
                    e["value"] = env_params["qa"][e["value"]]
                print("-------------------------------------")
                print(e["value"])
                if str(e["value"]).startswith("module."):
                    pass

    # copy "shared" env variables from the root level
    environment_variables = []
    if "environment_variables" in digger_config:
        environment_variables = digger_config["environment_variables"].copy()
    if "environment_variables" in block_options:
        environment_variables += block_options["environment_variables"].copy()
    if env_secrets:
        environment_variables += env_secrets["environment"].copy()

    block_options["environment_variables"] = convert_string_to_hcl(
        json.dumps(environment_variables, indent=2)
    )

    # replace terraform parameters in ##param## with param without quotes
    block_options["environment_variables"] = replace_terraform_parameters(
        block_options["environment_variables"]
    )

    # copy "shared" secrets from the root level
    secrets = []
    secrets_mappings = []
    if "secrets" in digger_config:
        secrets += digger_config["secrets"]
    if "secrets" in block_options:
        secrets += block_options["secrets"]
    if env_secrets:
        secrets += env_secrets["secrets"]
    if "secret_mappings" in block_options:
        secrets_mappings = process_secrets_mapping(block_options["secret_mappings"])

    aws_region = digger_config["aws_region"]
    aws_account_id = digger_config["aws_account_id"]

    # copy shared_ecs_cluster settings from the root level
    if "shared_ecs_cluster" in digger_config and digger_config["shared_ecs_cluster"]:
        block_options["shared_ecs_cluster"] = digger_config["shared_ecs_cluster"]
        block_options["shared_ecs_cluster_name"] = digger_config[
            "shared_ecs_cluster_name"
        ]
        if "shared_ecs_capacity_provider_strategy_is_fargate_spot" in digger_config:
            block_options["capacity_provider_strategy_is_fargate_spot"] = digger_config[
                "shared_ecs_capacity_provider_strategy_is_fargate_spot"
            ]

    block_options["secrets"] = convert_secrets_list_to_hcl(
        secrets, secrets_mappings, aws_region, aws_account_id
    )

    run_jinja_for_dir(repo, repo_branch, block_options, ecs_terraform_dir)

    generate_ecs_task_execution_policy(
        ecs_terraform_dir,
        s3_bucket_arn_list=[],
        ssm_list=["*"],
        sqs_arn_list=[],
        datadog_enabled=datadog_enabled,
    )
    generate_ecs_task_policy(ecs_terraform_dir, use_ssm=True)

    if debug:
        add_debug_info(ecs_terraform_dir, block_options)


def process_s3_module(dest_dir, terraform_options, repo, repo_branch, debug=False):
    recreate_dir(dest_dir)

    run_jinja_for_dir(repo, repo_branch, terraform_options, dest_dir)

    if debug:
        add_debug_info(dest_dir, terraform_options)


def process_sqs_module(dest_dir, terraform_options, repo, repo_branch, debug=False):
    recreate_dir(dest_dir)

    run_jinja_for_dir(repo, repo_branch, terraform_options, dest_dir)

    if debug:
        add_debug_info(dest_dir, terraform_options)


def process_api_gateway_module(
    dest_dir, terraform_options, repo, repo_branch, debug=False
):
    print(f"process_api_gateway_module, dest_dir: {dest_dir}")
    recreate_dir(dest_dir)

    run_jinja_for_dir(repo, repo_branch, terraform_options, dest_dir)

    if debug:
        add_debug_info(dest_dir, terraform_options)


def process_resource_module(
    dest_dir, terraform_options, repo, repo_branch, debug=False
):
    print(f"process_resource_module, dest_dir: {dest_dir}")
    recreate_dir(dest_dir)

    run_jinja_for_dir(repo, repo_branch, terraform_options, dest_dir)

    if debug:
        add_debug_info(dest_dir, terraform_options)


def process_tf_templates(dest_dir, terraform_options, tf_templates_dir, debug=False):
    print(f"process_tf_templates, dest_dir: {dest_dir}")

    templates = [
        "main.template.tf",
        "secrets.template.tf",
        "envs.template.tf",
        "dns.template.tf",
        "outputs.template.tf",
        "terraform.template.tfvars",
        "variables.template.tf",
    ]

    # check if shared ALB needs to be created
    if "api_gateway" in terraform_options and terraform_options["api_gateway"] is True:
        if "api_gateway_name" not in terraform_options:
            raise ValueError(
                f"api_gateway_name param is missing. If 'api_gateway' is true, then 'api_gateway_name' is mandatory."
            )
        templates.append("api_gateway.template.tf")

    # check if shared ALB needs to be created
    if "shared_alb" in terraform_options and terraform_options["shared_alb"] is True:
        if "shared_alb_name" not in terraform_options:
            raise ValueError(
                f"shared_alb_name param is missing. If 'shared_alb' is true, then 'shared_alb_name' is mandatory."
            )
        templates.append("shared_alb.template.tf")

        # shared alb is internal by default
        terraform_options["internal"] = True

        for b in terraform_options["blocks"]:
            if "listener_arn" not in b:
                b["listener_arn"] = "test_listener"
            if "alb_arn" not in b:
                b["alb_arn"] = "test_listener"

    # process backend.tf separately
    if (
        "remote_state" not in terraform_options
        or terraform_options["remote_state"] != "local"
    ):
        bundle_id = terraform_options["id"]
        region = terraform_options["backend_region"]
        aws_account_id = ""
        if "aws_account_id" in terraform_options:
            aws_account_id = "-" + terraform_options["aws_account_id"]

        backend_options = {
            "bucket": f"digger-terraform-state" + aws_account_id,
            "key": bundle_id,
            "region": region,
            "dynamodb_table": "digger-terraform-state-lock",
        }

        jinja_template = tf_templates_dir + "backend.template.tf"
        jinja_result = f"{dest_dir}/backend.tf"
        render_jinja_template(backend_options, jinja_template, jinja_result, False)

    for t in templates:
        jinja_template = tf_templates_dir + t
        r = t.replace(".template", "")
        jinja_result = f"{dest_dir}/{r}"
        render_jinja_template(terraform_options, jinja_template, jinja_result, False)
        format_generated_terraform(dest_dir)

    if debug:
        add_debug_info(dest_dir, terraform_options)


def process_static_files(dest_dir):
    shutil.copytree("./staticfiles/", f"{dest_dir}/", dirs_exist_ok=True)


def process_env_file(dest_dir, env_id):
    with open(f"{dest_dir}/.digger", "w") as f:
        f.write(f"ENVIRONMENT_ID={env_id}")


# Further file processing goes here


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


def generate_terraform_project(
    terraform_project_dir, tf_templates_dir, config, config_dir=None
):
    """
    generates terraform project for specified options in config and return it as base64 encoded zip file in
    the following json:
        {
          "statusCode": 200,
          "body": encoded_zip,
        }

    :param config_dir:
    :param terraform_project_dir:
    :param tf_templates_dir
    :param config:
    :return:
    """

    if "tags" in config:
        config["tags"] = convert_dict_to_hcl(config["tags"])
    debug = False
    if "debug" in config and config["debug"]:
        debug = True

    if "blocks" not in config:
        raise PayloadValidationException(
            '"blocks" key is missing in provided configuration.'
        )
    if "id" not in config:
        raise PayloadValidationException(
            '"id" key is missing in provided configuration.'
        )
    environment_id = config["id"]
    terraform_dir = f"{terraform_project_dir}/terraform"

    if os.path.isdir(terraform_dir):
        shutil.rmtree(terraform_dir)
    os.makedirs(os.path.abspath(terraform_dir))
    network_module_name = None
    ecs_security_groups_list = []
    block_secrets = {}

    if "enable_bastion" in config:
        validate_bastion_parameters(config)
        ecs_security_groups_list.append(f"module.bastion.bastion_security_group_id")

    config = convert_config_parameters_to_hcl(config)

    if "namespace" in config and config["namespace"]:
        for b in config["blocks"]:
            if "name" in b:
                b["name"] += "-" + config["namespace"]
            if "aws_app_identifier" in b:
                b["aws_app_identifier"] += "-" + config["namespace"]

    datadog_enabled = False
    if "datadog_enabled" in config and config["datadog_enabled"]:
        datadog_enabled = True
        if not "secrets" in config or not "DATADOG_KEY" in config["secrets"]:
            raise ValidationError(
                "If DataDog integration enabled, DATADOG_KEY secret required."
            )

    updated_config = {"blocks": []}

    for m in config["blocks"]:

        if m["type"] == "vpc":
            network_module_name = m["name"]
            repo, branch = parse_module_target(m["target"])
            vpc_terraform_dir = f"{terraform_dir}/{m['name']}"
            block_options = m  # todo: move to a separate dict

            process_vpc_module(
                dest_dir=vpc_terraform_dir,
                terraform_options=block_options,
                repo=repo,
                repo_branch=branch,
                debug=debug,
            )
            updated_config["blocks"].append(m)

    for m in config["blocks"]:
        if m["type"] == "container":
            ecs_security_groups_list.append(
                f"module.{m['name']}.ecs_task_security_group_id"
            )

            repo, branch = parse_module_target(m["target"])
            # repo = 'target-ecs-module'  # todo repo, branch hardcoded for now
            # branch = 'dev'
            public_subnets_ids = f"module.{network_module_name}.public_subnets"
            private_subnets_ids = f"module.{network_module_name}.private_subnets"

            internal = False
            if "internal" in m:
                internal_value = m["internal"]
                if isinstance(internal_value, bool):
                    internal = internal_value
                elif isinstance(internal_value, str) and internal_value == "true":
                    internal = True

            if internal:
                m["ecs_subnet_ids"] = private_subnets_ids
            else:
                m["ecs_subnet_ids"] = public_subnets_ids
            if "alb_internal" in m and m["alb_internal"]:
                m["alb_subnet_ids"] = private_subnets_ids
            else:
                m["alb_subnet_ids"] = public_subnets_ids

            block_options = m  # todo: move to a separate dict

            process_ecs_module(
                terraform_dir=terraform_dir,
                block_options=block_options,
                digger_config=config,
                repo=repo,
                repo_branch=branch,
                debug=debug,
                datadog_enabled=datadog_enabled,
                config_dir=config_dir,
            )

            updated_config["blocks"].append(m)

            if "secrets" in m:
                block_secrets[m["name"]] = m["secrets"]

        if m["type"] == "imported":
            dest_dir = f"{terraform_dir}/{m['name']}"
            recreate_dir(dest_dir)
            process_custom_terraform(
                dest_dir=dest_dir, custom_terraform=m["custom_terraform"]
            )

    ecs_security_groups = f'[{",".join(ecs_security_groups_list)}]'
    print(f"ecs_security_groups: {ecs_security_groups}")
    for m in config["blocks"]:
        if m["type"] in ["resource"]:
            print(f"resource block, type: {m['type']}")
            repo, branch = parse_module_target(m["target"])

            if m["resource_type"] == "database":
                print(f"resource block, resource_type: {m['resource_type']}")
                repo = "target-rds-module"  # todo repo, branch hardcoded for now
                branch = "dev"
                public_subnets_ids = f"module.{network_module_name}.public_subnets"
                private_subnets_ids = f"module.{network_module_name}.private_subnets"

                if "publicly_accessible" in m and m["publicly_accessible"]:
                    m["subnets"] = public_subnets_ids
                else:
                    m["subnets"] = private_subnets_ids

            elif m["resource_type"] == "redis":
                repo = (
                    "target-elasticache-module"  # todo repo, branch hardcoded for now
                )
                branch = "main"
                private_subnets_ids = f"module.{network_module_name}.private_subnets"
                m["private_subnets_ids"] = private_subnets_ids
            elif m["resource_type"] == "docdb":
                repo = "target-docdb-module"  # todo repo, branch hardcoded for now
                branch = "main"
                private_subnets_ids = f"module.{network_module_name}.private_subnets"
                m["private_subnets_ids"] = private_subnets_ids

            if "shared_terraform_module" in m and m["shared_terraform_module"]:
                resource_terraform_dir = (
                    f"{terraform_dir}/{m['shared_terraform_module_name']}"
                )
            else:
                resource_terraform_dir = f"{terraform_dir}/{m['name']}"

            m["security_groups"] = ecs_security_groups

            block_options = m  # todo: move to a separate dict

            process_resource_module(
                dest_dir=resource_terraform_dir,
                terraform_options=block_options,
                repo=repo,
                repo_branch=branch,
                debug=debug,
            )
            updated_config["blocks"].append(m)

    for m in config["blocks"]:
        if m["type"] == "api-gateway":
            repo, branch = parse_module_target(m["target"])
            resource_terraform_dir = f"{terraform_dir}/{m['name']}"
            subnets = f"module.{network_module_name}.public_subnets"
            m["subnets"] = subnets
            block_options = m  # todo: move to a separate dict

            process_api_gateway_module(
                dest_dir=resource_terraform_dir,
                terraform_options=block_options,
                repo=repo,
                repo_branch=branch,
                debug=debug,
            )
            updated_config["blocks"].append(m)

        if m["type"] == "sqs":
            repo, branch = parse_module_target(m["target"])
            resource_terraform_dir = f"{terraform_dir}/{m['name']}"
            block_options = m  # todo: move to a separate dict

            process_sqs_module(
                dest_dir=resource_terraform_dir,
                terraform_options=block_options,
                repo=repo,
                repo_branch=branch,
                debug=debug,
            )
            updated_config["blocks"].append(m)
        if m["type"] == "s3":
            repo, branch = parse_module_target(m["target"])
            resource_terraform_dir = f"{terraform_dir}/{m['name']}"
            block_options = m  # todo: move to a separate dict
            process_s3_module(
                dest_dir=resource_terraform_dir,
                terraform_options=block_options,
                repo=repo,
                repo_branch=branch,
                debug=debug,
            )
            updated_config["blocks"].append(m)

    # process root level terraform templates
    main_tf_options = config
    main_tf_options["network_module_name"] = network_module_name
    main_tf_options["block_secrets"] = block_secrets

    print(f"main_tf_options: {main_tf_options}")
    process_tf_templates(
        dest_dir=terraform_dir,
        terraform_options=main_tf_options,
        tf_templates_dir=tf_templates_dir,
        debug=debug,
    )

    process_static_files(dest_dir=terraform_dir)
    process_env_file(dest_dir=terraform_dir, env_id=environment_id)
    if "override_repo" in config:
        process_terraform_overrides(
            dest_dir=terraform_dir,
            override_repo_name=config["override_repo"]["repo_name"],
            override_repo_username=config["override_repo"]["repo_username"],
            override_repo_password=config["override_repo"]["repo_password"],
            override_repo_region=config["override_repo"]["repo_region"],
            override_repo_branch=config["override_repo"].get("repo_branch", None),
        )

    # zip generated terraform project
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        name = "terraform"
        extension = "zip"

        # it's important to not change current dir in lambda otherwise it will blow up on the next request
        current_dir = os.getcwd()
        try:
            os.chdir(terraform_dir)
            shutil.make_archive(
                base_name=f"{tmp_dir_name}/{name}",
                format=extension,
                root_dir=terraform_dir,
            )
            # shutil.move(f"{current_dir}/{name}.{extension}", tmp_dir_name)
        finally:
            os.chdir(current_dir)

        with open(f"{tmp_dir_name}/{name}.{extension}", "rb") as terraform_zip:
            zip = terraform_zip.read()
            encoded_zip = base64.encodebytes(zip)
            return {
                "statusCode": 200,
                "body": encoded_zip,
            }
