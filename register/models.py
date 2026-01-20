from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
# Create your models here.

class Client(models.Model):

	firstname = models.CharField(max_length=30)
	lastname = models.CharField(max_length=30)

	# Status as a simple text field (adjust max_length as needed)
	status = models.CharField(max_length=50)

	# Email field; enforce uniqueness for clients
	email = models.EmailField(blank=True)

class Product(models.Model):
	# Product name
	name = models.CharField(max_length=100)

	# Price with two decimal places
	price = models.DecimalField(max_digits=10, decimal_places=2)

	# Available quantity
	quantity = models.PositiveIntegerField()

class Operation(models.Model):
	# Type as plain string (not enum)
	type = models.CharField(max_length=100)

	# Sum can be negative
	sum = models.DecimalField(max_digits=12, decimal_places=2)

	# Optional relations to Client and Product
	client = models.ForeignKey("Client", null=True, blank=True, on_delete=models.SET_NULL)
	product = models.ForeignKey("Product", null=True, blank=True, on_delete=models.SET_NULL)
	isDebt = models.BooleanField(default=False)
	# Optional quantity and comments
	quantity = models.IntegerField(null=True, blank=True)
	comments = models.TextField(null=True, blank=True)
	created_at = models.DateTimeField()
	# Author - the user who created this operation
	author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='operations')

class CurrentBalance(models.Model):
	amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
	debt = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

class OperationType(models.Model):
    name = models.CharField(max_length=100, unique=True)


class OperationChange(models.Model):
    """Tracks all changes made to existing operations."""
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='changes')
    initially_created = models.DateTimeField()
    edited_at = models.DateTimeField(auto_now_add=True)
    original_author = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='original_operations_changed'
    )
    edited_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='operation_edits'
    )
    changes = models.TextField()  # Format: "column_name:'Original value'->'New value';..."

    class Meta:
        ordering = ['-edited_at']
	