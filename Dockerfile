FROM public.ecr.aws/lambda/python:3.9

# recommended by aws security check
RUN yum update -y expat

RUN yum install -y yum-utils
RUN yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo

RUN yum install -y terraform
RUN yum install -y git

RUN git --version
RUN terraform -v

COPY *.py ${LAMBDA_TASK_ROOT}/
COPY tf_templates/*.tf ${LAMBDA_TASK_ROOT}/
COPY pyproject.toml ${LAMBDA_TASK_ROOT}/
COPY staticfiles ${LAMBDA_TASK_ROOT}/staticfiles

WORKDIR ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry config virtualenvs.create false --local
RUN poetry install

RUN mkdir ~/.ssh
RUN ssh-keyscan github.com >> ~/.ssh/known_hosts

CMD [ "handler.generate_terraform" ]

