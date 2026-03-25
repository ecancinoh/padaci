from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from clients.models import Cliente

from .services import reoptimizar_planes_por_cliente


LOCATION_FIELDS = ('comuna', 'latitud', 'longitud', 'direccion', 'ciudad', 'region')


@receiver(pre_save, sender=Cliente)
def cliente_pre_save_detectar_cambio_ubicacion(sender, instance, **kwargs):
    if not instance.pk:
        instance._planner_location_changed = False
        return

    try:
        previo = Cliente.objects.get(pk=instance.pk)
    except Cliente.DoesNotExist:
        instance._planner_location_changed = False
        return

    changed = any(getattr(previo, field) != getattr(instance, field) for field in LOCATION_FIELDS)
    instance._planner_location_changed = changed


@receiver(post_save, sender=Cliente)
def cliente_creado_enviar_a_planes(sender, instance, created, **kwargs):
    if not created:
        if getattr(instance, '_planner_location_changed', False):
            reoptimizar_planes_por_cliente(instance)
    return
