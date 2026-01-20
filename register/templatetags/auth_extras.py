from django import template

register = template.Library()


@register.filter(name='is_admin')
def is_admin(user):
    """Check if user is in the 'admins' group or is a superuser."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name='admins').exists()
