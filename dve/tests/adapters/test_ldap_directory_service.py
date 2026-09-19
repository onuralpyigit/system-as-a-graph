"""The mock LDAP directory service's fixed users (SRS DSM-DVE req 3)."""

from fakes import seed
from dve.adapters.ldap_directory_service import LdapDirectoryService
from dve.domain.user import Role, User


def test_known_users_authenticate_with_their_role():
    service = LdapDirectoryService()

    assert service.authenticate(seed.ADMIN, seed.ADMIN) == User(seed.ADMIN, Role.ADMIN)
    assert service.authenticate(seed.OPERATOR, seed.OPERATOR) == User(seed.OPERATOR, Role.OPERATOR)


def test_wrong_password_and_unknown_user_are_refused_alike():
    service = LdapDirectoryService()

    assert service.authenticate(seed.ADMIN, "wrong") is None
    assert service.authenticate("nobody", seed.ADMIN) is None
