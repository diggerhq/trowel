{% for s in secret_keys %}
resource "aws_ssm_parameter" "{{ s | lower }}" {
  name        = "/{{ environment_id }}/{{ s | lower }}"
  description = "{{ s }}"
  type        = "SecureString"
  value       = "REPLACE_ME"
  lifecycle {
    ignore_changes = [value]
  }
}
{% endfor %}

{% if secret_keys is defined %}
locals {
  secrets = [
        {% for s in secret_keys %}
{
"key" : "{{ s }}"
"value": aws_ssm_parameter.{{s | lower}}.arn
},
        {% endfor %}

  ]
}
{% endif %}
