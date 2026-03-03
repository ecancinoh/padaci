from django.db import migrations, models


def add_observaciones_if_missing(apps, schema_editor):
    Cliente = apps.get_model('clients', 'Cliente')
    table_name = Cliente._meta.db_table
    column_name = 'observaciones'

    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name.lower()
            for column in schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }

    if column_name not in columns:
        field = models.TextField(
            blank=True,
            default='',
            help_text='Indicaciones especiales de entrega, acceso, horarios, etc.',
            verbose_name='Observaciones',
        )
        field.set_attributes_from_name(column_name)
        schema_editor.add_field(Cliente, field)


def remove_observaciones_if_exists(apps, schema_editor):
    Cliente = apps.get_model('clients', 'Cliente')
    table_name = Cliente._meta.db_table
    column_name = 'observaciones'

    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name.lower()
            for column in schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }

    if column_name in columns:
        field = models.TextField(
            blank=True,
            default='',
            help_text='Indicaciones especiales de entrega, acceso, horarios, etc.',
            verbose_name='Observaciones',
        )
        field.set_attributes_from_name(column_name)
        schema_editor.remove_field(Cliente, field)


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_alter_cliente_options_cliente_comuna_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_observaciones_if_missing, remove_observaciones_if_exists),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='cliente',
                    name='observaciones',
                    field=models.TextField(blank=True, default='', help_text='Indicaciones especiales de entrega, acceso, horarios, etc.', verbose_name='Observaciones'),
                ),
            ],
        ),
    ]
