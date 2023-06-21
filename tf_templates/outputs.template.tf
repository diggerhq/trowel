{% for block in blocks %}
  output "{{ block.name}}" {
    value = module.{{ block.name}}
  }
{% endfor %}