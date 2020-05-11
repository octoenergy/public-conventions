# Terraform

Terraform is a really powerful tool with a lot of freedom in the way you use it.
It isn't a very opinionated tool, however if you don't stick with rules it can
easily get complicated and hard to maintain.

This is why we decided to write our own guideline on how to structure a
`terraform` codebase.

## Patterns

## Name files after the resource they manage

Files should be named with the AWS (or other cloud provider) components they are
referring to. Keeping this open to future needs, if a component is getting more
in use than others we can make the filename more specific.
The idea is to keep a balance between too many small files and too few huge
files.

```
/my-projet/
├─ modules/
│   └─ database/
│       ├─ ec2.tf
│       ├─ cloudwatch.tf
│       ├─ outputs.tf
│       ├─ rds.tf
│       └─ variables.tf
└─ workspaces/
   └─ someclient-prod/
        ├─ backend.tf      # To set the backend instruction of terraform
        ├─ cloudflare.tf
        ├─ config.tf       # To set provider(s), required terraform version, ...
        ├─ ec2_api.tf      # Subset of EC2 for API related resources.
        ├─ ec2_worker.tf   # Subset of EC2 for workers related resources.
        ├─ rds.tf
        ├─ keypair.tf
        ├─ iam.tf
        ├─ variables.tf
        └─ outputs.tf
```

__As filenames doesn't matter for terraform, we can easily refactor them
overtime.__

### Allow callers to add security group ingress rules

When a service needs to access a database of any kind (i.e. PostgreSQL, RabbitMQ,
...), the database security group needs to be open from the service so the
communication can be established.

The idea is to use the composability principale to compose the database security
group (and the client if we also want to restrict outbound rules).
Let's assume you have 2 modules, a module to create a database and a module that
needs to connect to the database.

1. The database module needs to create a security group that the database users
and expose its ID as a module output.
2. The connecting module needs to accept the database security group ID as a
variable so it can create all the appropriate aws_security_group_rule resouces
to grant itself access.

__Note, don't use `ingress` or `egress` attributes as they don't work together
([here](https://www.terraform.io/docs/providers/aws/r/security_group_rule.html)
for more details) with `aws_security_group_rule` resources.__

```hcl
# file: module/database/ec2.tf

resource "aws_security_group" "rds" {
  name_prefix = "my-db-"
  # ...
}

resource "aws_security_group_rule" "rds_outbound_to_all" {
  security_group_id = aws_security_group.rds.id
  type              = "egress"

  from_port   = -1
  to_port     = -1
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}
```

```hcl
# file: module/database/outputs.tf

output "security_group_id" {
  value = aws_security_group.rds.id
}
```

```hcl
# file: rds.tf
module "my_database" {
  source = "module/database"
}
```

```hcl
# file: ec2.tf
module "my_service" {
  source = "module/service"

  database_security_group_id = module.my_database.security_group_id
}
```

```hcl
# file: module/service/ec2.tf
resource "aws_security_group_rule "rds_inbound_from_service" {
  security_group_id = var.database_security_group_id
  type              = "ingress"

  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.service.id
}
```
