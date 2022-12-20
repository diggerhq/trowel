rm -rf tf
python run_lambda.py test_configs/digger.json tf

cd tf
terraform init
terraform plan -out=plan.out

cd ..
poetry run terraform-compliance -p tf/plan.out -f features
