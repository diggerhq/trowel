FROM public.ecr.aws/lambda/python:3.9

RUN yum install -y yum-utils
RUN yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo

RUN yum install -y terraform
RUN yum install -y git

RUN git --version
RUN terraform -v

COPY *.py ${LAMBDA_TASK_ROOT}/
COPY *.tf ${LAMBDA_TASK_ROOT}/
COPY staticfiles ${LAMBDA_TASK_ROOT}/staticfiles
COPY requirements.txt ${LAMBDA_TASK_ROOT}

WORKDIR ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

RUN mkdir ~/.ssh
RUN ssh-keyscan github.com >> ~/.ssh/known_hosts

CMD [ "handler.generate_terraform" ]

