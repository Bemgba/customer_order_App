from decouple import config

class OtpTokenConfig:
    LENGTH = config("TOKEN_LENGTH",  default=1, cast=int)   
    EXPIRES_IN_MINUTES = config("OTP_TOKEN_EXPIRES_IN_MINUTES", default=15, cast=int)

class DatabaseConfig:
    pass