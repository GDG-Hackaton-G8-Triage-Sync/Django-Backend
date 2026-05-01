# 📱 TriageSync Flutter Integration Guide

This guide defines standard operating procedures for integrating the TriageSync backend into the frontend Flutter application.

## 1. System Dependencies

Include the following standardized dependencies in your `pubspec.yaml`:

```yaml
dependencies:
    flutter:
        sdk: flutter
    http: ^1.2.0 # Primary HTTP Client
    web_socket_channel: ^3.0.1 # Realtime connections
    shared_preferences: ^2.2.3 # Secure token persistence
    json_annotation: ^4.9.0 # Model serialization
```

## 2. API Configuration Matrix

Establish an `ApiConfig` model in `lib/core/config/api_config.dart`. Ensure you dynamically handle the Local Development IP variance (Android Emulator: `10.0.2.2`, iOS Simulator: `127.0.0.1`).

```dart
class ApiConfig {
  static const String baseUrl = 'http://127.0.0.1:8000/api/v1';
  static const String wsUrl = 'ws://127.0.0.1:8000/ws';

  // State
  static const String login = '$baseUrl/auth/login/';
  static const String refresh = '$baseUrl/auth/refresh/';

  // Services
  static const String submitSymptoms = '$baseUrl/triage/';
  static const String getPatients = '$baseUrl/dashboard/staff/patients/';

  static String updateStatus(int id) => '$baseUrl/dashboard/staff/patient/$id/status/';
}
```

## 3. JWT State Management

Tokens should be securely handled via interceptors. If a `401 Unauthorized` is encountered:

1. Lock standard outbound requests.
2. Fire a request to `ApiConfig.refresh` using the stored refresh token.
3. Upon success, retry the initial failed request with the new access token.
4. If the refresh token fails, forcefully dispatch an unauthenticated state in the app to route the user back to the login screen.
