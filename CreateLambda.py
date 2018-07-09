#! C:\Python36\python.exe

#
# Sample code to create AWS Lambda function and API Gateway REST interface using AWS CloudFormation
#
# Before running the script:
#   -- The AWS command-line utility must be installed and configured. The script uses the configured user's
#           credentials to create the AWS resources. All resources are created in the user's configured default
#           region. You do not need to be logged into AWS to run the script.
#   -- The repository's test.py file must be manually zipped into a test.zip file located in the current directory.
#
#  The script creates three CloudFormation stacks.
#   -- BootstrapS3Bucket: This stack is defined by a CloudFormation template file defined in the script. Creates a
#           bootstrap S3 bucket. The repository's CreateS3Bucket.yaml file is copied to the bucket to initialize the
#           rest of the operation.
#   -- LambdaS3Bucket: Stack created by the repository's CreateS3Bucket.yaml CloudFormation template file, which
#           creates another S3 bucket to store the Lambda source code file test.py/test.zip. The script copies the
#           zip file to the bucket before creating the next stack.
#   -- LambdaFunction: Stack created by the repository's CreateLambdaFunction.yaml template file, which creates a
#           Lambda function using the code defined in test.py/test.zip. Also creates a REST interface to the function
#           using AWS API Gateway. All required roles, policies, and permissions are also created.
#
# After running the script:
#   -- Refer to the instructions in the repositories README.md file to call the Lambda function using the REST API.
#   -- To delete the CloudFormation stacks and associated AWS resources, run the script with the -d or --delete
#           argument.

########################################
# Imports

import argparse                         # For command-line argument parsing
import boto3 as aws
from botocore.exceptions import ClientError, WaiterError

########################################
# Constants and global variables

VERSION             = 'v0.21'

# CloudFormation stack names
CF_STACKNAME_LAMBDA         = 'LambdaFunction'
CF_STACKNAME_LAMBDA_S3      = 'LambdaS3Bucket'
CF_STACKNAME_BOOTSTRAP_S3   = 'BootstrapS3Bucket'

# S3 bucket names
# Note: Bucket names are also referenced in the CF template files
CF_LAMBDA_S3_BUCKET_NAME    = 'generic-lambda-functions-01234'
CF_BOOTSTRAP_S3_BUCKET_NAME = 'generic-bootstrap-bucket-01234'

# Lambda source code
CF_LAMBDA_SOURCE    = 'test.zip'

# CloudFormation template files
CF_TEMPLATE_S3      = 'CreateS3Bucket.yaml'
CF_TEMPLATE_LAMBDA  = 'CreateLambdaFunction.yaml'
CF_TEMPLATE_BOOTSTRAP_S3    = \
'''---
Resources:
  DocS3BootstrapBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: {bucketName}
      Tags:
        - Key: "Documentation"
          Value: "Documentation"

  # Allow CF templates to perform all S3 operations on this bucket
  DocBucketAccessPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket:
        Ref: "DocS3BootstrapBucket"
      PolicyDocument:
        Statement:
          - Action: "*"
            Effect: "Allow"
            Resource:
              Fn::Join:
              - ""
              - - "arn:aws:s3:::"
                - Ref: "DocS3BootstrapBucket"
                - "/*"
            Principal:
              Service:
              - cloudformation.amazonaws.com
'''

########################################
# Create S3 bucket(s) using CloudFormation
# Copy CF template files to the buckets
#
# Note: When creating an S3 bucket from the AWS console, the CF template can be manually specified and uploaded.
# However, when creating a bucket programmatically, the template must already exist in another S3 bucket. Hence,
# it's necessary to bootstrap the operation by first creating an S3 bucket without a template, i.e. by specifying
# the bucket's properties as a string (not in a template file) and passing the string to CF in the TemplateBody
# argument.
#
# This method performs the following operations.
#   * Create a CF_BOOTSTRAP_S3_BUCKET_NAME bucket using the CF TemplateBody argument, i.e. template defined in script.
#   * Copy the CF_TEMPLATE_S3 file to the bucket.
#   * Create a CF_LAMBDA_BUCKET_NAME bucket using the CF TemplateURL argument, i.e. repository template file.
#   * Copy the CF_TEMPLATE_LAMBDA file to the bucket.


def create_s3_bucket():
    # Create a bootstrap S3 bucket specifying the template in CF TemplateBody string
    print('Creating CloudFormation stack: {stack}, S3 bucket: {bucket}...'.format(stack=CF_STACKNAME_BOOTSTRAP_S3,
                                                                                  bucket=CF_BOOTSTRAP_S3_BUCKET_NAME))
    try:
        cf = aws.client('cloudformation')
        stack = cf.create_stack(StackName=CF_STACKNAME_BOOTSTRAP_S3,
                                TemplateBody=CF_TEMPLATE_BOOTSTRAP_S3.format(bucketName=CF_BOOTSTRAP_S3_BUCKET_NAME))
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            # This short message provides the information we need
            print('ERROR: ' + e.response['Error']['Message'])
        else:
            # Unexpected error; better get the long descriptive message
            print('ERROR: ' + e)
        return -1

    # Wait for the stack creation to complete
    try:
        waiter = cf.get_waiter('stack_create_complete')
        # waiter = cf.meta.client.get_waiter('stack_create_complete')   # reference to get_waiter() if cf = aws.resource('cloudformation')
        waiter.wait(StackName=CF_STACKNAME_BOOTSTRAP_S3,
                    WaiterConfig={'Delay': 5, 'MaxAttempts': 12})
    except WaiterError as e:
        # Probably a timeout, i.e. MaxAttempts exceeded
        # Could also be that a bucket with this name already exists
        print('ERROR: ' + e)
        return -1

    # Upload CF template file to bootstrap S3 bucket
    print('Uploading {template} to {bucket} bucket...'.format(template=CF_TEMPLATE_S3,
                                                              bucket=CF_BOOTSTRAP_S3_BUCKET_NAME))
    try:
        s3 = aws.client('s3')
        s3.upload_file(CF_TEMPLATE_S3, CF_BOOTSTRAP_S3_BUCKET_NAME, CF_TEMPLATE_S3)
        #s3.upload_file(CF_TEMPLATE_LAMBDA, CF_BOOTSTRAP_S3_BUCKET_NAME, CF_TEMPLATE_LAMBDA)
    except ClientError as e:
        print('ERROR: ' + e)
        return -1

    # Create the S3 Lambda bucket using the uploaded CloudFormation template
    print('Creating CloudFormation stack: {stack}, S3 bucket: {bucket}...'.format(stack=CF_STACKNAME_LAMBDA_S3,
                                                                                  bucket=CF_LAMBDA_S3_BUCKET_NAME))
    try:
        # cf = aws.client('cloudformation')        # Reuse CF client created above
        stack = cf.create_stack(StackName=CF_STACKNAME_LAMBDA_S3,
                                TemplateURL='https://s3.amazonaws.com/{bucket}/{template}'.format(bucket=CF_BOOTSTRAP_S3_BUCKET_NAME,
                                                                                                  template=CF_TEMPLATE_S3))
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            # This short message provides the information we need
            print('ERROR: ' + e.response['Error']['Message'])
        else:
            # Unexpected error; better get the long descriptive message
            print('ERROR: ' + e)
        return -1

    # Wait for the stack creation to complete
    try:
        #waiter = cf.get_waiter('stack_create_complete')    # Reuse Waiter object created above
        waiter.wait(StackName=CF_STACKNAME_LAMBDA_S3,
                    WaiterConfig={'Delay': 5, 'MaxAttempts': 12})
    except WaiterError as e:
        # Probably a timeout, i.e. MaxAttempts exceeded
        print('ERROR: ' + e)
        return -1

    # Upload CF template file to Lambda S3 bucket
    print('Uploading {template} to {bucket} bucket...'.format(template=CF_TEMPLATE_LAMBDA,
                                                              bucket=CF_LAMBDA_S3_BUCKET_NAME))
    try:
        #s3 = aws.client('s3')       # Reuse S3 client created above
        s3.upload_file(CF_TEMPLATE_LAMBDA, CF_LAMBDA_S3_BUCKET_NAME, CF_TEMPLATE_LAMBDA)
    except ClientError as e:
        print('ERROR: ' + e)
        return -1

    # Success
    return 0

########################################
# Create AWS Lambda function and API Gateway REST interface using CloudFormation template
#
# Expects the CF_TEMPLATE_LAMBDA template file to exist in CF_LAMBDA_S3_BUCKET_NAME.
# Copies the CF_LAMBDA_SOURCE file (test.zip) containing the Lambda source code to CF_LAMBDA_S3_BUCKET_NAME.


def create_lambda():

    # Copy Lambda source file to S3 bucket
    print('Uploading {source} to {bucket} bucket...'.format(source=CF_LAMBDA_SOURCE, bucket=CF_LAMBDA_S3_BUCKET_NAME))
    try:
        s3 = aws.client('s3')
        s3.upload_file(CF_LAMBDA_SOURCE, CF_LAMBDA_S3_BUCKET_NAME, CF_LAMBDA_SOURCE)
    except ClientError as e:
        print('ERROR: ' + e)
        return -1

    # Create CF stack
    # Note: Need to specify Capabilities argument because the template creates a Lambda execution AWS::IAM::Role.
    print('Creating CloudFormation stack: {stack}...'.format(stack=CF_STACKNAME_LAMBDA))
    try:
        cf = aws.client('cloudformation')
        stack = cf.create_stack(StackName=CF_STACKNAME_LAMBDA,
                                TemplateURL='https://s3.amazonaws.com/{bucket}/{template}'.format(bucket=CF_LAMBDA_S3_BUCKET_NAME,
                                                                                                  template=CF_TEMPLATE_LAMBDA),
                                Capabilities=['CAPABILITY_IAM'])
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            # This short message provides the information we need
            print('ERROR: ' + e.response['Error']['Message'])
        else:
            # Unexpected error; better get the long descriptive message
            print('ERROR: ' + e)
        return -1

    # Wait for the stack creation to complete
    try:
        waiter = cf.get_waiter('stack_create_complete')
        # waiter = cf.meta.client.get_waiter('stack_create_complete')       # reference to get_waiter() if cf = aws.resource('cloudformation')
        waiter.wait(StackName=CF_STACKNAME_LAMBDA,
                    WaiterConfig={'Delay': 5, 'MaxAttempts': 24})
    except WaiterError as e:
        # Probably a timeout, i.e. MaxAttempts exceeded
        print('ERROR: ' + e)
        return -1

    # Success
    return 0

########################################
# Delete a specified CloudFormation stack
#
# Note: If the stack includes an S3 bucket, the bucket must be empty


def delete_cf_stack(stack_name, cf_client=None, wait_delay=5, wait_max_attempts=12, verbose=True):

    if verbose:
        print('Deleting CloudFormation stack: {}...'.format(stack_name))

    if cf_client is None:
        cf_client = aws.client('cloudformation')

    cf_client.delete_stack(StackName=stack_name)    # If stack does not exist, method returns without throwing exception
    try:
        waiter = cf_client.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stack_name,
                    WaiterConfig={'Delay': wait_delay, 'MaxAttempts': wait_max_attempts})
    except WaiterError as e:
        # Probably a timeout, i.e., MaxAttempts exceeded
        if verbose:
            print('ERROR: ' + e)
        return -1

    # Success
    return 0

########################################
# Delete each of the CloudFormation stacks created by the script

def delete_cloudformation_stacks():

    # S3 bucket must be empty before deleting it
    print('Emptying all buckets...')
    s3 = aws.client('s3')

    # Empty the bootstrap bucket
    objects = s3.list_objects_v2(Bucket=CF_BOOTSTRAP_S3_BUCKET_NAME)        # retrieve list of bucket's file objects
    if objects['KeyCount']:     # KeyCount == 0 if bucket is empty
        objDict = {'Objects': [{'Key': obj['Key']} for obj in objects['Contents']]}  # dict of list of bucket's file objects
        response = s3.delete_objects(Bucket=CF_BOOTSTRAP_S3_BUCKET_NAME, Delete=objDict)

    # Empty the lambda bucket
    objects = s3.list_objects_v2(Bucket=CF_LAMBDA_S3_BUCKET_NAME)
    if objects['KeyCount']:
        objDict = {'Objects': [{'Key': obj['Key']} for obj in objects['Contents']]}
        response = s3.delete_objects(Bucket=CF_LAMBDA_S3_BUCKET_NAME, Delete=objDict)

    # Delete the CloudFormation stacks
    cf = aws.client('cloudformation')
    if (delete_cf_stack(CF_STACKNAME_LAMBDA, cf_client=cf, wait_max_attempts=24) or
        delete_cf_stack(CF_STACKNAME_LAMBDA_S3, cf_client=cf) or
        delete_cf_stack(CF_STACKNAME_BOOTSTRAP_S3, cf_client=cf)):
            return -1

    # Success
    return 0

########################################
# Program entry point

if __name__ == '__main__':

    # Splash screen
    print('================================================')
    print('Create Lambda Function with CloudFormation', VERSION)
    print('================================================\n')

    # Process any command-line arguments
    argParser = argparse.ArgumentParser(description='CreateLambda ' + VERSION)
    argParser.add_argument('-d', '--delete', action='store_true',
                           help='delete CloudFormation stacks and associated resources')
    args = argParser.parse_args()
    delete_stacks = args.delete

    # Deleting stacks?
    if delete_stacks:
        if delete_cloudformation_stacks():
            exit(-1)
        exit(0)

    # Create S3 bucket and prepare it for the Lambda creation
    if create_s3_bucket():
        exit(-1)

    # Create Lambda function and REST API interface
    if create_lambda():
        exit(-1)

    # *** Retrieve information about the created resources
    # Get resource information about the CF Lambda stack
    cf = aws.client('cloudformation')
    # Retrieve info about all stack resources
    resources = cf.describe_stack_resources(StackName=CF_STACKNAME_LAMBDA)
    # Cycle through the returned dict of resources to identify the various resources and their logical resource
    # IDs. Alternatively, the logical resource IDs are also defined in the CF template, in which case they are already
    # known and can be specified as explicit strings. With the logical resource ID, additional detailed information
    # about the resource can be retrieved.
    # In the calls below, explicit strings from the CF template are used, but the same IDs could have been retrieved
    # by accessing the stack resources.

    # Retrieve info about the AWS::ApiGateway::RestApi resource TestRestApi (defined in CF template)
    resourceRestApi = cf.describe_stack_resource(StackName=CF_STACKNAME_LAMBDA, LogicalResourceId='TestRestApi')
    # Retrieve info about the AWS::ApiGateway::Method resource UsersGet (defined in CF template)
    resourceMethod = cf.describe_stack_resource(StackName=CF_STACKNAME_LAMBDA, LogicalResourceId='UsersGet')
    # Retrieve info about the AWS::ApiGateway::Resource UsersResource (defined in CF template)
    resourceResource = cf.describe_stack_resource(StackName=CF_STACKNAME_LAMBDA, LogicalResourceId='UsersResource')
    # Retrieve info about the AWS::ApiGateway::Deployment resource (defined in CF template)
    resourceDeploy = cf.describe_stack_resource(StackName=CF_STACKNAME_LAMBDA, LogicalResourceId='TestRestApiDeployment')

    # Get information about the stack's API Gateway resources
    ag = aws.client('apigateway')
    # Retrieve info about the REST API itself
    restApi = ag.get_rest_api(restApiId=resourceRestApi['StackResourceDetail']['PhysicalResourceId'])       # 'TestRestApi'
    # Retrieve info about the UsersGet method (defined in CF template)
    method = ag.get_method(restApiId=resourceRestApi['StackResourceDetail']['PhysicalResourceId'],          # 'TestRestApi'
                           resourceId=resourceResource['StackResourceDetail']['PhysicalResourceId'],        # 'UsersResource'
                           httpMethod='GET')    # From CF template: UsersGet.Properties.HttpMethod
    # Retrieve info about the 'UsersResource' resource (defined in CF template)
    # Retrieves info about the resource's methods. Because the resource has only a single GET method,
    # returns the same information as the ag.get_method() call above.
    resource = ag.get_resource(restApiId=resourceRestApi['StackResourceDetail']['PhysicalResourceId'],      # 'TestRestApi'
                               resourceId=resourceResource['StackResourceDetail']['PhysicalResourceId'],    # 'user'
                               embed=['methods'])
    # Retrieve info about the 'TestRestApiDeployment' deployment (defined in CF template)
    # Note: Does not include the StageName value
    deploy = ag.get_deployment(restApiId=resourceRestApi['StackResourceDetail']['PhysicalResourceId'],      # 'TestRestApi'
                               deploymentId=resourceDeploy['StackResourceDetail']['PhysicalResourceId'],    # 'TestRestApiDeployment'
                               embed=['apisummary'])
    # Retrieve information about deployment stages
    stages = ag.get_stages(restApiId=resourceRestApi['StackResourceDetail']['PhysicalResourceId'],          # 'TestRestApi'
                           deploymentId=resourceDeploy['StackResourceDetail']['PhysicalResourceId'])        # 'TestRestApiDeployment'
    # Retrieve information about the first (and only) deployment stage
    stage = ag.get_stage(restApiId=resourceRestApi['StackResourceDetail']['PhysicalResourceId'],            # 'TestRestApi'
                         stageName=stages['item'][0]['stageName'])                                          # 'v1'
    exit(0)
