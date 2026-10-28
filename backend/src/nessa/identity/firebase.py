"""Firebase ID-token verification through the Admin SDK, against the Auth emulator (adapter).

The SDK checks the token's project (audience), issuer and expiry, and with `check_revoked`
asks the emulator whether the account is disabled or its tokens were revoked (spec section
17). Emulator tokens are unsigned (`alg: none`), so this is local-only identity: anyone who
can reach the API could mint one. That is why the configuration refuses anything but a
`demo-` project and a local emulator host, and the API refuses non-loopback hosts and
origins (ADR 0001, ADR 0004). It is not evidence of production identity security.
"""

import firebase_admin
from firebase_admin import auth, exceptions

from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.identity.access import VerifiedIdentity, unauthenticated

_REJECTED = (
    auth.InvalidIdTokenError,
    auth.ExpiredIdTokenError,
    auth.RevokedIdTokenError,
    auth.UserDisabledError,
    auth.UserNotFoundError,
    ValueError,
)


class FirebaseTokenVerifier:
    def __init__(self, project_id: str) -> None:
        name = f"nessa-{project_id}"
        try:
            self._app = firebase_admin.get_app(name)
        except ValueError:
            self._app = firebase_admin.initialize_app(options={"projectId": project_id}, name=name)

    def verify(self, token: str) -> VerifiedIdentity:
        try:
            claims = auth.verify_id_token(token, app=self._app, check_revoked=True)
        except _REJECTED:
            raise unauthenticated() from None
        except exceptions.FirebaseError:
            raise NessaError(
                ErrorCode.AUTH_UNAVAILABLE,
                "The sign-in service did not answer. Try again shortly.",
                stage=ErrorStage.IDENTITY,
                retryable=True,
            ) from None
        email = claims.get("email")
        if claims.get("email_verified") is not True or not isinstance(email, str):
            # Invitations are by email, so an unverified email cannot claim one.
            raise unauthenticated()
        return VerifiedIdentity(
            firebase_uid=str(claims["uid"]), email=email.lower(), expires_at=int(claims["exp"])
        )
