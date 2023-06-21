locals {
{% for block in blocks %}
  {% if 'secrets' in block and block.secrets | length > 0 %}
    {{ block.name | underscorify }}_secrets = [
            {% for s, v in block.secrets.items() %}
    {
    "key" : "{{ s }}"
    "value": {{ v }}
    },
            {% endfor %}
      ]
  {% endif %}
{% endfor %}
}




