locals {
{% for block in blocks %}
  {% if 'secrets' in block and block.secrets | length > 0 %}
    {{ block.name | underscorify }}_secrets = {{ block.secrets }}
  {% endif %}
{% endfor %}
}



