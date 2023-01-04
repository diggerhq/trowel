

{% if secret_keys is defined %}
locals {
{% for block_name, block_secrets in block_secret_keys.items() %}

{{ block_name | underscorify }}_secrets = [
        {% for s, v in block_secrets.items() %}
{
"key" : "{{ s }}"
"value": "{{ secret_keys[v] }}"
},
        {% endfor %}
  ]
        {% endfor %}
}
{% endif %}



