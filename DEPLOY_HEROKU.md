# Deploying to Heroku

## Quick Deploy
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Manual Deployment Steps

1. **Prerequisites**
   - A Heroku account
   - [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
   - Git installed

2. **Create a New Heroku App**
   ```bash
   heroku create your-app-name
   ```

3. **Configure Environment Variables**
   Set the following required environment variables:
   ```bash
   heroku config:set AZURE_AD_CLIENT_ID=your_client_id
   heroku config:set AZURE_AD_CLIENT_SECRET=your_client_secret
   heroku config:set AZURE_AD_AUTHORITY=https://login.microsoftonline.com/your_tenant_id
   heroku config:set AZURE_AD_REDIRECT_URI=https://your-app-name.herokuapp.com/auth/redirect
   heroku config:set DOCSIE_PORTAL_MASTER_KEY=your_master_key
   heroku config:set DOCSIE_PORTAL_URL=your_portal_url
   heroku config:set SECRET_KEY=your_secret_key
   ```

4. **Deploy the Application**
   ```bash
   git push heroku main
   ```

5. **Open the Application**
   ```bash
   heroku open
   ```

## Post-Deployment Configuration

1. Update your Microsoft Entra ID application settings with your new Heroku URL
2. Add `https://your-app-name.herokuapp.com/auth/redirect` to your application's redirect URIs

## Troubleshooting

- View application logs:
  ```bash
  heroku logs --tail
  ```
- Restart the application:
  ```bash
  heroku restart
  ```

For more detailed information about Heroku deployments, visit [Heroku's documentation](https://devcenter.heroku.com/articles/getting-started-with-python). 