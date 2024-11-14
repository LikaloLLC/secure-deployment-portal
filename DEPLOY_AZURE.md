# Deploying to Azure

## Quick Deploy
[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FLikaloLLC%2Fsecure-deployment-portal%2Fmain%2Fazuredeploy.json)

## Manual Deployment Steps

1. **Prerequisites**
   - An Azure account
   - [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
   - [Azure App Service Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azureappservice) for VS Code (optional)

2. **Login to Azure**
   ```bash
   az login
   ```

3. **Create Resource Group**
   ```bash
   az group create --name your-resource-group --location eastus
   ```

4. **Create App Service Plan**
   ```bash
   az appservice plan create --name your-service-plan --resource-group your-resource-group --sku B1 --is-linux
   ```

5. **Create Web App**
   ```bash
   az webapp create --resource-group your-resource-group --plan your-service-plan --name your-app-name --runtime "PYTHON:3.11" --deployment-container-image-name your-docker-image
   ```

6. **Configure Environment Variables**
   ```bash
   az webapp config appsettings set --resource-group your-resource-group --name your-app-name --settings \
     AZURE_AD_CLIENT_ID=your_client_id \
     AZURE_AD_CLIENT_SECRET=your_client_secret \
     AZURE_AD_AUTHORITY=https://login.microsoftonline.com/your_tenant_id \
     AZURE_AD_REDIRECT_URI=https://your-app-name.azurewebsites.net/auth/redirect \
     DOCSIE_PORTAL_MASTER_KEY=your_master_key \
     DOCSIE_PORTAL_URL=your_portal_url \
     SECRET_KEY=your_secret_key
   ```

7. **Deploy the Application**
   ```bash
   az webapp deployment source config --name your-app-name --resource-group your-resource-group --repo-url https://github.com/LikaloLLC/secure-deployment-portal --branch main
   ```

## Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new Web App
3. Under "Deployment Center":
   - Choose "GitHub" as source
   - Configure GitHub connection
   - Select repository and branch
4. Under "Configuration":
   - Add all required environment variables
5. Under "Overview":
   - Click "Browse" to open your application

## Post-Deployment Configuration

1. Update your Microsoft Entra ID application settings:
   - Add `https://your-app-name.azurewebsites.net/auth/redirect` to redirect URIs
   - Update application settings if necessary

## Monitoring and Troubleshooting

- View logs:
  ```bash
  az webapp log tail --name your-app-name --resource-group your-resource-group
  ```
- Restart app:
  ```bash
  az webapp restart --name your-app-name --resource-group your-resource-group
  ```
- Monitor metrics in Azure Portal:
  - Go to your Web App
  - Click on "Metrics" under Monitoring

## Additional Resources

- [Azure Web Apps Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Python on Azure Documentation](https://docs.microsoft.com/en-us/azure/app-service/configure-language-python)
- [Azure Container Registry](https://docs.microsoft.com/en-us/azure/container-registry/) 