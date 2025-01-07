import os

if os.getenv('FLASK_ENV') == 'production':
    import gevent.monkey

    gevent.monkey.patch_all()

from urllib.parse import parse_qs, urlencode, urlparse

import jwt
from flask import Flask, redirect
from identity.flask import Auth
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_session import Session

__version__ = '0.1.0'

app = Flask(__name__)
# See https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
app.wsgi_app = ProxyFix(app.wsgi_app)

# Configuration
app.config.from_prefixed_env(prefix='AZURE_AD')
app.config.from_prefixed_env(prefix='DOCSIE')

assert app.config.get('CLIENT_ID'), '`AZURE_AD_CLIENT_ID` environment variable is required.'
assert app.config.get('CLIENT_SECRET'), '`AZURE_AD_CLIENT_SECRET` environment variable is required.'
assert app.config.get('AUTHORITY'), '`AZURE_AD_AUTHORITY` environment variable is required.'
assert app.config.get('REDIRECT_URI'), '`AZURE_AD_REDIRECT_URI` environment variable is required.'
assert app.config.get('PORTAL_MASTER_KEY'), '`DOCSIE_PORTAL_MASTER_KEY` environment variable is required.'
assert app.config.get('PORTAL_URL'), '`DOCSIE_PORTAL_URL` environment variable is required.'

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.getenv('FLASK_SESSION_DIR', '/app/session')
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

Session(app)

# Auth
auth = Auth(
    app,
    oidc_authority=app.config['AUTHORITY'],
    client_id=app.config['CLIENT_ID'],
    client_credential=app.config['CLIENT_SECRET'],
    redirect_uri=app.config['REDIRECT_URI'],
)

def get_user_claims(context):
    """Extract claims from the auth context with fallbacks"""
    # Get claims with fallback to empty dict
    claims = (context or {}).get('id_token_claims', {})
    
    # Build claims object with fallbacks for everything
    result = {
        'email': claims.get('preferred_username', ''),
        'tenant': claims.get('tid', ''),
        'groups': claims.get('groups', []) if isinstance(claims.get('groups'), list) else [],
        'department': claims.get('department', ''),
        'company': claims.get('companyName', '')
    }
    
    # Log if we're missing expected claims but don't fail
    if not result['email'] or not result['tenant']:
        print(f"Warning: Missing some expected claims. email: {bool(result['email'])}, tenant: {bool(result['tenant'])}")
        
    return result

def generate_jwt_for_portal(master_key: str, claims: dict) -> str:
    """Generate JWT with claims"""
    return jwt.encode(claims, master_key, algorithm='HS256')

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
    # Extract claims from context
    claims = get_user_claims(context)
    
    # Generate token with claims
    token = generate_jwt_for_portal(
        str(app.config['PORTAL_MASTER_KEY']), 
        claims
    )
    
    # Only pass the secure token, claims will be extracted server-side
    portal_url = with_query_params(
        app.config['PORTAL_URL'],
        token=token  # JWT contains all claims, encrypted with master key
    )

    return redirect(portal_url)

if __name__ == '__main__':
    app.run(host='localhost')
