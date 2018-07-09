# Create an AWS Lambda function and REST interface using CloudFormation

## Repository files

The repository contains the following files.

* `CreateLambda.py` : Python 3 script that automates the creation of the Lambda and REST API.
* `CreateS3Bucket.yaml` : CloudFormation template file. Creates an S3 bucket.
* `CreateLambdaFunction.yaml` : CloudFormation template file. Creates both a Lambda 
function and an API Gateway REST interface to it.
* `test.py` : Python 3 code that can be stored in a Lambda function.

Note: When using the repository files, do not keep the generated resources alive on AWS for
an extended time. The files create AWS S3 buckets, and bucket names must be globally unique.
Leaving the generated buckets on AWS will prevent others from creating the repository's 
resources. If you need to retain the resources, change the S3 bucket names specified 
in the CloudFormation template files and Python script to use your own unique names.  

## AWS background

This repository uses the following AWS services.

* Lambda
* API Gateway
* S3
* CloudFormation

The AWS Lambda service creates function resources. A Lambda function is executable 
source code stored in AWS. It can be written in various programming languages,
including Python, Node.js (JavaScript), Java, C#, or Go. The code can be executed
by invoking the function from either another Lambda function, an application running 
outside of AWS, or through a REST API front-end.

A Lambda function runs on an AWS server that is created and maintained by AWS--the Lambda
owner does not need to manage any aspect of the server--so Lambda functions can be used 
to implement a _serverless application_.

A Lambda function is also one way to implement a _microservice._ (Microservices can 
also be implemented as part of a web application.)

The AWS API Gateway service creates a REST API interface that can act as a front-end 
to one or more Lambda functions.

The AWS S3 service allocates disk storage on AWS. The service creates an AWS resource
called a _bucket,_ which is analogous to a folder on a disk drive.

The AWS CloudFormation service automates the creation of AWS resources. The
desired resources are defined in a _template file_ using JSON or YAML syntax.
The template file is submitted to CloudFormation which generates the specified 
resources. The group of generated resources is called a _stack._ CloudFormation 
can be used to create nearly any type of AWS resource, not just the types used 
in this repository.

There are several tools and methods available to create Lambda functions, REST 
interfaces, S3 buckets, and other AWS resources.

* Manually create and configure the resources using the browser-based AWS Console.
* Create a stack of resources by submitting a template file to AWS CloudFormation. The
template file can be submitted using either the AWS Console or the AWS CLI
(Command-Line Interface).
* Run a Python script to generate the desired resources.

Creating resources manually from the AWS Console is typically performed when 
developing and debugging resources for a new project. When the project becomes finished 
and stable, CloudFormation template files can be written to automate most of the manual
work. Full automation can be achieved by writing either a Python script or a batch file. 
The Python script controls AWS by calling an AWS-supported library, while the batch file
executes the AWS CLI.

The files in this repository can be used to create AWS resources by either of the 
following methods.

* In the AWS Console, submit the repository's template files to the CloudFormation service.
* From a command-line prompt, run the `CreateLambda.py` Python script.

## Create AWS resources manually

Prerequisites: None.

The Lambda function source code can be typed manually into the Lambda service using
the AWS Console. The repository's `test.py` file can be copied and pasted into the
service to define the Lambda function.

Alternatively, the function code can be written and saved in a text file and then 
uploaded to the Lambda service by performing the following steps.

1. Write and save the Lambda source code in a text file.
2. Store the source file, including all required library files, in a ZIP file. (The
`test.py` file does not require any additional libraries.)
3. Create an AWS S3 bucket.
4. Copy the ZIP file to the bucket.
5. In the AWS Console, create a new AWS Lambda function, instructing the service to
upload the S3 ZIP file.

Afterward, use the AWS Console and the API Gateway service to create a REST API 
interface to the Lambda function.

## Create AWS resources in CloudFormation

Prerequisites: Store the repository's `test.py` file in a ZIP file called `test.zip`. 
The script does not require any additional libraries, so the ZIP file can include only
the `test.py` file. 
	
1. In the AWS Console and CloudFormation service, create a stack using the repository's
`CreateS3Bucket.yaml` template file. The file creates an S3 bucket called
`gwdoc-lambda-functions`.  
2. In the S3 service, copy the `test.zip` file to the bucket.
3. In CloudFormation, create another stack using the repository's `CreateLambdaFunction.yaml`
template file. The file creates a Lambda function, REST API interface to it, and all 
required associated resources.

To invoke the Lambda function, use a program like `Postman` or `curl` to call
its REST API. The HTTPS address to call is located in the API Gateway resource.
Go to the resource's `Stages` page. Expand the Stages address elements and select
the `GET` operation. The HTTPS address to call is shown at the top of the page.
Copy the address and paste it into a `Postman` GET operation or `curl` command line.

The `test.py` Lambda function accepts integer query arguments called `next` and
`limit` and returns their values in the JSON response. A sample GET invocation 
is shown below.

    https://8281alslsqu5.execute-api.us-east-1.amazonaws.com/v1/user?next=1&limit=2

Note: CloudFormation template files can be created programatically by using the 
Python `troposphere` library. This technique might be useful if the template file
contains configuration settings that depend on conditions that are not known
until the resource is being created.  

## Create AWS resources with a Python script

Prerequisites:
* Store the repository's `test.py` file in a ZIP file called `test.zip`.
* Install Python 3.x.
* Install the AWS Python library `boto3`. Instructions are at https://github.com/boto/boto3.
* Install the AWS CLI (Command Line Interface). Windows installation instructions are at 
https://docs.aws.amazon.com/cli/latest/userguide/awscli-install-windows.html. The CLI
can be installed by using either a Windows MSI installer or the Python `pip` 
command. The `pip` method is recommended to ease updating the CLI in the future.
* Configure the AWS CLI. Instructions are at 
https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html.

Run the repository's `CreateLambda.py` script to create the Lambda function, REST
API interface, and related resources. You do not need to be signed into AWS before
running the script. The script gains access to AWS by using the AWS `credentials` 
file that was created while configuring the CLI.

    python CreateLambda.py

To delete the script's AWS resources, run the script with the `-d` or `--delete` argument.

    python CreateLambda.py -d
