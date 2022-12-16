{% for module in modules %}
  output "{{ module.module_name}}" {
    value = module.{{ module.module_name}}
  }
{% endfor %}