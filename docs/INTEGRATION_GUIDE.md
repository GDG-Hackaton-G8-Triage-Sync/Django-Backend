# Frontend Integration Guide (Flutter)

This guide provides specific implementation patterns for integrating the TriageSync backend into a Flutter mobile application.

## 📦 Recommended Packages

```yaml
dependencies:
  dio: ^5.4.0              # Powerful HTTP client with interceptors
  web_socket_channel: ^2.4.0 # WebSocket handling
  flutter_secure_storage: ^9.0.0 # Securely storing JWTs
  json_annotation: ^4.8.1   # Type-safe model serialization
```

---

## 🔐 JWT Interceptor Logic

Implement an interceptor to handle token refreshing automatically. This ensures a seamless user experience without manual logins.

```dart
class AuthInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // 1. Attempt to refresh token
      // 2. If success, retry the original request
      // 3. If failure, redirect to Login
    }
    return handler.next(err);
  }
}
```

---

## 📡 WebSocket Manager

Use a persistent service to manage the WebSocket connection.

```dart
class WebSocketService {
  WebSocketChannel? _channel;

  void connect(String token) {
    final url = 'ws://api.triagesync.com/ws/triage/events/?token=$token';
    _channel = WebSocketChannel.connect(Uri.parse(url));
    
    _channel!.stream.listen((message) {
      final data = jsonDecode(message);
      _handleEvent(data);
    });
  }
}
```

---

## 🏗️ Data Models

### User Roles
```dart
enum UserRole { patient, nurse, doctor, admin }
```

### Triage Submission
```dart
class TriageItem {
  final int id;
  final String description;
  final int priority;      // 1-5
  final int urgencyScore; // 0-100
  final String status;    // waiting, in_progress, completed
}
```

---

## 🚀 Environment Configuration

Ensure you handle the Local Development IP variance:
- **Android Emulator**: Use `10.0.2.2` instead of `127.0.0.1`.
- **iOS Simulator**: Use `127.0.0.1` or `localhost`.
- **Physical Device**: Use your computer's local network IP (e.g., `192.168.1.5`).
