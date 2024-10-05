from decouple import Config, Csv

config = Config()

DEBUG = config('DEBUG', default=False, cast=bool)

class OtpTokenConfig:
    LENGTH = config("TOKEN_LENGTH")
    EXPIRES_IN_MINUTES = config("OTP_TOKEN_EXPIRES_IN_MINUTES")

class DatabaseConfig:
    pass