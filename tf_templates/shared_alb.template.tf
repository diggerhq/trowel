
locals {
  alb_name                       = var.shared_alb_name
  lb_sg_name                     = "${var.shared_alb_name}-sg"
  internal                       = {{ internal | lower }}
  subnet_ids                     = module.{{ network_module_name }}.private_subnets
  lb_port                        = var.shared_alb_port
  lb_protocol                    = var.shared_alb_protocol
  lb_ssl_protocol                = var.shared_alb_ssl_protocol
  lb_ssl_port                    = var.shared_alb_ssl_port
  deregistration_delay           = var.shared_alb_deregistration_delay
  health_check_enabled           = var.shared_alb_health_check_enabled
  health_check                   = var.shared_alb_health_check
  health_check_matcher           = var.shared_alb_health_check_matcher
  health_check_interval          = var.shared_alb_health_check_interval
  health_check_timeout           = var.shared_alb_health_check_timeout
  lb_access_logs_expiration_days = var.shared_alb_access_logs_expiration_days
  lb_ssl_certificate_arn         = null
  dggr_acm_certificate_arn       = null
  vpc_id                         = module.{{ network_module_name }}.vpc_id
  alb_zone_id                     = aws_alb.shared_alb.zone_id
  //alb_https_listener_arn          =try(aws_lb_listener.https[0].arn, null)
  alb_http_listener_arn           =try(aws_alb_listener.http.arn, null)
  alb_arn                         =aws_alb.shared_alb.arn
  alb_dns                         =aws_alb.shared_alb.dns_name
  listener_arn                    =aws_alb_listener.http.arn
}

resource "aws_security_group" "shared_lb_sg" {
  name        = local.lb_sg_name
  description = "Allow connections from external resources."
  vpc_id      = local.vpc_id
  tags = {{ tags }}
}

resource "aws_security_group_rule" "lb_ingress_rule" {
  description       = "Connection to ALB"
  type              = "ingress"
  from_port         = local.lb_port
  to_port           = local.lb_port
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.shared_lb_sg.id
}

resource "aws_security_group_rule" "lb_egress_rule" {
  description       = "Connection from ALB"
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = -1
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.shared_lb_sg.id
}


resource "aws_alb" "shared_alb" {
  name = local.alb_name

  # launch lbs in public or private subnets based on "internal" variable
  internal        = {{ internal | lower }}
  subnets         = module.{{ network_module_name }}.private_subnets
  security_groups = [aws_security_group.shared_lb_sg.id]
  tags            = {{ tags }}

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
  force_destroy = true
  tags          = {{ tags }}
}

resource "aws_s3_bucket_ownership_controls" "lb_access_logs_ownership_controls" {
  bucket = aws_s3_bucket.lb_access_logs.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "lb_access_logs_acl" {
  depends_on = [aws_s3_bucket_ownership_controls.lb_access_logs_ownership_controls]

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
  load_balancer_arn = aws_alb.shared_alb.id
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
  tags          = {{ tags }}
}

resource "aws_alb_listener" "https" {
  count = (local.lb_ssl_certificate_arn==null && local.dggr_acm_certificate_arn==null) ? 0 : 1
  load_balancer_arn = aws_alb.shared_alb.arn
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
  tags          = {{ tags }}
}

/*
resource "aws_alb_listener_certificate" "lb_listener_cert" {
   count = (local.lb_ssl_certificate_arn==null && local.dggr_acm_certificate_arn==null) ? 0 : 1
   listener_arn = aws_lb_listener.https[0].arn
   certificate_arn   = local.lb_ssl_certificate_arn==null ? local.dggr_acm_certificate_arn : local.lb_ssl_certificate_arn
}
*/

# The load balancer DNS name
output "alb_dns" {
  value = local.alb_dns
}

output "alb_arn" {
  value = local.alb_arn
}

output "alb_http_listener_arn" {
  value = local.alb_http_listener_arn
}

/*
output "alb_https_listener_arn" {
  value = local.alb_https_listener_arn
}
*/

output "alb_zone_id" {
  value = local.alb_zone_id
}