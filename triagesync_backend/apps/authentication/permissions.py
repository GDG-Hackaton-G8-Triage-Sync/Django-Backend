from rest_framework.permissions import BasePermission

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'doctor'

class IsNurse(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_nurse()

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsMedicalStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.is_doctor() or request.user.is_nurse())
        )


class IsPatient(BasePermission):
    """Permission class for patient-only endpoints."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'patient'

class IsStaff(BasePermission):
    """Permission class for staff endpoints (nurse or doctor)."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['nurse', 'doctor', 'staff']
        )
