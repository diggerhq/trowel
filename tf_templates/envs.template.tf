locals {
{% for block in blocks %}
  {% if 'environment_variables' in block and block.environment_variables | length > 0 %}
    {{ block.name | underscorify }}_envs = {{ block.environment_variables }}
  {% endif %}
{% endfor %}
}



