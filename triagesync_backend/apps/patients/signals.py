"""
Signal handlers for Patient model.

Handles automatic cleanup of profile photo files when:
- A new photo is uploaded (deletes old photo)
- A Patient instance is deleted (deletes associated photo)

Requirements: 10.1, 10.3, 10.4, 10.5
"""

import logging
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import Patient

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Patient)
def delete_old_profile_photo_on_update(sender, instance, **kwargs):
    """
    Delete old profile photo file when a new one is uploaded.
    
    This signal fires before saving a Patient instance. If the profile_photo
    field is being changed, the old file is deleted from storage.
    
    Requirements: 10.1, 10.4, 10.5
    """
    if not instance.pk:
        # New instance, no old photo to delete
        return
    
    try:
        old_instance = Patient.objects.get(pk=instance.pk)
    except Patient.DoesNotExist:
        # Instance doesn't exist yet, nothing to delete
        return
    
    # Check if profile_photo field is being changed
    old_photo = old_instance.profile_photo
    new_photo = instance.profile_photo
    
    # If old photo exists and is different from new photo, delete it
    if old_photo and old_photo != new_photo:
        try:
            # Delete the file from storage
            old_photo.delete(save=False)
            logger.info(f"Deleted old profile photo: {old_photo.name}")
        except Exception as e:
            # Log error but don't prevent save operation
            logger.error(f"Failed to delete old profile photo {old_photo.name}: {e}")


@receiver(post_delete, sender=Patient)
def delete_profile_photo_on_patient_delete(sender, instance, **kwargs):
    """
    Delete profile photo file when Patient instance is deleted.
    
    This signal fires after a Patient instance is deleted. It removes the
    associated profile photo file from storage.
    
    Requirements: 10.3, 10.4, 10.5
    """
    if instance.profile_photo:
        try:
            # Delete the file from storage
            instance.profile_photo.delete(save=False)
            logger.info(f"Deleted profile photo on patient deletion: {instance.profile_photo.name}")
        except Exception as e:
            # Log error but don't prevent deletion
            logger.error(f"Failed to delete profile photo {instance.profile_photo.name}: {e}")
