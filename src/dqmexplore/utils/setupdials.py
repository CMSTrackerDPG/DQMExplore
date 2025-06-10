def setup_dials_object_deviceauth():
    from cmsdials import Dials
    from cmsdials.auth.bearer import Credentials

    creds = Credentials.from_creds_file()
    return Dials(creds)
