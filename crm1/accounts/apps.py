from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Wire up signal handlers only — no DB queries here.
        # All DB work (get_or_create, queryset calls) lives inside the
        # signal receivers in signals.py, which run lazily on first use.
        import accounts.signals  # noqa: F401
