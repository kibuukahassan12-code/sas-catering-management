def init_sentry(app):
    # Disable Sentry until a valid DSN is configured
    print("Sentry disabled: no valid DSN provided.")
    return