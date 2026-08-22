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
- Founders section: Oindrila Maity + Arjun Jha (real LinkedIn URLs, gmails, Arjun's AI-edited photo, June 2026)
- Story emoji reactions (❤️🔥👏😂😮 toggle/switch) + trending "Most active this week" strip in directory (tested, iteration_3: 20/20 backend)
- Story views: view tracking (deduped, author-only viewer list, "Viewed by N" panel, pauses auto-advance)
- Teacher section roster: 5 NSEC faculty/staff + 80 community members (alphabetical, initial avatars)
- Discover (search people/rooms/notes)
- Client-side JS image compression (max 800px, JPEG q=60, never rejects)

## Personas
- Student, Teacher, Founder/Admin

## Backlog (P1)
- Gmail OTP email verification (needs SMTP or Resend creds)
- Real photo for Oindrila (Arjun's done)
- Roster: swap initial avatars for real photos when user supplies them (NSEC site has none)
- Auth hardening (testing agent flagged): brute-force lockout, explicit CORS origins, idempotent admin seed — use integration_expert before changing
- Teacher PDF upload support
- Real Google OAuth wiring
- Story delete + view counts

## Key Files
- /app/backend/server.py (FastAPI + Mongo)
- /app/frontend/src/App.js (all React views)
- /app/frontend/src/App.css (dark theme + section accents)
