{% if api_gateway is defined and api_gateway %}

resource "aws_api_gateway_rest_api" "{{api_gateway_name}}_rest_api" {
  name = "{{api_gateway_name}}"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "{{api_gateway_name}}_resource" {
  rest_api_id = aws_api_gateway_rest_api.{{api_gateway_name}}_rest_api.id
  parent_id   = aws_api_gateway_rest_api.{{api_gateway_name}}_rest_api.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "{{api_gateway_name}}_method" {
  rest_api_id   = aws_api_gateway_rest_api.{{api_gateway_name}}_rest_api.id
  resource_id   = aws_api_gateway_resource.{{api_gateway_name}}_resource.id
  http_method   = "ANY"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_integration" "{{api_gateway_name}}_integration" {
  rest_api_id          = aws_api_gateway_rest_api.{{api_gateway_name}}_rest_api.id
  resource_id          = aws_api_gateway_resource.{{api_gateway_name}}_resource.id
  http_method          = aws_api_gateway_method.{{api_gateway_name}}_method.http_method
  type                 = "HTTP_PROXY"
  timeout_milliseconds = 29000

  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.{{api_gateway_name}}_vpc_link.id
  integration_http_method = "ANY"
  uri                     = "http://${aws_lb.{{api_gateway_name}}_nlb.dns_name}/{proxy}"

  request_parameters = {
    "integration.request.path.proxy" = "method.request.path.proxy"
  }

  cache_key_parameters = [
    "method.request.path.proxy",
  ]
}

resource "aws_api_gateway_deployment" "{{api_gateway_name}}_deployment" {
  rest_api_id = aws_api_gateway_rest_api.{{api_gateway_name}}_rest_api.id
  depends_on = [
    aws_api_gateway_rest_api.{{api_gateway_name}}_rest_api
  ]
  triggers = {
   #force redeployment on each apply
   redeployment = sha1(timestamp())
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "{{api_gateway_name}}_stage" {
  rest_api_id   = aws_api_gateway_rest_api.{{api_gateway_name}}_rest_api.id
  deployment_id = aws_api_gateway_deployment.{{api_gateway_name}}_deployment.id
  stage_name    = "default"
  variables = {
    "vpcLinkId" : aws_api_gateway_vpc_link.{{api_gateway_name}}_vpc_link.id
  }
  tags = var.tags
}

# Create NLB
resource "aws_lb" "{{api_gateway_name}}_nlb" {
  name               = "{{api_gateway_name}}-nlb"
  internal           = true
  load_balancer_type = "network"
  subnets            = module.oc-vpc.public_subnets
  tags               = var.tags
}

# Create NLB target group that forwards traffic to alb
# https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_CreateTargetGroup.html
resource "aws_lb_target_group" "{{api_gateway_name}}_tg" {
  name        = "{{api_gateway_name}}-tg"
  port        = 80
  protocol    = "TCP"
  vpc_id      = module.oc-vpc.vpc_id
  target_type = "alb"
  tags        = var.tags
}

# Create target group attachment
# More details: https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_TargetDescription.html
# https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_RegisterTargets.html
resource "aws_lb_target_group_attachment" "{{api_gateway_name}}_tga" {
  target_group_arn = aws_lb_target_group.{{api_gateway_name}}_tg.arn
  # target to attach to this target group
  target_id = aws_alb.shared_alb.id
  #  If the target type is alb, the targeted Application Load Balancer must have at least one listener whose port matches the target group port.
  port = 80
}


resource "aws_lb_listener" "{{api_gateway_name}}_lb_listener" {
  load_balancer_arn = aws_lb.{{api_gateway_name}}_nlb.arn
  port              = "80"
  protocol          = "TCP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.{{api_gateway_name}}_tg.arn
  }
  tags = var.tags

}

# create vpc link
resource "aws_api_gateway_vpc_link" "{{api_gateway_name}}_vpc_link" {
  name        = "{{api_gateway_name}}_vpc_link"
  target_arns = [aws_lb.{{api_gateway_name}}_nlb.arn]
}



{% endif %}