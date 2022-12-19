{% for block in blocks %}
  output "{{ block.name}}" {
    value = module.{{ module.module_name}}
  }
{% endfor %}