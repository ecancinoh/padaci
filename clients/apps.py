from django.apps import AppConfig
from django.db import connections


class ClientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clients'

    def ready(self):
        self._ensure_observaciones_column()

    def _ensure_observaciones_column(self):
        try:
            from .models import Cliente

            connection = connections['default']
            table_name = Cliente._meta.db_table
            column_name = 'observaciones'

            with connection.cursor() as cursor:
                existing_tables = set(connection.introspection.table_names(cursor))
                if table_name not in existing_tables:
                    return

                table_description = connection.introspection.get_table_description(cursor, table_name)
                existing_columns = {column.name.lower() for column in table_description}

            if column_name in existing_columns:
                return

            field = Cliente._meta.get_field(column_name)
            with connection.schema_editor() as schema_editor:
                schema_editor.add_field(Cliente, field)
        except Exception:
            return
