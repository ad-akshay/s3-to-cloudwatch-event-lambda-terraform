variable "region" {
}


variable "function_name" {
  type    = string
  default = "lambda_s3_to_cw_logs_insertion"
}

variable "destination_cloudwatch_log_group" {
  type = string
  default = "S3_cloudwatch_loggroup"
}


#--------------------------------------------------------------
# Provider definitions
#--------------------------------------------------------------
provider "aws" {
  region  = var.region
}
