
Functions to generate ECS Task policies:
```python
def generate_ecs_task_execution_policy(
    path, s3_bucket_arn_list, ssm_list, sqs_arn_list
)
    
def generate_ecs_task_policy(path, use_ssm=False)
```

Run terraform fmt command in specified dir
```python
def terraform_format(path=".")
```

Render templates (borrowed from Digger)
```python
def render_jinja_template(
    terraform_options, input_file, output_file, delete_original=False
)
```

main function that clone module, render jinja templates and inject parameters:
```python
def process(dest_dir, repo, repo_branch, module_name, templates, terraform_options)
```

example:
```python
repo = "git@github.com:diggerhq/target-network-module.git"
repo_branch = "main"
# destination dir
dest_dir="/tmp/tf-gen"
# rendered module dir name
module_name = "target-network-module-tmp"
# templates in the module
templates = [("/vpc.template.tf", "/vpc.tf")]
terraform_options = {"enable_vpc_endpoints": True}

process(dest_dir, repo, repo_branch, module_name, templates, terraform_options)
```