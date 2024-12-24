# WorkMail Automation with AWS Lambda

---

### Update (23 December 2024)
Units tests have been updated. They're not in their final form as development is ongoing; some are "quick and dirty" sanity-checks. "Finalized" unit tests and integration tests coming soon-ish, along with more useful documentation.

---

### Update (15 December 2024)
The underlying functions for which all the tests were written have changed, so I expect that, at the moment, none of them pass. I will push updated tests soon.

---

## Description
![AWS SAM](https://img.shields.io/badge/AWS-SAM-orange)
![CloudFormation](https://img.shields.io/badge/AWS-CloudFormation-blue)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Boto3](https://img.shields.io/badge/Boto3-1.28.0-blue)

![GitHub last commit](https://img.shields.io/github/last-commit/garrettdotdev/workmail-lambda)
![GitHub repo size](https://img.shields.io/github/repo-size/garrettdotdev/workmail-lambda)
![License](https://img.shields.io/github/license/garrettdotdev/workmail-lambda)

[//]: # (![Build Status]&#40;https://github.com/garrettdotdev/workmail-lambda/actions/workflows/lint-test.yml/badge.svg&#41;)
[//]: # (![Dependencies]&#40;https://img.shields.io/librariesio/github/garrettdotdev/workmail-lambda&#41;)
[//]: # (![GitHub issues]&#40;https://img.shields.io/github/issues/garrettdotdev/workmail-lambda&#41;)

This is a contract project I am working on for a client. They have graciously agreed to allow me to share the code publicly.

The purpose of the project is to automate the creation and deletion of AWS WorkMail organizations and users using AWS Lambda functions exposed via an Http Api Gateway. By providing a few input parameters, WorkMail Organizations and Users can be rapidly provisioned (or removed).

The automation process is powered by AWS SAM (Serverless Application Model) and AWS CloudFormation to define and deploy the required AWS resources. The project is still in active development and not yet fully functional. I project that the first production version will be deployed before the New Year.

Because this project is being developed for a specific client, some aspects of the assumed environment may either (a) not make sense to you or (b) not apply to your architecture. To implement this code in another environment (beyond it needing to be finished) will require several modifications to suit your environment, including the input schemas, database interactions, environment variables, and so on.

On the other hand, a large portion of the SAM template (`template.yaml`) and the codebase should be usable with minimal modifications. WorkMail is as yet unsupported by CloudFormation which makes automating it a bit more challenging than we've become accustomed to with other AWS services. My hope is that by sharing this codebase, it can at least serve as inspiration or get you unstuck on your own projects.

## Architecture
The project follows a serverless architecture that includes:

- **AWS Lambda Functions**: Two primary functions — `workmail_create` and `workmail_cancel` — handle the creation and deletion of WorkMail organizations, respectively. There will likely be additional functions added as development continues.
- **AWS API Gateway**: Provides HTTP endpoints to trigger the Lambda functions.
- **AWS CloudFormation**: Manages the infrastructure as code (IaC) for the entire stack.
- **AWS SAM**: Simplifies the process of building and deploying the application.

## Primary Language
The primary language for this project is Python, which is used to write the Lambda functions and associated logic. The project uses the `boto3` library to interact with AWS services.

CloudFormation is handled by AWS SAM, template is written in YAML.

## Project Structure
The repository is organized as follows:

```
workmail-lambda/
├── layers/
│   └── common/              # Source for Lambda layer shared by all functions
├── workmail_authorizer/     # Code and resources for the AuthorizerFunction
│   ├── app.py               # Application logic for AuthorizerFunction (not yet implemented)
│   └── requirements.txt
├── workmail_cancel/         # Code and resources for the CancelFunction
│   ├── schemas/             # Contains input-validation JSON schema
│   ├── app.py               # Application logic for CancelFunction
│   └── requirements.txt
├── workmail_create/         # Code and resources for the CreateFunction
│   ├── schemas/             # Contains input-validation JSON schema
│   ├── app.py               # Application logic for CreateFunction
│   └── requirements.txt
├── samconfig.toml           # Configuration file for AWS SAM
├── template.yaml            # AWS SAM template for defining the CloudFormation stack
└── README.md                # This file
```

## Endpoints
The project exposes the following endpoints via API Gateway:

1. **Create WorkMail Organization**
   - **Path**: `/workmail/create`
   - **Method**: POST
   - **Description**: Creates a WorkMail organization with the provided input parameters.
   - **Input Schema**: The expected payload is defined in `workmail_create/schemas/input_schema.json`.

2. **Cancel WorkMail Organization**
   - **Path**: `/workmail/cancel`
   - **Method**: POST
   - **Description**: Deletes a WorkMail organization and associated user(s) based on the input parameters.
   - **Input Schema**: The expected payload is defined in `workmail_cancel/schemas/input_schema.json`.

*Note: It is likely that at least one more endpoint will be added. More on that later.*

## Input Parameters
The required input parameters for each function are defined in JSON schema files. The key parameters are:

### Create Endpoint (`workmail_create/schemas/input_schema.json`)
- **contact_id**: Used to look up customer information in the RDS database.
- **appname**: Used along with `contact_id` to query the RDS database.
- **email_username**: Username for the email address.
- **vanity_name**: Domain name for the email address.

### Cancel Endpoint (`workmail_cancel/schemas/input_schema.json`)
- **organization_id**: Unique identifier of the WorkMail organization to be canceled.
- **email_username**: Username of the user whose WorkMail account should be removed.
- **vanity_name**: Domain name associated with the WorkMail organization.

> **Note**: These schemas are still under development and may change as the project evolves.

## Deployment
To deploy this project, you must have the AWS SAM CLI installed and configured with AWS credentials.

### Prerequisites
- **AWS CLI**: To manage AWS resources.
- **AWS SAM CLI**: To build, package, and deploy the serverless application.
- **Python 3.12**: Required to run the Python Lambda functions.

### Deployment Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/garrettdotdev/workmail-lambda.git
   cd workmail-lambda
   ```

2. Build the SAM application:
   ```bash
   sam build
   ```

3. Deploy the application:
   ```bash
   sam deploy --guided
   ```
   Follow the prompts to specify deployment parameters, such as stack name and AWS region.

Once deployed, the API Gateway URL will be displayed in the output. Use this URL to make requests to the `create` and `cancel` endpoints.

## Development
This project is actively being developed, and not all features are fully functional. The following items are still in progress:

- **Full API Functionality**: Primary focus at the moment. The `workmail_create` and `workmail_cancel` functions are not yet fully implemented.
- **Complete Unit and Integration Tests**: Test files are in place but currently fail because they're behind the times. On my list to update these.

## Usage
To create a WorkMail organization, send a POST request to the `/workmail/create` endpoint. An example request body might look like this:

```json
{
  "contact_id": "12345",
  "appname": "exampleapp",
  "email_username": "john.doe",
  "vanity_name": "example.com"
}
```

To cancel a WorkMail organization, send a POST request to the `/workmail/cancel` endpoint with a payload like this:

```json
{
  "organization_id": "m-1234567890",
  "email_username": "john.doe",
  "vanity_name": "example.com"
}
```

## Testing
The project includes unit and integration tests located in the `tests/` directory. To run the tests, use the following command:

```bash
pytest tests/
```

> **Note**: Some tests are placeholders and may not be fully implemented.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact
If you have questions, please reach out to the repository owner via GitHub Issues or pull requests.

