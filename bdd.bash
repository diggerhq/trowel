# Runs terraform-compliance tests for given json payload
#
# Example: ./bdd.bash test_configs/mytest.json
#
# It will execute tests from features/mytest.json/ directory.

usage() {
    echo "Usage: ./bdd.bash file_with_payload.json";
    exit 1;
}

die() {
    echo "Fatal error: $1"
    exit;
}

[ -z "$1" ] && usage;

payload_file="$1"

[ -f "$payload_file" ] || die "File $payload_file not found";

features_dir="features/$(basename $1)"

[ -d "$features_dir" ] || die "Directory $features_dir not found";

rm -rf tf
set -x
poetry run python run_lambda.py "$payload_file" tf

cd tf
terraform init
terraform plan -out=plan.out

cd ..
poetry run terraform-compliance -p tf/plan.out -f "$features_dir"
