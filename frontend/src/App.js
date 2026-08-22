import { useEffect, useState, useRef } from "react";
import axios from "axios";
import { Routes, Route } from "react-router-dom";
import { BookOpen, Compass, GraduationCap, Heart, Home, ImagePlus, Linkedin, LogIn, MessageCircle, MessageSquare, Plus, Search, Send, Shield, Sparkles, UserRound, Users, X, Building2 } from "lucide-react";
import "@/App.css";

const api = axios.create({ baseURL: `${process.env.REACT_APP_BACKEND_URL}/api`, withCredentials: true });

const founderData = [
  { name: "Oindrila", role: "Co-Founder", email: "oindrila@nsec.edu", linkedin: "https://linkedin.com/in/oindrila", initial: "O" },
  { name: "Arjun Jha", role: "Co-Founder", email: "arjunjha056@nsec.edu", linkedin: "https://linkedin.com/in/arjunjha056", initial: "A" },
];

const fallbackRooms = [
  { id: "academics", title: "Academics & Research", description: "Ideas, papers, labs, and learning resources", members: 128 },
  { id: "placements", title: "Placements & Careers", description: "Internships, interviews, and opportunities", members: 96 },
  { id: "campus", title: "Campus Life", description: "Clubs, hostel life, events, and everyday NSEC", members: 74 },
];

const formatError = e => {
  const d = e.response?.data?.detail;
  return Array.isArray(d) ? d.map(x => x.msg).join(" ") : d || "Something went wrong. Try again.";
};

// Client-side compression: always compress, never reject. Max 800px width, JPEG q=60.
const compressImage = file => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, 800 / img.width);
      const canvas = document.createElement("canvas");
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
      resolve(canvas.toDataURL("image/jpeg", 0.6));
    };
    img.onerror = reject;
    img.src = reader.result;
  };
  reader.onerror = reject;
  reader.readAsDataURL(file);
});

const timeAgo = iso => {
  if (!iso) return "";
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  if (s < 86400) return `${Math.floor(s / 3600)}h`;
  return `${Math.floor(s / 86400)}d`;
};

function Auth({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "student" });
  const [error, setError] = useState("");
  const submit = async e => {
    e.preventDefault();
    try { onAuth((await api.post(`/auth/${mode}`, form)).data); }
    catch (err) { setError(formatError(err)); }
  };
  return (
    <main className="auth-page">
      <section className="auth-visual">
        <div className="brand-mark"><span>n</span> NSEC / ACADEMIA</div>
        <div>
          <p className="eyebrow">NETAJI SUBHAS ENGINEERING COLLEGE</p>
          <h1>Where campus<br/><em>thinking</em> connects.</h1>
          <p className="hero-note">A private academic network for ideas, people, and the work happening at NSEC.</p>
        </div>
        <div className="campus-strip">
          <img src="https://images.unsplash.com/photo-1591123120675-6f7f1aae0e5b?crop=entropy&cs=srgb&fm=jpg&q=85" alt="Campus"/>
          <span>Explore the people behind the progress →</span>
        </div>
      </section>
      <section className="auth-panel">
        <div className="auth-box">
          <p className="eyebrow">{mode === "login" ? "WELCOME BACK" : "JOIN THE NETWORK"}</p>
          <h2>{mode === "login" ? "Sign in to your campus." : "Create your campus profile."}</h2>
          <p className="muted">Connect with classmates, teachers, and ideas.</p>
          {error && <div className="error" data-testid="auth-error">{error}</div>}
          <form onSubmit={submit} data-testid="auth-form">
            {mode === "register" && <input data-testid="register-name-input" placeholder="Full name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required/>}
            <input data-testid="auth-email-input" type="email" placeholder="College email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required/>
            <input data-testid="auth-password-input" type="password" placeholder="Password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required/>
            {mode === "register" && <select data-testid="role-select" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}><option value="student">Student</option><option value="teacher">Teacher</option><option value="founder">Founder / Admin</option></select>}
            <button className="primary-btn" data-testid="auth-submit-button">{mode === "login" ? "Enter NSEC" : "Create profile"} <LogIn size={17}/></button>
          </form>
          <button className="google-btn" data-testid="google-login-button" onClick={() => setError("Google login is ready for OAuth configuration by an administrator.")}>G <span>Continue with Google</span></button>
          <button className="text-btn" data-testid="auth-mode-toggle" onClick={() => setMode(mode === "login" ? "register" : "login")}>{mode === "login" ? "New to NSEC? Create an account" : "Already have an account? Sign in"}</button>
          <button className="access-link" data-testid="access-issue-button" onClick={() => setError("For access issues, contact the NSEC founders from the Info section.")}>Having trouble accessing your account?</button>
        </div>
      </section>
    </main>
  );
}

function StoryComposer({ onClose, onSaved }) {
  const [image, setImage] = useState("");
  const [caption, setCaption] = useState("");
  const [busy, setBusy] = useState(false);
  const file = async e => { if (e.target.files[0]) setImage(await compressImage(e.target.files[0])); };
  const submit = async () => {
    if (!image) return;
    setBusy(true);
    try { await api.post("/stories", { image, caption }); onSaved(); onClose(); }
    finally { setBusy(false); }
  };
  return (
    <div className="story-composer" onClick={onClose}>
      <div className="story-composer-box" onClick={e => e.stopPropagation()} data-testid="story-composer">
        <h3>Add to your story</h3>
        <div className="story-composer-preview">
          {image ? <img src={image} alt="Story preview"/> : <span>Choose an image to share</span>}
        </div>
        <label className="attach" style={{ justifySelf: "start" }} data-testid="story-image-label">
          <ImagePlus size={17}/> {image ? "Change image" : "Pick image"}
          <input type="file" accept="image/*" onChange={file} data-testid="story-image-input"/>
        </label>
        <input type="text" placeholder="Add a caption (optional)" value={caption} onChange={e => setCaption(e.target.value)} data-testid="story-caption-input"/>
        <div className="story-composer-actions">
          <button className="google-btn" style={{ width: "auto" }} onClick={onClose} data-testid="story-cancel-button">Cancel</button>
          <button className="primary-btn" disabled={!image || busy} onClick={submit} data-testid="story-publish-button">{busy ? "Sharing..." : "Share story"} <Send size={16}/></button>
        </div>
      </div>
    </div>
  );
}

function StoryViewer({ group, onClose, onNextGroup, onPrevGroup }) {
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => {
      if (idx < group.stories.length - 1) setIdx(idx + 1);
      else onNextGroup();
    }, 5000);
    return () => clearTimeout(t);
  }, [idx, group, onNextGroup]);
  const current = group.stories[idx];
  const back = () => { if (idx > 0) setIdx(idx - 1); else onPrevGroup(); };
  const next = () => { if (idx < group.stories.length - 1) setIdx(idx + 1); else onNextGroup(); };
  return (
    <div className="story-modal" onClick={onClose}>
      <div className="story-frame" onClick={e => e.stopPropagation()} data-testid="story-viewer">
        <div className="story-progress">
          {group.stories.map((_, i) => <span key={i} className={i < idx ? "done" : i === idx ? "active" : ""}/>)}
        </div>
        <div className="story-header">
          <div className="avatar small" data-testid="story-header-avatar">
            {group.avatar ? <img src={group.avatar} alt=""/> : group.author[0]}
          </div>
          <div>
            <div className="story-header-name">{group.author}</div>
            <div className="story-header-time">{timeAgo(current.created_at)} ago · {group.role}</div>
          </div>
          <button className="story-close" onClick={onClose} data-testid="story-close-button"><X size={22}/></button>
        </div>
        <button className="story-nav left" onClick={back} data-testid="story-back-button"/>
        <button className="story-nav right" onClick={next} data-testid="story-next-button"/>
        <img src={current.image} alt="Story"/>
        {current.caption && <div className="story-caption">{current.caption}</div>}
      </div>
    </div>
  );
}

function StoriesBar({ user, groups, onRefresh }) {
  const [composing, setComposing] = useState(false);
  const [viewingIdx, setViewingIdx] = useState(null);
  const myGroup = groups.find(g => g.author_id === user.id);
  const others = groups.filter(g => g.author_id !== user.id);
  const ordered = [myGroup, ...others].filter(Boolean);
  return (
    <>
      <div className="stories-bar" data-testid="stories-bar">
        <button className="story-item" onClick={() => setComposing(true)} data-testid="story-add-button">
          <div className="story-ring story-add">
            <div className="story-inner"><div className="story-avatar" style={{ background: "var(--card-2)", color: "var(--blue)" }}><Plus size={26}/></div></div>
          </div>
          <span className="story-name">Your story</span>
        </button>
        {ordered.map((g, i) => (
          <button key={g.author_id} className="story-item" onClick={() => setViewingIdx(i)} data-testid={`story-open-${g.author_id}`}>
            <div className="story-ring">
              <div className="story-inner">
                <div className="story-avatar">{g.avatar ? <img src={g.avatar} alt=""/> : g.author[0]}</div>
              </div>
            </div>
            <span className="story-name">{g.author_id === user.id ? "You" : g.author.split(" ")[0]}</span>
          </button>
        ))}
      </div>
      {composing && <StoryComposer onClose={() => setComposing(false)} onSaved={onRefresh}/>}
      {viewingIdx !== null && ordered[viewingIdx] && (
        <StoryViewer
          group={ordered[viewingIdx]}
          onClose={() => setViewingIdx(null)}
          onNextGroup={() => setViewingIdx(viewingIdx + 1 < ordered.length ? viewingIdx + 1 : null)}
          onPrevGroup={() => setViewingIdx(viewingIdx > 0 ? viewingIdx - 1 : viewingIdx)}
        />
      )}
    </>
  );
}

function FeedPost({ post, user, onChanged }) {
  const [liked, setLiked] = useState((post.liked_by || []).includes(user.id));
  const [count, setCount] = useState(post.like_count || 0);
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [commentBody, setCommentBody] = useState("");
  const [cCount, setCCount] = useState(post.comment_count || 0);

  const toggleLike = async () => {
    const r = await api.post(`/feed/${post.id}/like`);
    setLiked((r.data.liked_by || []).includes(user.id));
    setCount(r.data.like_count);
  };
  const openComments = async () => {
    setShowComments(!showComments);
    if (!showComments) {
      const r = await api.get(`/feed/${post.id}/comments`);
      setComments(r.data);
    }
  };
  const submitComment = async e => {
    e.preventDefault();
    if (!commentBody.trim()) return;
    const r = await api.post(`/feed/${post.id}/comments`, { body: commentBody });
    setComments([...comments, r.data]);
    setCommentBody("");
    setCCount(cCount + 1);
  };

  return (
    <article className="post" data-testid="feed-post">
      <div className="post-top">
        <div className="avatar small">{post.avatar ? <img src={post.avatar} alt=""/> : post.author[0]}</div>
        <div>
          <strong>{post.author}</strong>
          <small>{post.role} · {timeAgo(post.created_at)} ago</small>
        </div>
      </div>
      <p>{post.body}</p>
      {post.image && <img className="post-image" src={post.image} alt="Post attachment"/>}
      <div className="post-actions">
        <button className={liked ? "post-action liked" : "post-action"} onClick={toggleLike} data-testid={`like-button-${post.id}`}>
          <Heart size={17}/> {count > 0 ? count : ""} Like
        </button>
        <button className="post-action" onClick={openComments} data-testid={`comment-toggle-${post.id}`}>
          <MessageCircle size={17}/> {cCount > 0 ? cCount : ""} Comment
        </button>
      </div>
      {showComments && (
        <>
          <div className="comments-list" data-testid={`comments-list-${post.id}`}>
            {comments.length === 0 && <div className="muted" style={{ fontSize: 13 }}>No comments yet. Be the first.</div>}
            {comments.map(c => (
              <div className="comment" key={c.id} data-testid="comment-item">
                <div className="avatar small">{c.avatar ? <img src={c.avatar} alt=""/> : c.author[0]}</div>
                <div className="comment-bubble">
                  <strong>{c.author} <span style={{ color: "var(--muted)", fontWeight: 400, fontSize: 11, marginLeft: 6 }}>{timeAgo(c.created_at)} ago</span></strong>
                  <p>{c.body}</p>
                </div>
              </div>
            ))}
          </div>
          <form className="comment-form" onSubmit={submitComment} data-testid={`comment-form-${post.id}`}>
            <input placeholder="Write a comment..." value={commentBody} onChange={e => setCommentBody(e.target.value)} data-testid={`comment-input-${post.id}`}/>
            <button type="submit" data-testid={`comment-submit-${post.id}`}><Send size={14}/></button>
          </form>
        </>
      )}
    </article>
  );
}

function TeacherComposer({ onSaved }) {
  const [topic, setTopic] = useState("");
  const [details, setDetails] = useState("");
  const [image, setImage] = useState("");
  const file = async e => { if (e.target.files[0]) setImage(await compressImage(e.target.files[0])); };
  const submit = async e => {
    e.preventDefault();
    await api.post("/teacher-updates", { topic, details: image ? `${details}\n\n[IMG]${image}` : details });
    setTopic(""); setDetails(""); setImage(""); onSaved();
  };
  return (
    <form className="teacher-form" onSubmit={submit} data-testid="teacher-update-form">
      <input data-testid="teacher-topic-input" placeholder="Today's topic" value={topic} onChange={e => setTopic(e.target.value)} required/>
      <textarea data-testid="teacher-details-input" placeholder="What did you teach today?" value={details} onChange={e => setDetails(e.target.value)} required/>
      {image && <img src={image} alt="Preview" style={{ maxWidth: 220, borderRadius: 8 }}/>}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <label className="attach" data-testid="teacher-image-label">
          <ImagePlus size={17}/> {image ? "Change photo" : "Attach whiteboard/notes"}
          <input type="file" accept="image/*" onChange={file} data-testid="teacher-image-input"/>
        </label>
        <button className="primary-btn compact" data-testid="teacher-update-submit-button">Publish teaching note <Plus size={16}/></button>
      </div>
    </form>
  );
}

function Section({ title, eyebrow, intro, children, accent }) {
  return (
    <div className={accent ? `section-accent accent-${accent}` : ""}>
      <div className="page-head section-head">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="muted intro">{intro}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

function RoomView({ rooms }) {
  const [selected, setSelected] = useState(rooms[0]?.id);
  const [posts, setPosts] = useState([]);
  const [body, setBody] = useState("");
  const [replyTo, setReplyTo] = useState(null);
  useEffect(() => { if (selected) api.get(`/rooms/${selected}/posts`).then(r => setPosts(r.data)).catch(() => {}); }, [selected]);
  const publish = async e => {
    e.preventDefault();
    if (!body.trim()) return;
    await api.post(`/rooms/${selected}/posts`, { body, parent_id: replyTo });
    setBody(""); setReplyTo(null);
    const r = await api.get(`/rooms/${selected}/posts`);
    setPosts(r.data);
  };
  const react = async id => {
    const r = await api.post(`/rooms/${selected}/posts/${id}/react`);
    setPosts(posts.map(p => p.id === id ? r.data : p));
  };
  return (
    <Section accent="red" title="Discussion rooms" eyebrow="OPEN CONVERSATIONS · REDDIT-STYLE" intro="Choose a room, share a thought, and build on the ideas already moving through NSEC.">
      <div className="room-layout">
        <div className="room-list">
          {rooms.map(r => (
            <button key={r.id} className={selected === r.id ? "room-select active" : "room-select"} data-testid={`room-select-${r.id}`} onClick={() => setSelected(r.id)}>
              <strong>{r.title}</strong>
              <small>{r.members} members</small>
            </button>
          ))}
        </div>
        <div className="conversation">
          <div className="conversation-head">
            <MessageSquare size={19}/>
            <strong>{rooms.find(r => r.id === selected)?.title}</strong>
          </div>
          <div className="conversation-posts">
            {posts.length ? posts.map(p => (
              <article className={p.parent_id ? "room-post reply" : "room-post"} key={p.id} data-testid="room-post">
                <div className="post-top">
                  <div className="avatar small">{p.author[0]}</div>
                  <div><strong>{p.author}</strong><small>{p.role}</small></div>
                </div>
                <p>{p.body}</p>
                <div className="room-actions">
                  <button data-testid={`room-react-${p.id}`} onClick={() => react(p.id)}>▲ {p.reactions?.thoughtful || 0}</button>
                  <button data-testid={`room-reply-${p.id}`} onClick={() => setReplyTo(p.id)}>Reply</button>
                </div>
              </article>
            )) : <div className="empty">Start this room's first conversation.</div>}
          </div>
          <form className="room-composer" onSubmit={publish} data-testid="room-composer">
            {replyTo && <div className="replying">Replying to a discussion <button type="button" data-testid="cancel-reply-button" onClick={() => setReplyTo(null)}><X size={14}/></button></div>}
            <textarea data-testid="room-post-input" placeholder="Add to the conversation..." value={body} onChange={e => setBody(e.target.value)} required/>
            <button className="primary-btn compact" data-testid="room-post-submit-button">Post to room <Plus size={16}/></button>
          </form>
        </div>
      </div>
    </Section>
  );
}

function ProfileView({ user, onSaved }) {
  const [form, setForm] = useState({ ...user, interests: (user.interests || []).join(", ") });
  const [message, setMessage] = useState("");
  const file = async e => { if (e.target.files[0]) setForm({ ...form, avatar: await compressImage(e.target.files[0]) }); };
  const submit = async e => {
    e.preventDefault();
    const payload = { ...form, interests: form.interests.split(",").map(x => x.trim()).filter(Boolean) };
    const r = await api.put("/profile", payload);
    onSaved(r.data);
    setMessage("Profile saved");
    setTimeout(() => setMessage(""), 2500);
  };
  return (
    <Section title="Your academic profile" eyebrow="PROFILE / EDIT" intro="Make it easier for the right people to find your work and interests.">
      <form className="profile-form" onSubmit={submit} data-testid="profile-form">
        <div className="profile-edit-top">
          <div className="avatar profile-avatar">{form.avatar ? <img src={form.avatar} alt="Profile preview"/> : form.name?.[0]}</div>
          <label className="attach" data-testid="profile-image-label">
            <ImagePlus size={17}/> Change photo
            <input data-testid="profile-image-input" type="file" accept="image/*" onChange={file}/>
          </label>
        </div>
        <div className="profile-fields">
          <label>Full name<input data-testid="profile-name-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}/></label>
          <label>Headline<input data-testid="profile-headline-input" placeholder="e.g. Computer science student" value={form.headline} onChange={e => setForm({ ...form, headline: e.target.value })}/></label>
          <label>Department<input data-testid="profile-department-input" placeholder="e.g. Information Technology" value={form.department} onChange={e => setForm({ ...form, department: e.target.value })}/></label>
          <label>Relationship status<select data-testid="profile-relationship-input" value={form.relationship} onChange={e => setForm({ ...form, relationship: e.target.value })}><option>Single</option><option>In a relationship</option><option>Prefer not to say</option></select></label>
          <label>Academic interests<input data-testid="profile-interests-input" placeholder="AI, robotics, design" value={form.interests} onChange={e => setForm({ ...form, interests: e.target.value })}/></label>
          <label>Biography<textarea data-testid="profile-bio-input" value={form.bio} onChange={e => setForm({ ...form, bio: e.target.value })}/></label>
        </div>
        {message && <div className="saved" data-testid="profile-saved-message">{message}</div>}
        <button className="primary-btn" data-testid="profile-save-button">Save profile</button>
      </form>
    </Section>
  );
}

function Discovery() {
  const [q, setQ] = useState("");
  const [data, setData] = useState({ people: [], rooms: [], updates: [] });
  const search = async e => {
    e.preventDefault();
    setData((await api.get("/discover", { params: { q } })).data);
  };
  return (
    <Section title="Find your campus" eyebrow="DISCOVERY / NSEC" intro="Search people, discussion rooms, and teaching notes across the community.">
      <form className="discover-search" onSubmit={search}>
        <Search size={18}/>
        <input data-testid="discovery-search-input" placeholder="Search people, departments, rooms..." value={q} onChange={e => setQ(e.target.value)}/>
        <button className="primary-btn compact" data-testid="discovery-search-button">Search</button>
      </form>
      <div className="discover-grid">
        <div>
          <h3>People</h3>
          {data.people.map(p => (
            <article className="result" key={p.id} data-testid="person-result">
              <div className="avatar small">{p.avatar ? <img src={p.avatar} alt=""/> : p.name[0]}</div>
              <div>
                <strong>{p.name}</strong>
                <small>{p.role} · {p.department || "NSEC community"}</small>
                <p>{p.headline || p.bio || "Open to campus conversations"}</p>
              </div>
            </article>
          ))}
        </div>
        <div>
          <h3>Rooms & notes</h3>
          {[...data.rooms.map(r => ({ ...r, type: "Room" })), ...data.updates.map(u => ({ ...u, title: u.topic, type: "Teacher note" }))].map((x, i) => (
            <article className="result compact-result" key={x.id || i} data-testid="discovery-result">
              <div><small>{x.type}</small><strong>{x.title}</strong><p>{x.description || x.details}</p></div>
            </article>
          ))}
        </div>
      </div>
    </Section>
  );
}

function DirectoryView() {
  const [people, setPeople] = useState([]);
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");
  useEffect(() => { api.get("/discover").then(r => setPeople(r.data.people)); }, []);
  const filtered = people.filter(p => (filter === "all" || p.role === filter) && (!q || (p.name + " " + (p.department || "") + " " + (p.headline || "")).toLowerCase().includes(q.toLowerCase())));
  const counts = { all: people.length, student: people.filter(p => p.role === "student").length, teacher: people.filter(p => p.role === "teacher").length, founder: people.filter(p => p.role === "founder").length };
  return (
    <Section title="NSEC Directory" eyebrow="COLLEGE DIRECTORY / EVERYONE AT NSEC" intro="Track every member studying, teaching, or building at Netaji Subhas Engineering College.">
      <div className="directory-filters" data-testid="directory-filters">
        <button className={filter === "all" ? "chip active" : "chip"} onClick={() => setFilter("all")} data-testid="dir-filter-all">All <span>{counts.all}</span></button>
        <button className={filter === "student" ? "chip active" : "chip"} onClick={() => setFilter("student")} data-testid="dir-filter-student">Students <span>{counts.student}</span></button>
        <button className={filter === "teacher" ? "chip active" : "chip"} onClick={() => setFilter("teacher")} data-testid="dir-filter-teacher">Teachers <span>{counts.teacher}</span></button>
        <button className={filter === "founder" ? "chip active" : "chip"} onClick={() => setFilter("founder")} data-testid="dir-filter-founder">Founders <span>{counts.founder}</span></button>
        <div className="directory-search"><Search size={16}/><input placeholder="Search name, department..." value={q} onChange={e => setQ(e.target.value)} data-testid="directory-search-input"/></div>
      </div>
      <div className="directory-grid">
        {filtered.map(p => (
          <article className="directory-card" key={p.id} data-testid="directory-card">
            <div className="avatar directory-avatar">{p.avatar ? <img src={p.avatar} alt=""/> : p.name[0]}</div>
            <div className="directory-info">
              <strong>{p.name}</strong>
              <span className={`role-badge role-${p.role}`}>{p.role}</span>
              <small>{p.department || "NSEC · Department not set"}</small>
              <p>{p.headline || p.bio || "—"}</p>
              <div className="directory-meta"><Building2 size={12}/> NSEC · Kolkata</div>
            </div>
          </article>
        ))}
        {filtered.length === 0 && <div className="empty">No members match this filter yet.</div>}
      </div>
    </Section>
  );
}

function Shell({ user, onLogout, onUserChange }) {
  const [active, setActive] = useState("feed");
  const [posts, setPosts] = useState([]);
  const [rooms, setRooms] = useState(fallbackRooms);
  const [updates, setUpdates] = useState([]);
  const [storyGroups, setStoryGroups] = useState([]);
  const [body, setBody] = useState("");
  const [image, setImage] = useState("");

  const refresh = () => {
    api.get("/feed").then(r => setPosts(r.data));
    api.get("/rooms").then(r => setRooms(r.data));
    api.get("/teacher-updates").then(r => setUpdates(r.data));
    api.get("/stories").then(r => setStoryGroups(r.data));
  };
  useEffect(refresh, []);

  const publish = async e => {
    e.preventDefault();
    if (!body.trim()) return;
    await api.post("/feed", { body, image });
    setBody(""); setImage(""); refresh();
  };
  const file = async e => { if (e.target.files[0]) setImage(await compressImage(e.target.files[0])); };

  const nav = [
    ["feed", "Feed", Home],
    ["rooms", "Discussion rooms", MessageSquare],
    ["directory", "NSEC directory", Users],
    ["teachers", "Teacher updates", GraduationCap],
    ["discover", "Discover", Compass],
    ["profile", "My profile", UserRound],
    ["info", "Info & founders", Sparkles],
  ];

  const parseTeacherUpdate = details => {
    const idx = details.indexOf("\n\n[IMG]");
    if (idx === -1) return { text: details, image: null };
    return { text: details.slice(0, idx), image: details.slice(idx + 7) };
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-mark"><span>n</span> NSEC / ACADEMIA</div>
        <div className="top-actions">
          <span className="role-chip"><span className="online-dot"/> {user.role}</span>
          <button data-testid="logout-button" className="icon-btn" onClick={onLogout}><X size={18}/></button>
        </div>
      </header>
      <div className="layout">
        <aside className="sidebar">
          <div className="profile-mini">
            <div className="avatar">{user.avatar ? <img src={user.avatar} alt=""/> : user.name[0]}</div>
            <strong data-testid="current-user-name">{user.name}</strong>
            <small>{user.email}</small>
            <span>{user.relationship}</span>
          </div>
          <nav>
            {nav.map(([id, label, Icon]) => (
              <button key={id} data-testid={`nav-${id}-button`} className={active === id ? "nav-item active" : "nav-item"} onClick={() => setActive(id)}>
                <Icon size={18}/>{label}
              </button>
            ))}
          </nav>
          <div className="sidebar-foot"><Shield size={16}/><span>Private NSEC community</span></div>
        </aside>
        <main className="content">
          {active === "feed" && (
            <div className="section-accent accent-blue">
              <div className="page-head">
                <div>
                  <p className="eyebrow">NSEC FEED · FACEBOOK-STYLE</p>
                  <h1>Good day, {user.name.split(" ")[0]}.</h1>
                </div>
              </div>
              <StoriesBar user={user} groups={storyGroups} onRefresh={refresh}/>
              <form className="composer" onSubmit={publish} data-testid="post-composer">
                <div className="avatar small">{user.avatar ? <img src={user.avatar} alt=""/> : user.name[0]}</div>
                <textarea data-testid="post-body-input" placeholder="Share an idea, question, or small win..." value={body} onChange={e => setBody(e.target.value)}/>
                {image && <img className="post-image image-preview" src={image} alt="Selected preview" style={{ maxWidth: 260 }}/>}
                <div className="composer-actions">
                  <label className="attach" data-testid="image-upload-label">
                    <ImagePlus size={17}/> Add image
                    <input data-testid="image-upload-input" type="file" accept="image/*" onChange={file}/>
                  </label>
                  <button className="primary-btn compact" data-testid="publish-post-button">Publish <Plus size={16}/></button>
                </div>
              </form>
              <div className="feed-list">
                {posts.length === 0 && <div className="empty">Be the first to share something with NSEC today.</div>}
                {posts.map(p => <FeedPost key={p.id} post={p} user={user} onChanged={refresh}/>)}
              </div>
            </div>
          )}
          {active === "rooms" && <RoomView rooms={rooms}/>}
          {active === "directory" && <DirectoryView/>}
          {active === "teachers" && (
            <Section title="Teacher updates" eyebrow="WHAT WAS TAUGHT TODAY" intro="Daily notes from the people guiding the next generation of builders.">
              {(user.role === "teacher" || user.role === "founder") && <TeacherComposer onSaved={refresh}/>}
              <div className="updates">
                {updates.map(u => {
                  const parsed = parseTeacherUpdate(u.details);
                  return (
                    <article className="update" key={u.id} data-testid="teacher-update">
                      <div className="date-tag">TODAY</div>
                      <div style={{ flex: 1 }}>
                        <strong>{u.topic}</strong>
                        <p>{parsed.text}</p>
                        {parsed.image && <img src={parsed.image} alt="Teacher note" style={{ maxWidth: "100%", borderRadius: 8, marginTop: 10 }}/>}
                        <small>Shared by {u.teacher}</small>
                      </div>
                    </article>
                  );
                })}
                {updates.length === 0 && <div className="empty">No teaching notes yet.</div>}
              </div>
            </Section>
          )}
          {active === "discover" && <Discovery/>}
          {active === "profile" && <ProfileView user={user} onSaved={u => { onUserChange(u); }}/>}
          {active === "info" && (
            <Section title="The people behind NSEC Academia" eyebrow="INFO / ACCESS SUPPORT" intro="A shared space for the NSEC community, shaped by its founders.">
              <div className="founder-grid">
                {founderData.map(f => (
                  <article className="founder" key={f.name} data-testid="founder-card">
                    <div className="founder-photo">{f.initial}</div>
                    <div>
                      <p className="eyebrow">{f.role.toUpperCase()}</p>
                      <h3>{f.name}</h3>
                      <p className="muted">{f.email}</p>
                      <p className="linkedin"><Linkedin size={13} style={{ verticalAlign: "middle", marginRight: 4 }}/> <a href={f.linkedin} target="_blank" rel="noreferrer">{f.linkedin.replace("https://", "")}</a></p>
                    </div>
                  </article>
                ))}
              </div>
              <div className="access-note">
                <BookOpen size={22}/>
                <div>
                  <strong>Need help getting access?</strong>
                  <p>Use your college email when registering. For account issues, reach out to a founder above.</p>
                </div>
              </div>
            </Section>
          )}
        </main>
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    api.get("/auth/me").then(r => setUser(r.data)).catch(() => {}).finally(() => setChecking(false));
  }, []);
  if (checking) return <div className="loading" data-testid="loading-state">Loading NSEC Academia…</div>;
  return user
    ? <Shell user={user} onLogout={async () => { await api.post("/auth/logout"); setUser(null); }} onUserChange={u => setUser(u)}/>
    : <Auth onAuth={setUser}/>;
}

export default function RoutedApp() {
  return <Routes><Route path="*" element={<App/>}/></Routes>;
}
