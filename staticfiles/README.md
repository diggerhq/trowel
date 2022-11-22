
![](digger-takes-care.png)

# What is this?

These are the terraform files that define your infrastructure. It was generated using [digger](https://digger.dev). These configurations files will
help you set up your environment on AWS in no time!

# How to run it?

## Prerequisites

You need to have the following tools installed on your machine or CI system to run these commands:

- [AWS cli](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) - for configuring access to AWS
- [terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) - for configuring terraform
- [dgctl](https://diggerhq.gitbook.io/trowel-docs/) - optinal, for configuring your remote terraform state


## On your machine

### Configuring S3 backend (Optional)

In order to work with teams it is important to use a remote backend location to store your terraform state. If you do not do this terraform will use local file system as a backend - this only works if you are the only one on the team and its not a critical infrastructure. In order to configure a backend state we provide a convinience wrapper tool to generate the necessary terraform configuration. To configure it you simply run:

```
dgctl init
```

You will be asked to enter a region after which the tool will create an S3 bucket in your account and generate a `backend.tf` file. Note that you need to have aws cli configured to point to the right aws account.

### Generating infrastructure

In the first step initialize your infrastructure and generate a plan to see what will be created:

```
terraform init
terraform plan
```

Finally, to create infrastructure run:

```
terraform apply
```

To destroy all infrastructure terraform created, run:

```
terraform destroy
```

More details and options can be found in terraform documentation: https://registry.terraform.io/providers/hashicorp/aws/latest/docs


### Updating the required secrets

- Go to AWS Parameter store (https://us-east-1.console.aws.amazon.com/systems-manager/parameters/?region=us-east-1&tab=Table) - make sure you are in the right region where you deployed your stack
- You will find a list of secrets there. If your stack has a database you will be able to retrieve the connection credentials there
- For every secret that your application depends on you will find a parameter store entry, you need to set it to the right value for your application

### Deploying from local machine

In the terraform apply step you should have seen outputs, search for the "docker_registry_url" and keep note of it. it will look like this "AWS_ACCOUNT_ID.dkr.ecr.AWS_REGION.amazonaws.com/ECR_REPO" - keep note of the values for AWS_REGION and ECR_REPO. You then need to run these commands within your code repository (it should contain a dockerfile to be built and pushed).

```
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query "Account" --output text)" 
export AWS_REGION=<<<YOURREGION>>>
export ECR_REPO=<<<YOURREPO>>>
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO .
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
```

If everything has been run corectly this will then it should deploy from that branch in a few minutes. In order to trigger another deployment you re-push the image again and finally run the following command to force a new deployment (this command is not necessary the first time):

```
aws ecs update-service --cluster <<CLUSTER_NAME>> --service <<SERVICE_NAME>> --force-new-deployment
```

Where you can find the values for CLUSTER_NAME and SERVICE_NAME in `main.tf` file.

# Miscelleneous

## Configuring your AWS cli

If aws haven't been configured locally, the simplest option is to run the following command to configure it:

```
$ aws configure
```

If you have multiple local profiles you can set which profile to run from by exporing an environment variable:

```
$ export AWS_PROFILE=digger-test2
```

Where `digger-test2` is the name of the AWS profile

