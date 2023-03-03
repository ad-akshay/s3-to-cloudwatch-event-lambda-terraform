# Create the Lambda function deployment package
data "archive_file" "lambda_function_zip" {
  type        = "zip"
  source_dir  = "lambda_event_s3_to_cloudwatch"
  output_path = "lambda_function.zip"
}


# Create a Lambda function
resource "aws_lambda_function" "lambda_function" {
  filename      = "lambda_function.zip"
  function_name = "S3ToCloudwatchGroup"
  role          = aws_iam_role.lambda_function_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  timeout       = 900
  memory_size   = 1024
  environment {
    variables = {
      CWLogGroup = var.destination_cloudwatch_log_group
    }
  }
}

data "aws_caller_identity" "current"{}


data "aws_iam_policy_document" "lambda_execution_cw_s3_access"{
  statement {
    actions = [
      "logs:CreateLogGroup"
    ]
    resources = ["arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"]
  }
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [ "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*" ]
  }
  statement {
    actions = [
      "s3:*Object*"
    ]
    resources = [
     "${data.aws_s3_bucket.source_bucket.arn}/*",
    ]
  }

}


resource "aws_iam_policy" "lambda_execution_s3_cw_policy" {
  name   = "lambda-s3-to-cw-access-policy"
  description = "Provide S3 and Cloudwatch access to Lambda to transfer data"
  path   = "/"
  policy = data.aws_iam_policy_document.lambda_execution_cw_s3_access.json
}


# Create an IAM role for the Lambda function
resource "aws_iam_role" "lambda_function_role" {
  name = "s3-to-cloudwatch-lambda-function-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}



# Role - Policy - Attachment
resource "aws_iam_role_policy_attachment" "lambda_s3_cw_role_policy_attachment" {
  role       = aws_iam_role.lambda_function_role.name
  policy_arn = aws_iam_policy.lambda_execution_s3_cw_policy.arn
}

resource "aws_cloudwatch_log_group" "cloudwatch-lg-logs-s3-data" {
  name = var.destination_cloudwatch_log_group
}

# S3 Bucket - to create notification event on
data "aws_s3_bucket" "source_bucket" {
    # bucket =  "databricks-datalake-log-${lower(var.default_tags["environment"])}"
    bucket = "ecsdemo1"
}


# Allow S3 bucket to execute lambda function
resource "aws_lambda_permission" "allow_bucket_lambda_execution" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.arn
  principal     = "s3.amazonaws.com"
  source_arn    = data.aws_s3_bucket.source_bucket.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = data.aws_s3_bucket.source_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_function.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = ""
    filter_suffix       = ".log"
  }

  depends_on = [aws_lambda_permission.allow_bucket_lambda_execution]
}
