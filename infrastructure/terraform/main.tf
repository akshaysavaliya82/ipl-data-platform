# Terraform configuration for AWS deployment
# IPL Real-Time Analytics Lakehouse Platform

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "ipl-platform-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "ap-south-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ipl-data-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ============================================
# Variables
# ============================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ipl-data-platform"
}

# ============================================
# S3 Buckets for Data Lake
# ============================================

resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-${var.environment}-data-lake"
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "bronze-lifecycle"
    status = "Enabled"
    filter {
      prefix = "bronze/"
    }
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }

  rule {
    id     = "silver-lifecycle"
    status = "Enabled"
    filter {
      prefix = "silver/"
    }
    transition {
      days          = 180
      storage_class = "STANDARD_IA"
    }
  }
}

# ============================================
# RDS PostgreSQL
# ============================================

resource "aws_db_instance" "analytics_db" {
  identifier           = "${var.project_name}-${var.environment}-db"
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = "db.t3.medium"
  allocated_storage    = 50
  max_allocated_storage = 200
  storage_encrypted    = true

  db_name  = "ipl_analytics"
  username = "ipl_admin"
  password = "CHANGE_ME_IN_PRODUCTION"

  multi_az               = var.environment == "prod"
  publicly_accessible    = false
  skip_final_snapshot    = var.environment != "prod"
  deletion_protection    = var.environment == "prod"
  backup_retention_period = 7

  tags = {
    Name = "${var.project_name}-analytics-db"
  }
}

# ============================================
# MSK (Managed Kafka)
# ============================================

resource "aws_msk_cluster" "kafka" {
  cluster_name           = "${var.project_name}-${var.environment}-kafka"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = var.environment == "prod" ? 3 : 2

  broker_node_group_info {
    instance_type = "kafka.m5.large"
    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
    client_subnets  = []  # Add your subnet IDs
    security_groups = []  # Add your security group IDs
  }

  tags = {
    Name = "${var.project_name}-kafka"
  }
}

# ============================================
# Outputs
# ============================================

output "data_lake_bucket" {
  value = aws_s3_bucket.data_lake.bucket
}

output "db_endpoint" {
  value = aws_db_instance.analytics_db.endpoint
}

output "kafka_bootstrap_brokers" {
  value = aws_msk_cluster.kafka.bootstrap_brokers_tls
}
