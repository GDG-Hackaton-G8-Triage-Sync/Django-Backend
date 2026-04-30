from rest_framework.permissions import BasePermission


class IsDoctor(BasePermission):
    """Permission class for doctor-only endpoints."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_doctor()


class IsNurse(BasePermission):
    """Permission class for nurse-only endpoints."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_nurse()


class IsAdmin(BasePermission):
    """Permission class for admin-only endpoints."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin()


class IsPatient(BasePermission):
    """Permission class for patient-only endpoints."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_patient()


class IsMedicalStaff(BasePermission):
    """Permission class for medical staff (staff, doctor, or nurse) endpoints."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_medical_staff()
        )


class IsStaffOrAdmin(BasePermission):
    """
    Permission class for staff members (nurse, doctor) or admins.
    Used for triage submissions history with email filtering.
    
    Requirements: 2.2, 2.3, 7.2
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.is_medical_staff() or request.user.is_admin())
        )
