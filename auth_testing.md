# NSEC Academia auth testing

1. POST `/api/auth/register` with name, email, password, and role.
2. POST `/api/auth/login` with email and password; confirm `access_token` cookie.
3. GET `/api/auth/me` with the session cookie; confirm the password is never returned.
4. POST `/api/auth/logout`; confirm protected calls return 401 afterward.

The Google button is an editable configuration placeholder until OAuth credentials are supplied.