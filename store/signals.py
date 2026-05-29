from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SocialMediaAccount, Platform


@receiver(post_save, sender=SocialMediaAccount)
def update_platform_quantity_on_account_change(sender, instance, created, **kwargs):
    """
    Update Platform quantity whenever a SocialMediaAccount is added or modified.
    This handles:
    - New accounts added (created=True)
    - Accounts updated (created=False), e.g., is_assigned status changes
    """
    platform = instance.platform
    platform.save()  # This triggers the quantity recalculation in Platform.save()


@receiver(post_delete, sender=SocialMediaAccount)
def update_platform_quantity_on_account_delete(sender, instance, **kwargs):
    """
    Update Platform quantity whenever a SocialMediaAccount is deleted.
    """
    platform = instance.platform
    platform.save()  # This triggers the quantity recalculation in Platform.save()

