# NSEC Academia Network - PRD

## Original Problem
Facebook/LinkedIn/Reddit-style academic social network for NSEC (Netaji Subhas Engineering College) students, teachers and founders.

## Implemented (through Feb 2026)
- Auth: register/login/logout, JWT refresh, password recovery, admin seed
- Dark theme (near-black bg)
- Feed with Facebook-blue accent (posts, likes toggle, comments, image compression 800px/JPEG 60)
- Discussion Rooms with Reddit-red accent (rooms, replies, upvotes)
- Instagram-style Stories (24h expiry, ring gradient, viewer, composer)
- NSEC Directory (role filters: all/student/teacher/founder + search)
- Teacher Updates (with image attachment)
- Profile edit (avatar upload, relationship, department, bio, headline, interests)
- Founders section: Oindrila + Arjun Jha (email + LinkedIn)
- Discover (search people/rooms/notes)
- Client-side JS image compression (max 800px, JPEG q=60, never rejects)

## Personas
- Student, Teacher, Founder/Admin

## Backlog (P1)
- Gmail OTP email verification (needs SMTP or Resend creds)
- Real photo/LinkedIn URLs for founders
- Teacher PDF upload support
- Real Google OAuth wiring
- Story delete + view counts

## Key Files
- /app/backend/server.py (FastAPI + Mongo)
- /app/frontend/src/App.js (all React views)
- /app/frontend/src/App.css (dark theme + section accents)
