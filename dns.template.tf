{% for addon in addons  %}
  {% if addon.type == "routing" %}
    data "aws_route53_zone" "route53_zone" {
      name         = "{{ addon.domain_name }}"
      private_zone = false
    }

    {% for routing in addon.routings %}
      resource "aws_route53_record" "{{ addon.block_name }}_{{ routing.region }}_cname_record" {
        zone_id = data.aws_route53_zone.route53_zone.id
        {% if routing.subdomain %}
          name    = "{{ routing.subdomain }}.{{ addon.domain_name }}"
        {% else %}
          name    = "{{ addon.domain_name }}"
        {% endif %}
        type    = "A"
        alias {
            name                   = module.{{ addon.block_name }}_{{routing.region}}.lb_dns
            zone_id                = module.{{ addon.block_name }}_{{routing.region}}.lb_zone_id
            evaluate_target_health = false
        }
        {% if routing.routing_type == 'latency' %}
        set_identifier = "Latency policy for {{ routing.region }}"
        latency_routing_policy {
          region = "{{ routing.region }}"
        }
        {% endif %}
      }

      resource "aws_acm_certificate" "{{ addon.block_name }}_{{ routing.region }}_acm_certificate" {
        {% if routing.subdomain %}
          domain_name    = "{{ routing.subdomain }}.{{ addon.domain_name }}"
        {% else %}
          domain_name    = "{{ addon.domain_name }}"
        {% endif %}
        validation_method = "DNS"
      }

      resource "aws_route53_record" "{{ addon.block_name }}_{{ routing.region }}_cert_validation_record" {
        for_each = {
          for dvo in aws_acm_certificate.{{ addon.block_name }}_{{ routing.region }}_acm_certificate.domain_validation_options : dvo.domain_name => {
            name   = dvo.resource_record_name
            record = dvo.resource_record_value
            type   = dvo.resource_record_type
          }
        }

        allow_overwrite = true
        name            = each.value.name
        records         = [each.value.record]
        ttl             = 60
        type            = each.value.type
        zone_id         = data.aws_route53_zone.route53_zone.zone_id
      }

      resource "aws_acm_certificate_validation" "{{ addon.block_name }}_{{ routing.region }}_acm_cert_validation" {
        certificate_arn         = aws_acm_certificate.{{ addon.block_name }}_{{ routing.region }}_acm_certificate.arn
        validation_record_fqdns = [for record in aws_route53_record.{{ addon.block_name }}_{{ routing.region }}_cert_validation_record : record.fqdn]
      }
    {% endfor %}
  {% endif %}
{% endfor %}