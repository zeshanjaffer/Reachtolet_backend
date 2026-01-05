from rest_framework import permissions


class IsMediaOwner(permissions.BasePermission):
    """
    Permission check for media owner only actions.
    Only users with user_type='media_owner' can perform these actions.
    """
    message = 'Only media owners can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'media_owner'
        )


class IsBillboardOwner(permissions.BasePermission):
    """
    Permission check for billboard ownership.
    Only the billboard owner (who must be a media_owner) can perform these actions.
    """
    message = 'You can only access your own billboards.'

    def has_object_permission(self, request, view, obj):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'media_owner' and
            obj.user == request.user
        )


