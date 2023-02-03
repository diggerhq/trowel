{% for block in blocks %}
  output "{{ block.name}}_{{block.region}}" {
    value = module.{{ block.name}}_{{block.region}}
  }
{% endfor %}