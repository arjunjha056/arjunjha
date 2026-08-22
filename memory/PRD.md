# NSEC Academia Network PRD

## Original problem statement
Build a LinkedIn/Facebook/Reddit-inspired academic social network for Netaji Subhas Engineering College with registration, login, relationship status, picture upload, posts, discussion rooms, teacher daily teaching updates, founder information, access support, and automatic image compression.

## Architecture decisions
- React frontend with React Router and Axios; FastAPI backend with MongoDB through the existing environment values.
- Cookie-based JWT sessions for email/password auth and role-aware users: student, teacher, founder.
- Client-side image compression to 800px maximum width and JPEG quality 60%; images are not rejected by size.
- Founder contact details are intentionally editable placeholders until supplied.

## Personas and core requirements
- Students: create profiles, share academic posts, browse rooms, and see teacher updates.
- Teachers: publish what they taught today.
- Founders/admins: access founder profile and community support information.
- All users: sign up, sign in, sign out, view relationship status, and browse the campus feed.

## Implemented — 2026-02-14
- NSEC-branded auth screen with registration, login, role selection, access issue guidance, and Google OAuth placeholder.
- Authenticated feed with post creation and compressed image attachments.
- Discussion rooms, teacher updates view, founder/info view, responsive navigation, and seeded founder/admin test account.
- FastAPI endpoints for auth, feed, rooms, and teacher updates.

## Prioritized backlog
- P0: Google OAuth credentials and real OAuth callback flow.
- P1: comments, reactions, profile editing, relationship status editing, and room conversations.
- P1: teacher update creation form and founder editing controls.
- P2: cloud object storage for image attachments, notifications, search, and moderation.