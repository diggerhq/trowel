terraform {
  backend "s3" {
    bucket = "{{ bucket }}"
    key    = "{{ key }}"
    region = "{{ backend_region }}"
    dynamodb_table = "{{ dynamodb_table }}"
  }
}