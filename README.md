# Docsie Secure Portals with Microsoft Authentication
This application provides Single Sign-On (SSO) authentication for Docsie secured portals using Microsoft  Azure AD (Entra ID).

## Quick Deploy
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)
[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FLikaloLLC%2Fsecure-deployment-portal%2Fmain%2Fazuredeploy.json)


## Initial Setup
- The application is configured with Azure AD (Microsoft Entra ID) credentials
- A Docsie portal master key and portal URL are required
- The application uses Flask as the web framework

## Authentication Flow
```mermaid
sequenceDiagram
    User->>Flask App: Visits application
    Flask App->>Azure AD: Redirects to Microsoft login
    Azure AD->>User: Shows login page
    User->>Azure AD: Authenticates
    Azure AD->>Flask App: Returns with auth token
    Flask App->>Docsie Portal: Generates JWT using portal master key
    Flask App->>User: Redirects to portal URL with JWT
```

## Key Components
- **Azure AD Authentication**: Handled by the Auth middleware from identity.flask
- **JWT Generation**: A simple JWT is created using the portal master key
- **URL Handling**: The application appends the JWT as a query parameter to the portal URL

## Security Measures
- All routes are protected with `@auth.login_required()`
- Environment variables are required for sensitive credentials
- HTTPS proxy support is enabled for production environments
- Gevent is used for production deployments

This creates a secure flow where:
1. Users must authenticate through Microsoft
2. Only authenticated users can access the portal
3. The portal validates the JWT that was signed with the master key
4. No sensitive credentials are exposed to the end user

The system acts as a secure bridge between Microsoft's authentication and Docsie's portal access control.

# Installation
## Step 1: Register your application
1. Sign in to the [Microsoft Entra admin center](https://entra.microsoft.com/) as at least a Cloud Application Administrator.
2. If you have access to multiple tenants, use the **Settings** icon in the top menu to switch to the tenant in which you want to register the application from the **Directories + subscriptions** menu.
3. Browse to **Identity** > **Applications** > **App registrations** and select **New registration**.
4. Enter a **Name** for your application, for example _my-docsie-portal_.
5. Under **Supported account types**, select **Accounts in this organizational directory only**.
6. Under **Redirect URIs**, select **Web** for the platform.
7. Enter a redirect URI of http://localhost:5000/getAToken. You can change this value later.
8. Select **Register**.

![Application overview](media/entra-app-conf.png)

## Step 2: Add a client secret
1. On the app **Overview** page, note the **Application (client) ID** value for later use.
2. Under **Manage**, select the **Certificates & secrets** and from the **Client secrets** section, select **New client secret**.
3. Enter a description for the client secret, leave the default expiration, and select **Add**.
4. Save the **Value** of the **Client Secret** in a safe location. You need this value configure the code, and you can't retrieve it later.

## Step 3: Configure the app
1. Open the application you downloaded
    ```shell
    cd docsie-secure-portals-ms-auth
    ```
2. Create an `.env` file in the root folder of the project using `.env.sample` as a guide.
    
    ```env
    # The following variables are required for the app to run.
   
    SECRET_KEY=<generated_random_secret_key>
   
    AZURE_AD_CLIENT_ID=<Enter_your_client_id>
    AZURE_AD_CLIENT_SECRET=<Enter_your_client_secret>
    AZURE_AD_AUTHORITY=<Enter_your_authority_url>
    AZURE_AD_REDIRECT_URI=<Enter_redirect_uri>
   
    DOCSIE_PORTAL_MASTER_KEY=<Enter_your_portal_master_key>
    DOCSIE_PORTAL_URL=<Enter_your_portal_url>
    ```
   * Set the value of `SECRET_KEY` to the generated random string.
   * Set the value of `AZURE_AD_CLIENT_ID` to the **Application (client) ID** for the registered application, available on the overview page.
   * Set the value of `AZURE_AD_CLIENT_SECRET` to the client secret you created in the **Certificates & Secrets** for the registered application.
   * Set the value of `AZURE_AD_AUTHORITY` to a `https://login.microsoftonline.com/<TENANT_GUID>`. The **Directory (tenant) ID** is available on the app registration overview page.
   * Set the value of `AZURE_AD_REDIRECT_URI` to the `http://localhost:5000/getAToken` (or the one you entered in the **Redirect URIs** of the application). 
   * Set the value of `DOCSIE_PORTAL_MASTER_KEY` to the master key for portal deployment.
   * Set the value of `DOCSIE_PORTAL_URL` to the URL of your portal.

## Step 4: Run the app
Using Docker Compose:
```shell
docker compose up -d
```

