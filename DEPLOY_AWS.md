# Deploying to AWS

## Quick Deploy
[![Deploy to AWS](https://raw.githubusercontent.com/amazonwebservices/aws-cloudformation-templates/master/aws-logo.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=docsie-ms-auth&templateURL=https://raw.githubusercontent.com/LikaloLLC/secure-deployment-portal/main/aws-template.yaml)

## Manual Deployment Steps

1. **Prerequisites**
   - An AWS account
   - [AWS CLI](https://aws.amazon.com/cli/) installed and configured
   - [AWS Elastic Beanstalk CLI](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html) installed

2. **Configure AWS CLI**
   ```bash
   aws configure
   ```

3. **Initialize Elastic Beanstalk Application**
   ```bash
   eb init -p docker docsie-ms-auth
   ```

4. **Create Environment**
   ```bash
   eb create docsie-ms-auth-env
   ```

5. **Configure Environment Variables**
   ```bash
   eb setenv \
     AZURE_AD_CLIENT_ID=your_client_id \
     AZURE_AD_CLIENT_SECRET=your_client_secret \
     AZURE_AD_AUTHORITY=https://login.microsoftonline.com/your_tenant_id \
     AZURE_AD_REDIRECT_URI=your_redirect_uri \
     DOCSIE_PORTAL_MASTER_KEY=your_master_key \
     DOCSIE_PORTAL_URL=your_portal_url \
     SECRET_KEY=your_secret_key
   ```

6. **Deploy Application**
   ```bash
   eb deploy
   ```

## Using AWS Console

1. Go to [AWS Console](https://console.aws.amazon.com)
2. Navigate to Elastic Beanstalk
3. Create new application
4. Choose Docker platform
5. Upload your code or specify GitHub repository
6. Configure environment variables in Configuration settings

## Post-Deployment Configuration

1. Update Microsoft Entra ID application settings:
   - Add your AWS endpoint URL to redirect URIs
   - Update application settings if necessary

## Monitoring and Troubleshooting

- View logs:
  ```bash
  eb logs
  ```
- SSH into instance:
  ```bash
  eb ssh
  ```
- Monitor health:
  ```bash
  eb health
  ```

## Additional Resources

- [AWS Elastic Beanstalk Documentation](https://docs.aws.amazon.com/elasticbeanstalk/)
- [Docker on AWS](https://aws.amazon.com/docker/)
- [AWS CloudFormation](https://aws.amazon.com/cloudformation/) 