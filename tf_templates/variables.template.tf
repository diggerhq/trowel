variable "hosted_zone_name" {}
variable "aws_region" {}

{% if shared_alb is defined and shared_alb %}
  variable "shared_alb_name" {}
{% endif %}