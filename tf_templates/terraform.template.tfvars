
hosted_zone_name = "{{ hosted_zone_name }}"
aws_region = "{{ aws_region }}"

{% if shared_alb is defined and shared_alb %}
  shared_alb_name = "{{ shared_alb_name }}"
{% endif %}