
locals {
  alb_name                       = "{{ alb_name }}"
  lb_sg_name                     = "{{ alb_name }}-sg"
  internal                       = {{ internal | lower }}
  subnet_ids                     = local.internal ? var.private_subnets : var.public_subnets
  lb_port                        = "80"
  lb_protocol                    = "HTTP"
  lb_ssl_protocol                = "HTTPS"
  lb_ssl_port                    = "443"
  deregistration_delay           = "30"
  health_check_enabled           = true
  health_check                   = "/"
  health_check_matcher           = "200-499"
  health_check_interval          = "30"
  health_check_timeout           = "30"
  lb_access_logs_expiration_days = "7"
  lb_ssl_certificate_arn         = null
  dggr_acm_certificate_arn       = null
  vpc_id                         = data.aws_vpc.vpc.id
}

resource "aws_security_group" "lb_sg" {
  name        = local.lb_sg_name
  description = "Allow connections from external resources."
  vpc_id      = local.vpc_id

  tags = var.tags
}

resource "aws_security_group_rule" "lb_ingress_rule" {
  description       = "Connection to ALB"
  type              = "ingress"
  from_port         = local.lb_port
  to_port           = local.lb_port
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.lb_sg.id
}

resource "aws_security_group_rule" "lb_egress_rule" {
  description       = "Connection from ALB"
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = -1
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.lb_sg.id
}


resource "aws_alb" "main" {
  name = local.alb_name

  # launch lbs in public or private subnets based on "internal" variable
  internal        = local.internal
  subnets         = local.subnet_ids
  security_groups = [aws_security_group.lb_sg.id]
  tags            = var.tags

  # enable access logs in order to get support from aws
  access_logs {
    enabled = true
    bucket  = aws_s3_bucket.lb_access_logs.bucket
  }
}

data "aws_elb_service_account" "main" {
}

# bucket for storing ALB access logs
resource "aws_s3_bucket" "lb_access_logs" {
  bucket_prefix = local.alb_name
  tags          = var.tags
  force_destroy = true
}

resource "aws_s3_bucket_acl" "lb_access_logs_acl" {
  bucket = aws_s3_bucket.lb_access_logs.id
  acl    = "private"
}

resource "aws_s3_bucket_lifecycle_configuration" "lb_access_logs_lifecycle_rule" {
  bucket = aws_s3_bucket.lb_access_logs.id

  rule {
    id     = "cleanup"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
    expiration {
      days = local.lb_access_logs_expiration_days
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lb_access_logs_server_side_encryption" {
  bucket = aws_s3_bucket.lb_access_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}


# give load balancing service access to the bucket
resource "aws_s3_bucket_policy" "lb_access_logs" {
  bucket = aws_s3_bucket.lb_access_logs.id

  policy = <<POLICY
{
  "Id": "Policy",
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:PutObject"
      ],
      "Effect": "Allow",
      "Resource": [
        "${aws_s3_bucket.lb_access_logs.arn}",
        "${aws_s3_bucket.lb_access_logs.arn}/*"
      ],
      "Principal": {
        "AWS": [ "${data.aws_elb_service_account.main.arn}" ]
      }
    }
  ]
}
POLICY
}


# adds an http listener to the load balancer and allows ingress
# (delete this file if you only want https)

resource "aws_alb_listener" "http" {
  load_balancer_arn = aws_alb.main.id
  port              = local.lb_port
  protocol          = local.lb_protocol

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "OK"
      status_code  = "200"
    }
  }

  lifecycle {
    ignore_changes = [port, protocol, default_action]
  }
}

/*
resource "aws_lb_listener" "https" {
  count = (local.lb_ssl_certificate_arn==null && local.dggr_acm_certificate_arn==null) ? 0 : 1
  load_balancer_arn = aws_alb.main.arn
  port              = local.lb_ssl_port
  protocol          = local.lb_ssl_protocol
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = local.lb_ssl_certificate_arn==null ? local.dggr_acm_certificate_arn : local.lb_ssl_certificate_arn
  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "OK"
      status_code  = "200"
    }
  }
}


resource "aws_lb_listener_certificate" "lb_listener_cert" {
   count = (local.lb_ssl_certificate_arn==null && local.dggr_acm_certificate_arn==null) ? 0 : 1
   listener_arn = aws_lb_listener.https[0].arn
   certificate_arn   = local.lb_ssl_certificate_arn==null ? local.dggr_acm_certificate_arn : local.lb_ssl_certificate_arn
}
*/
# The load balancer DNS name
output "lb_dns" {
  value = aws_alb.main.dns_name
}

output "lb_arn" {
  value = aws_alb.main.arn
}

output "lb_http_listener_arn" {
  value = try(aws_alb_listener.http.arn, null)
}

/*
output "lb_https_listener_arn" {
  value = try(aws_lb_listener.https[0].arn, null)
}
*/
output "lb_zone_id" {
  value = aws_alb.main.zone_id
}