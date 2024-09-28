def setup_dials_object_deviceauth():
    from cmsdials import Dials
    from cmsdials.auth.client import AuthClient
    from cmsdials.auth.bearer import Credentials

    auth = AuthClient()
    token = auth.device_auth_flow()
    creds = Credentials.from_authclient_token(token)
    return Dials(creds)
