"""
JWT Authentication Middleware for WebSocket Connections

This module provides ASGI middleware for authenticating and authorizing
WebSocket connections using JWT tokens. It validates tokens passed via
query parameters, resolves user identity, and enforces role-based access
control before allowing connections to proceed to the consumer layer.
"""

import logging
from typing import Optional
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthMiddleware:
    """
    ASGI middleware for JWT authentication on WebSocket connections.
    
    Extracts JWT tokens from query parameters, validates them using
    rest_framework_simplejwt, resolves user identity, and enforces
    role-based authorization before allowing connections to proceed.
    
    Usage:
        application = ProtocolTypeRouter({
            "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
        })
    """
    
    def __init__(self, app):
        """
        Initialize middleware with the next ASGI application in the stack.
        
        Args:
            app: The next ASGI application (typically URLRouter)
        """
        self.app = app
    
    def _extract_token(self, scope) -> Optional[str]:
        """
        Extract JWT token from query string parameter 'token'.
        
        Args:
            scope: ASGI scope containing query_string
            
        Returns:
            Token string if present and non-empty, None otherwise
        """
        # First, try query string param `token`
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token_list = query_params.get('token', [])
        if token_list and token_list[0]:
            return token_list[0]

        # Fallback: try the Authorization header (Bearer <token>) for clients
        # that prefer headers over query params. ASGI scope stores headers
        # as a list of [name, value] byte pairs.
        headers = dict((k.decode('utf-8').lower(), v.decode('utf-8')) for k, v in scope.get('headers', []))
        auth = headers.get('authorization') or headers.get('Authorization')
        if auth:
            parts = auth.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                return parts[1]

        return None
    
    async def _authenticate_user(self, token: str) -> Optional[User]:
        """
        Validate JWT token and retrieve user from database.
        
        Args:
            token: JWT access token string
            
        Returns:
            User object if authentication succeeds, None otherwise
            
        Raises:
            No exceptions (catches all and returns None)
        """
        try:
            # Validate token (checks signature, expiration, etc.)
            access_token = AccessToken(token)
            
            # Extract user ID from token payload
            user_id = access_token['user_id']
            
            # Retrieve user from database (async)
            user = await database_sync_to_async(User.objects.get)(id=user_id)
            
            return user
            
        except TokenError as e:
            logger.info(f"Token validation failed: {e}")
            return None
        except User.DoesNotExist:
            logger.info(f"User not found for token user_id: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}", exc_info=True)
            return None
    
    def _is_authorized_role(self, user: User) -> bool:
        """
        Check if user's role is authorized for WebSocket access.
        
        Args:
            user: Authenticated user object
            
        Returns:
            True if role is authorized, False otherwise
        """
        # All authenticated roles are allowed to connect.
        # Specific event filtering is handled in the consumer layer.
        AUTHORIZED_ROLES = {
            User.Roles.ADMIN,
            User.Roles.DOCTOR,
            User.Roles.NURSE,
            User.Roles.PATIENT,
            'staff',
        }
        
        return user.role in AUTHORIZED_ROLES
        
        return user.role in AUTHORIZED_ROLES
    
    async def _reject_connection(self, send, code: int, reason: str):
        """
        Reject WebSocket connection with specified close code and reason.
        
        Args:
            send: ASGI send callable
            code: WebSocket close code (4001 for auth failure, 4003 for authorization failure)
            reason: Human-readable reason for rejection
        """
        logger.info(f"Rejecting WebSocket connection: {reason} (code: {code})")
        
        await send({
            'type': 'websocket.close',
            'code': code,
            'reason': reason.encode('utf-8')
        })
    
    async def __call__(self, scope, receive, send):
        """
        ASGI application interface. Intercepts WebSocket connections,
        performs authentication/authorization, and either forwards or rejects.
        
        Args:
            scope: ASGI connection scope dictionary
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Only process WebSocket connections, pass through HTTP requests
        if scope['type'] != 'websocket':
            return await self.app(scope, receive, send)
        
        try:
            # Extract JWT token from query parameters
            token = self._extract_token(scope)
            if not token:
                await self._reject_connection(
                    send, 
                    4001, 
                    "Authentication required: JWT token missing from query parameters"
                )
                return
            
            # Authenticate user using JWT token
            user = await self._authenticate_user(token)
            if not user:
                await self._reject_connection(
                    send,
                    4001,
                    "Authentication failed: Invalid or expired JWT token"
                )
                return
            
            # Check role-based authorization
            if not self._is_authorized_role(user):
                await self._reject_connection(
                    send,
                    4003,
                    f"Authorization failed: Role '{user.role}' not authorized for WebSocket access"
                )
                return
            
            # Authentication and authorization successful - attach user to scope
            scope['user'] = user
            logger.info(f"WebSocket connection authorized for user {user.username} (role: {user.role})")
            
            # Forward connection to next ASGI app
            return await self.app(scope, receive, send)
            
        except Exception as e:
            # Catch any unexpected errors to prevent ASGI server crashes
            logger.error(f"Unexpected error in JWT middleware: {e}", exc_info=True)
            await self._reject_connection(
                send,
                4001,
                "Authentication error: Internal server error"
            )
            return
