
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


```bash
export AWS_PROFILE=digger-test
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query "Account" --output text)" 
AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query "Account" --output text)" 
export AWS_REGION=us-east-1
export ECR_REPO=trowel-lambda

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

aws ecr create-repository --repository-name $ECR_REPO  --image-scanning-configuration scanOnPush=true

docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO -f ./Dockerfile .
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest



```