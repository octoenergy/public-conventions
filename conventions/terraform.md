# Terraform

Terraform is a really powerful tool with a lot of freedom in the way you use it.
It isn't a very opinionated tool, however if you don't stick with rules it can
easily get complicated and hard to maintain.

This is why we decided to write our own guideline on how to structure a
`terraform` codebase.

Contents:

- [Name files after the resource they manage](#resource-naming)
- [Allow callers to add security group ingress rules](#ingress-rules)

## <a name="resource-naming">Name files after the resource they manage</a>

Files should be named after the AWS (or other cloud provider) components they
manage (e.g. `ec2.tf`). If the file for a particular component gets large, then
add a suffix to distinguish between different groups of component (e.g.
`ec2_api.tf`).

The idea is to keep a balance between too many small files and too few huge
files.

```
/my-project/
├─ modules/
│   └─ database/
│       ├─ ec2.tf
│       ├─ cloudwatch.tf
│       ├─ outputs.tf
│       ├─ rds.tf
│       └─ variables.tf
└─ workspaces/
    └─ someclient-prod/
        ├─ acm.tf
        ├─ backend.tf      # To set the backend instruction of Terraform
        ├─ config.tf       # To set provider(s), required Terraform version, ...
        ├─ route53.tf
        ├─ main.tf         # Where modules are imported
        └─ variables.tf
```

As filenames doesn't matter for Terraform, we can easily refactor them overtime.

## <a name="ingress-rules">Allow callers to add security group ingress rules</a>

When a component in one module needs to connect to a component in another module
(e.g. an application server needs to connect to PostgreSQL), the security group
in the server module needs to allow packets from the client module. There's
several ways of handling this in Terraform but prefer the following approach.

1. Expose the security group ID from server module as an output.
2. Inject this security group ID into client modules that want to connect to the
   components in the server module.
3. In each client module, add ingress rules to the server security group to
   enable client resources to connect to the server.

For example, support we have a "database" module that a "services" module needs
to connect to. First create and export an `aws_security_group` that an RDS
instance uses:

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

resource "aws_db_instance" "default" {
  vpc_security_group_ids = [aws_security_group.rds.id]
  # ...
}

# file module/database/outputs.tf
output "rds_security_group_id" {
  value = aws_security_group.rds.id
}
```

then inject this security group ID into the services module:

```hcl
# file: module/service/variables.tf
variable "database_security_group_id" {}

# file: main.tf
module "my_database" {
  source = "module/database"
}

module "my_service" {
  source = "module/service"

  database_security_group_id = module.my_database.rds_security_group_id
}
```

and, in the services module, add the `aws_security_group_rule` rules that allows
resources to connect to the database:

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

Note: don't use `ingress` or `egress` attributes on the exported
`aws_security_group` resource as they don't work together with separate
`aws_security_group_rule` resources (see the
[Terraform docs](https://www.terraform.io/docs/providers/aws/r/security_group_rule.html))

The advantage of this approach is it allows many calling modules to connect to a
particular "server" resource without having to modify the server's module for
each new caller.

A similar technique is possible using an exported "client" security group that
is given to each calling resource. This is an elegant approach but is limited by
the max number (5) of security groups that an EC2 instance can have.
