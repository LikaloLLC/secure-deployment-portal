import os
from datetime import datetime, timedelta
import logging
import sys
from dotenv import load_dotenv

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# # Debug: Print environment before .env load
# logger.info("BEFORE .env load:")
# logger.info("AZURE_AD_CLIENT_ID: %s", os.getenv('AZURE_AD_CLIENT_ID'))
# logger.info("All AZURE vars: %s", {k: v for k, v in os.environ.items() if 'AZURE' in k})

# Load environment variables from .env file
logger.info("Loading .env file...")
load_dotenv(override=True)  # Add override=True to force .env values

# # Debug: Print environment after .env load
# logger.info("AFTER .env load:")
# logger.info("AZURE_AD_CLIENT_ID: %s", os.getenv('AZURE_AD_CLIENT_ID'))
# logger.info("All AZURE vars: %s", {k: v for k, v in os.environ.items() if 'AZURE' in k})

# # Debug: Print raw environment variables
# logger.info("Raw AZURE_AD_CLIENT_ID: %s", os.getenv('AZURE_AD_CLIENT_ID'))
# logger.info("Raw AZURE_AD_AUTHORITY: %s", os.getenv('AZURE_AD_AUTHORITY'))
# logger.info("Raw AZURE_AD_REDIRECT_URI: %s", os.getenv('AZURE_AD_REDIRECT_URI'))
# logger.info("All env vars: %s", {k: v for k, v in os.environ.items() if 'AZURE' in k})

if os.getenv('FLASK_ENV') == 'production':
    try:
        import gevent.monkey
        gevent.monkey.patch_all()
        logger.info("Gevent monkey patching completed")
    except Exception as e:
        logger.error(f"Failed to patch gevent: {str(e)}")

from urllib.parse import parse_qs, urlencode, urlparse

import jwt
from flask import Flask, redirect, request
from identity.flask import Auth
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_session import Session

__version__ = '0.1.0'

app = Flask(__name__)
# See https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
app.wsgi_app = ProxyFix(app.wsgi_app)

try:
    # Configuration
    logger.info("Raw env vars before config:")
    logger.info("AZURE_AD_CLIENT_ID: %s", os.getenv('AZURE_AD_CLIENT_ID'))
    
    # Instead of using from_prefixed_env, set config directly
    app.config['CLIENT_ID'] = os.getenv('AZURE_AD_CLIENT_ID')
    app.config['CLIENT_SECRET'] = os.getenv('AZURE_AD_CLIENT_SECRET')
    app.config['AUTHORITY'] = os.getenv('AZURE_AD_AUTHORITY')
    app.config['REDIRECT_URI'] = os.getenv('AZURE_AD_REDIRECT_URI')
    app.config['PORTAL_MASTER_KEY'] = os.getenv('DOCSIE_PORTAL_MASTER_KEY')
    app.config['PORTAL_URL'] = os.getenv('DOCSIE_PORTAL_URL')
    
    logger.info("Config after direct set:")
    logger.info("CLIENT_ID: %s", app.config['CLIENT_ID'])
    
    # Validate required config
    required_configs = {
        'CLIENT_ID': 'AZURE_AD_CLIENT_ID',
        'CLIENT_SECRET': 'AZURE_AD_CLIENT_SECRET',
        'AUTHORITY': 'AZURE_AD_AUTHORITY',
        'REDIRECT_URI': 'AZURE_AD_REDIRECT_URI',
        'PORTAL_MASTER_KEY': 'DOCSIE_PORTAL_MASTER_KEY',
        'PORTAL_URL': 'DOCSIE_PORTAL_URL'
    }
    
    for config_key, env_var in required_configs.items():
        if not app.config.get(config_key):
            raise ValueError(f'`{env_var}` environment variable is required.')
        else:
            logger.info(f"Config {config_key} is set")
            
    # Token expiration
    app.config['TOKEN_EXPIRY_MINUTES'] = int(os.getenv('DOCSIE_TOKEN_EXPIRY_MINUTES', '60'))
    logger.info(f"Token expiry set to {app.config['TOKEN_EXPIRY_MINUTES']} minutes")
    
    # Session configuration
    if os.getenv('FLASK_ENV') == 'production':
        session_dir = os.getenv('FLASK_SESSION_DIR', '/app/session')
    else:
        # Use a local directory for development
        session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'session')
    
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = session_dir
    os.makedirs(session_dir, exist_ok=True)
    logger.info(f"Session directory created at {session_dir}")

    Session(app)
    
    # Auth setup
    logger.info("Setting up Auth with:")
    logger.info("  - Authority: %s", app.config['AUTHORITY'])
    logger.info("  - Client ID: %s", app.config['CLIENT_ID'])
    logger.info("  - Redirect URI: %s", app.config['REDIRECT_URI'])
    
    auth = Auth(
        app,
        oidc_authority=app.config['AUTHORITY'],
        client_id=app.config['CLIENT_ID'],
        client_credential=app.config['CLIENT_SECRET'],
        redirect_uri=app.config['REDIRECT_URI'],
    )
    logger.info("Auth setup completed")
    
except Exception as e:
    logger.error(f"Failed to initialize app: {str(e)}")
    raise

def get_user_claims(context):
    """Extract claims from the auth context following Azure AD standards"""
    # Get claims from different possible locations
    id_token_claims = context.get('id_token_claims', {}) if context else {}
    user_info = context.get('user', {}) if context else {}
    
    logger.info("ID token claims: %s", id_token_claims)
    logger.info("User info: %s", user_info)
    
    # Try to get email from various possible claims
    email = (
        id_token_claims.get('preferred_username') or 
        id_token_claims.get('email') or 
        id_token_claims.get('upn') or 
        user_info.get('preferred_username') or
        user_info.get('email') or
        ''
    )
    
    # Try to get name from various possible claims
    name = (
        id_token_claims.get('name') or 
        user_info.get('name') or
        ' '.join(filter(None, [
            id_token_claims.get('given_name', ''),
            id_token_claims.get('family_name', '')
        ])) or
        ''
    )
    
    result = {
        'email': email,
        'name': name,
        'groups': id_token_claims.get('groups', []),
        'tid': id_token_claims.get('tid', '') or user_info.get('tid', ''),
        'oid': id_token_claims.get('oid', '') or user_info.get('oid', '')
    }
    
    logger.info("Final processed claims: %s", result)
    return result

def generate_jwt_for_portal(master_key: str, claims: dict) -> str:
    """Generate JWT with claims and expiry"""
    if not claims:
        logger.warning("No claims provided for JWT generation")
        claims = {}
        
    payload = {
        'claims': claims,  # Nest claims under 'claims' key
        'exp': int((datetime.utcnow() + timedelta(minutes=app.config['TOKEN_EXPIRY_MINUTES'])).timestamp())
    }
    
    logger.info("Generating JWT with payload: %s", payload)
    return jwt.encode(payload, master_key, algorithm='HS256')

def with_query_params(url: str, **params) -> str:
    url_components = urlparse(url)
    original_params = parse_qs(url_components.query)
    merged_params = {**original_params, **params}
    updated_query = urlencode(merged_params, doseq=True)
    # _replace() is how you can create a new NamedTuple with a changed field
    url_components = url_components._replace(query=updated_query)
    if not url_components.path.endswith('/'):
        url_components = url_components._replace(path=url_components.path + '/')

    return url_components.geturl()

@app.route('/')
@auth.login_required()
def index(*, context):
    try:
        logger.info("Processing request with context")
        logger.info("Raw context type: %s", type(context))
        logger.info("Raw context keys: %s", context.keys() if context else None)
        logger.info("Raw context content: %s", context)

        # Get user information directly
        try:
            user = auth.get_user()
            logger.info("User info from auth.get_user(): %s", user)
        except Exception as e:
            logger.error("Error getting user info: %s", str(e))

        # Try to get claims directly from the token
        try:
            token = context.get('id_token_claims', {})
            logger.info("Direct token claims: %s", token)
        except Exception as e:
            logger.error("Error accessing token claims: %s", str(e))
        
        # Extract claims from context
        claims = get_user_claims(context)
        logger.info("Final processed claims: %s", claims)
        
        # Generate token
        token = generate_jwt_for_portal(
            str(app.config['PORTAL_MASTER_KEY']), 
            claims
        )
        
        # Log the final token contents
        try:
            decoded = jwt.decode(token, str(app.config['PORTAL_MASTER_KEY']), algorithms=['HS256'])
            logger.info("Final JWT contents: %s", decoded)
        except Exception as e:
            logger.error("Error decoding JWT: %s", str(e))
        
        # Check if there's a return URL in the query parameters
        return_url = request.args.get('return')
        
        if return_url:
            # If return URL exists, append token to it and redirect there
            redirect_url = with_query_params(return_url, token=token)
            logger.info("Redirecting to return URL: %s", redirect_url)
            return redirect(redirect_url)
        else:
            # Otherwise use the default portal URL
            portal_url = with_query_params(
                app.config['PORTAL_URL'],
                token=token
            )
            logger.info("Redirecting to portal: %s", portal_url)
            return redirect(portal_url)
        
    except Exception as e:
        logger.error("Error in index route: %s", str(e), exc_info=True)
        raise

if __name__ == '__main__':
    logger.info("Starting development server")
    app.run(host='localhost', port=5001)
