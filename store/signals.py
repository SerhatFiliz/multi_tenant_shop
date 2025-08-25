"""
This file contains Django signal receivers.
Signals are used to allow decoupled applications to get notified when certain
actions occur elsewhere in the framework. Here, we use post_save and post_delete
signals on the ProductVariant model to automatically update the Elasticsearch
index whenever a product is created, updated, or deleted.
"""

# Import the specific signals we want to listen for (post_save, post_delete).
from django.db.models.signals import post_save, post_delete
# Import the 'receiver' decorator, which is our "smoke detector".
from django.dispatch import receiver
# Import the registry from our search library to tell it what to update.
from django_elasticsearch_dsl.registries import registry
# Import the model we want to listen to.
from .models import ProductVariant


# This is the "smoke detector" for when a ProductVariant is saved or created.
@receiver(post_save, sender=ProductVariant)
def update_document(sender, instance, **kwargs):
    """
    Updates the Elasticsearch document whenever a ProductVariant instance is saved.
    
    - @receiver: Decorator that turns this function into a signal handler.
    - post_save: The specific signal to listen for. It fires AFTER a model's .save() method.
    - sender=ProductVariant: Only listen for this signal if it comes from the ProductVariant model.
    
    - instance: This is the actual ProductVariant object that was just saved.
    """
    # This line tells the django-elasticsearch-dsl library:
    # "Take this specific object ('instance') and update it in the Elasticsearch index."
    registry.update(instance)


# This is the "smoke detector" for when a ProductVariant is deleted.
@receiver(post_delete, sender=ProductVariant)
def delete_document(sender, instance, **kwargs):
    """
    Deletes the Elasticsearch document whenever a ProductVariant instance is deleted.
    
    - post_delete: The signal that fires AFTER a model's .delete() method.
    - instance: The object that was just deleted.
    """
    # This line tells the library:
    # "Take this object and delete its corresponding entry from the Elasticsearch index."
    registry.delete(instance)