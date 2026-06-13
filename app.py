"""
RecruitIQ v2 — app.py
AI-Powered Resume Intelligence & Skill Gap Analyzer
Backend: Flask + SQLite + pypdf
"""

import io, re, sqlite3, json, hashlib, os
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request,
                   jsonify, session, redirect, url_for)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "recruitiq-v2-secret-key-2024")
DB = "database.db"

# ═══════════════════════════════════════════
# SKILL CONFIGURATION
# ═══════════════════════════════════════════

SKILLS = [
    "python","java","c","c++","javascript","html","css","react",
    "node","sql","mongodb","ui","ux","figma","testing","api","git",
    "docker","kubernetes","aws","azure","linux","typescript","angular",
    "vue","flutter","swift","kotlin","rust","go"
]

SYNONYMS = {
    "js":"javascript","es6":"javascript","ecmascript":"javascript",
    "ts":"typescript","typescript":"typescript",
    "html5":"html","css3":"css","scss":"css","sass":"css","less":"css",
    "nodejs":"node","node.js":"node","express":"node","expressjs":"node",
    "reactjs":"react","react.js":"react","react native":"react",
    "vuejs":"vue","vue.js":"vue","angularjs":"angular",
    "postgres":"sql","postgresql":"sql","mysql":"sql","sqlite":"sql",
    "mariadb":"sql","mssql":"sql","oracle":"sql",
    "mongo":"mongodb","mongoose":"mongodb",
    "rest":"api","restful":"api","rest api":"api","graphql":"api",
    "github":"git","gitlab":"git","bitbucket":"git","version control":"git",
    "unit testing":"testing","jest":"testing","pytest":"testing",
    "selenium":"testing","cypress":"testing","qa":"testing",
    "user interface":"ui","user experience":"ux",
    "adobe xd":"figma","sketch":"figma","invision":"figma",
    "django":"python","flask":"python","fastapi":"python",
    "pandas":"python","numpy":"python","tensorflow":"python",
    "spring":"java","spring boot":"java","maven":"java","hibernate":"java",
    "k8s":"kubernetes","amazon web services":"aws","gcp":"aws",
    "google cloud":"aws","azure devops":"azure",
}

EDUCATION_KW = [
    "bachelor","master","degree","bsc","btech","mtech","b.tech","m.tech",
    "graduate","university","college","diploma","engineering","phd","mba",
    "postgraduate","undergraduate","b.e","m.e","b.sc","m.sc"
]

EXPERIENCE_KW = [
    "internship","experience","project","worked","company","developed",
    "built","implemented","deployed","collaborated","led","managed",
    "designed","architected","delivered","maintained","created","launched",
    "optimized","integrated","automated","freelance"
]

FRONTEND_SKILLS = {"html","css","javascript","react","angular","vue","ui","ux","figma","typescript"}
BACKEND_SKILLS  = {"python","java","node","sql","mongodb","api","c","c++","go","rust","aws","docker","kubernetes"}

# ── Skill Gap Intelligence ──────────────────
SKILL_INTEL = {
    "python":{"priority":"HIGH","impact":15,"learn":"4–6 weeks","resources":[
        {"label":"Python Official Tutorial","url":"https://docs.python.org/3/tutorial/"},
        {"label":"CS50P – Harvard (Free)","url":"https://cs50.harvard.edu/python/"},
        {"label":"Python Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=rfscVS0vtbw"}]},
    "javascript":{"priority":"HIGH","impact":14,"learn":"4–6 weeks","resources":[
        {"label":"JavaScript.info","url":"https://javascript.info/"},
        {"label":"MDN JavaScript Guide","url":"https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"},
        {"label":"JS Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=PkZNo7MFNFg"}]},
    "react":{"priority":"HIGH","impact":13,"learn":"3–5 weeks","resources":[
        {"label":"React Official Docs","url":"https://react.dev/learn"},
        {"label":"React Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=bMknfKXIFA8"},
        {"label":"Scrimba React Course","url":"https://scrimba.com/learn/learnreact"}]},
    "node":{"priority":"HIGH","impact":13,"learn":"2–4 weeks","resources":[
        {"label":"Node.js Official Docs","url":"https://nodejs.org/en/docs/"},
        {"label":"Node.js Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=Oe421EPjeBE"},
        {"label":"W3Schools Node.js","url":"https://www.w3schools.com/nodejs/"}]},
    "sql":{"priority":"HIGH","impact":12,"learn":"2–3 weeks","resources":[
        {"label":"SQLZoo Interactive","url":"https://sqlzoo.net/"},
        {"label":"SQL Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=HXV3zeQKqGY"},
        {"label":"W3Schools SQL","url":"https://www.w3schools.com/sql/"}]},
    "mongodb":{"priority":"MEDIUM","impact":10,"learn":"1–2 weeks","resources":[
        {"label":"MongoDB University (Free)","url":"https://learn.mongodb.com/"},
        {"label":"MongoDB Crash Course","url":"https://www.youtube.com/watch?v=ofme2o29ngU"},
        {"label":"MongoDB Docs","url":"https://www.mongodb.com/docs/"}]},
    "java":{"priority":"HIGH","impact":13,"learn":"6–8 weeks","resources":[
        {"label":"Java Tutorial – Oracle","url":"https://docs.oracle.com/javase/tutorial/"},
        {"label":"Java Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=grEKMHGYyns"},
        {"label":"MOOC.fi Java Course","url":"https://java-programming.mooc.fi/"}]},
    "html":{"priority":"MEDIUM","impact":8,"learn":"1 week","resources":[
        {"label":"MDN HTML Guide","url":"https://developer.mozilla.org/en-US/docs/Learn/HTML"},
        {"label":"HTML Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=pQN-pnXPaVg"},
        {"label":"W3Schools HTML","url":"https://www.w3schools.com/html/"}]},
    "css":{"priority":"MEDIUM","impact":8,"learn":"1–2 weeks","resources":[
        {"label":"MDN CSS Guide","url":"https://developer.mozilla.org/en-US/docs/Learn/CSS"},
        {"label":"CSS Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=OXGznpKZ_sA"},
        {"label":"CSS-Tricks","url":"https://css-tricks.com/"}]},
    "git":{"priority":"HIGH","impact":10,"learn":"3–5 days","resources":[
        {"label":"Pro Git Book (Free)","url":"https://git-scm.com/book/en/v2"},
        {"label":"Git & GitHub Crash Course","url":"https://www.youtube.com/watch?v=RGOj5yH7evk"},
        {"label":"Learn Git Branching","url":"https://learngitbranching.js.org/"}]},
    "api":{"priority":"HIGH","impact":11,"learn":"1–2 weeks","resources":[
        {"label":"REST API Tutorial","url":"https://restfulapi.net/"},
        {"label":"APIs for Beginners – freeCodeCamp","url":"https://www.youtube.com/watch?v=GZvSYJDk-us"},
        {"label":"Postman Learning Center","url":"https://learning.postman.com/"}]},
    "testing":{"priority":"MEDIUM","impact":9,"learn":"2–3 weeks","resources":[
        {"label":"Pytest Docs","url":"https://docs.pytest.org/"},
        {"label":"Software Testing – freeCodeCamp","url":"https://www.youtube.com/watch?v=u6QfIXgjwGQ"},
        {"label":"Jest Docs","url":"https://jestjs.io/docs/getting-started"}]},
    "docker":{"priority":"HIGH","impact":12,"learn":"2–3 weeks","resources":[
        {"label":"Docker Official Docs","url":"https://docs.docker.com/get-started/"},
        {"label":"Docker Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=fqMOX6JJhGo"},
        {"label":"Play with Docker","url":"https://labs.play-with-docker.com/"}]},
    "aws":{"priority":"HIGH","impact":13,"learn":"4–8 weeks","resources":[
        {"label":"AWS Free Tier","url":"https://aws.amazon.com/free/"},
        {"label":"AWS Training (Free)","url":"https://aws.amazon.com/training/"},
        {"label":"AWS Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=ubCNZFQZZbE"}]},
    "typescript":{"priority":"MEDIUM","impact":10,"learn":"2–3 weeks","resources":[
        {"label":"TypeScript Official Docs","url":"https://www.typescriptlang.org/docs/"},
        {"label":"TypeScript Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=30LWjhZzg50"},
        {"label":"TypeScript Handbook","url":"https://www.typescriptlang.org/docs/handbook/intro.html"}]},
    "figma":{"priority":"LOW","impact":6,"learn":"1–2 weeks","resources":[
        {"label":"Figma Official Tutorials","url":"https://www.figma.com/resources/learn-design/"},
        {"label":"Figma Crash Course","url":"https://www.youtube.com/watch?v=FTFaQWZBqQ8"},
        {"label":"Figma for Beginners","url":"https://www.youtube.com/watch?v=II-6dDzc-80"}]},
    "ui":{"priority":"MEDIUM","impact":7,"learn":"2–4 weeks","resources":[
        {"label":"Google UX Design Certificate","url":"https://grow.google/certificates/ux-design/"},
        {"label":"UI Design – freeCodeCamp","url":"https://www.youtube.com/watch?v=c9Wg6Cb_YlU"},
        {"label":"Refactoring UI","url":"https://www.refactoringui.com/"}]},
    "ux":{"priority":"MEDIUM","impact":7,"learn":"2–4 weeks","resources":[
        {"label":"Nielsen Norman Group","url":"https://www.nngroup.com/articles/"},
        {"label":"UX Design Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=tyHy_9Hqd_U"},
        {"label":"UX Collective","url":"https://uxdesign.cc/"}]},
    "kubernetes":{"priority":"MEDIUM","impact":10,"learn":"4–6 weeks","resources":[
        {"label":"Kubernetes Official Docs","url":"https://kubernetes.io/docs/home/"},
        {"label":"K8s Full Course – freeCodeCamp","url":"https://www.youtube.com/watch?v=X48VuDVv0do"},
        {"label":"Play with Kubernetes","url":"https://labs.play-with-k8s.com/"}]},
    "linux":{"priority":"MEDIUM","impact":9,"learn":"2–4 weeks","resources":[
        {"label":"Linux Command Line – freeCodeCamp","url":"https://www.youtube.com/watch?v=ZtqBQ68cfJc"},
        {"label":"The Linux Command Line (Free Book)","url":"https://linuxcommand.org/tlcl.php"},
        {"label":"OverTheWire – Linux Practice","url":"https://overthewire.org/wargames/bandit/"}]},
}

_DEFAULT_INTEL = {
    "priority":"MEDIUM","impact":8,"learn":"2–4 weeks",
    "resources":[
        {"label":"freeCodeCamp YouTube","url":"https://www.youtube.com/@freecodecamp"},
        {"label":"MDN Web Docs","url":"https://developer.mozilla.org/"},
    ]
}

LEVEL_MAP = {
    "expert":("Expert",5),"advanced":("Expert",5),"senior":("Expert",5),
    "intermediate":("Intermediate",3),"mid-level":("Intermediate",3),"proficient":("Intermediate",3),
    "basic":("Basic",0),"beginner":("Basic",0),"junior":("Basic",0),
    "entry level":("Basic",0),"entry-level":("Basic",0),"familiar":("Basic",0),
}


# ═══════════════════════════════════════════
# PASSWORD HASHING
# ═══════════════════════════════════════════

def hash_pw(plain):
    return hashlib.sha256(("riq_salt_2024__" + plain).encode()).hexdigest()


# ═══════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL UNIQUE COLLATE NOCASE,
            email      TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password   TEXT NOT NULL,
            role       TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        )
    """)
    # History table
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL,
            score            REAL NOT NULL,
            skill_score      REAL NOT NULL DEFAULT 0,
            education_score  REAL NOT NULL DEFAULT 0,
            experience_score REAL NOT NULL DEFAULT 0,
            level_bonus      REAL NOT NULL DEFAULT 0,
            matched_skills   TEXT NOT NULL,
            missing_skills   TEXT NOT NULL,
            recommendation   TEXT NOT NULL,
            timestamp        TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


# ── User helpers ────────────────────────────

def db_register(username, email, password):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username,email,password,role,created_at) VALUES (?,?,?,?,?)",
            (username.strip(), email.strip().lower(), hash_pw(password),
             "user", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True, "Account created."
    except sqlite3.IntegrityError as e:
        return False, "Username already taken." if "username" in str(e) else "Email already registered."
    finally:
        conn.close()


def db_get_user(username):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── History helpers ─────────────────────────

def db_save(user_id, score, ss, es, xs, lb, matched, missing, reco):
    conn = get_db()
    conn.execute("""
        INSERT INTO history
        (user_id,score,skill_score,education_score,experience_score,level_bonus,
         matched_skills,missing_skills,recommendation,timestamp)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (user_id, score, ss, es, xs, lb,
          json.dumps(matched), json.dumps(missing),
          reco, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def db_history(user_id, limit=20):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM history WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append({
            "id": r["id"], "score": r["score"],
            "skill_score": r["skill_score"],
            "education_score": r["education_score"],
            "experience_score": r["experience_score"],
            "level_bonus": r["level_bonus"],
            "matched_skills": json.loads(r["matched_skills"]),
            "missing_skills": json.loads(r["missing_skills"]),
            "recommendation": r["recommendation"],
            "timestamp": r["timestamp"],
        })
    return out


# ═══════════════════════════════════════════
# AUTH DECORATORS
# ═══════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.path.startswith(("/analyze","/history","/api")):
                return jsonify({"error":"Login required.","auth":False}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════
# TEXT PROCESSING
# ═══════════════════════════════════════════

def extract_pdf(file_bytes):
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text = " ".join(p.extract_text() or "" for p in reader.pages)
        return text.strip()
    except Exception as e:
        raise ValueError(f"PDF read error: {e}")


def normalize(text):
    text = text.lower()
    for syn, can in SYNONYMS.items():
        text = re.sub(r'\b' + re.escape(syn) + r'\b', can, text)
    return text


def find_skills(text):
    norm = normalize(text)
    return {s for s in SKILLS if re.search(r'\b' + re.escape(s) + r'\b', norm)}


def score_section(text, keywords, max_pts, req=3):
    norm = text.lower()
    hits = sum(1 for k in keywords if k in norm)
    return round(min(hits / req, 1.0) * max_pts, 2)


def detect_level(text):
    norm = text.lower()
    best_b, best_l, best_k = -1, "Not specified", "—"
    for kw, (label, bonus) in LEVEL_MAP.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', norm) and bonus > best_b:
            best_b, best_l, best_k = bonus, label, kw
    if best_b == -1:
        return {"label":"Not specified","bonus":1,"keyword":"—"}
    return {"label":best_l,"bonus":best_b,"keyword":best_k}


def build_gap(missing, jd_skills):
    total = max(len(jd_skills), 1)
    result = []
    for skill in sorted(missing):
        intel  = SKILL_INTEL.get(skill, _DEFAULT_INTEL)
        impact = round((1 / total) * 60, 1)
        result.append({
            "skill":skill,"priority":intel["priority"],
            "impact":impact,"learn":intel["learn"],
            "resources":intel["resources"]
        })
    order = {"HIGH":0,"MEDIUM":1,"LOW":2}
    result.sort(key=lambda x: order.get(x["priority"],3))
    return result


def build_suggestions(resume_text, missing, exp_level, edu_score, exp_score):
    norm = resume_text.lower()
    tips = []
    if missing:
        top = [s.title() for s in missing[:3]]
        extra = f" (+{len(missing)-3} more)" if len(missing) > 3 else ""
        tips.append({"icon":"🎯","title":"Learn Missing Skills",
                     "body":f"Resume is missing: {', '.join(top)}{extra}. Add projects demonstrating these."})
    if edu_score < 10:
        tips.append({"icon":"🎓","title":"Strengthen Education Section",
                     "body":"Add degree name, university, graduation year, relevant coursework and GPA."})
    if exp_score < 10:
        tips.append({"icon":"💼","title":"Expand Work Experience",
                     "body":"Use action verbs: Developed, Built, Deployed, Led. Quantify your achievements."})
    if not re.search(r'\d+\s*(%|users|clients|projects|months|years)', norm):
        tips.append({"icon":"📊","title":"Add Quantified Achievements",
                     "body":"Numbers impress. E.g. 'Reduced load time by 40%', 'Served 500+ users'."})
    if not re.search(r'github|portfolio|linkedin|behance', norm):
        tips.append({"icon":"🔗","title":"Add Portfolio / GitHub Link",
                     "body":"Include GitHub, LinkedIn or portfolio URL. Recruiters check real work."})
    if exp_level["label"] == "Basic":
        tips.append({"icon":"🚀","title":"Show Depth of Knowledge",
                     "body":"Build 1–2 full end-to-end projects and document your technical decisions."})
    if not re.search(r'certif|aws|azure|google cloud|coursera|udemy|hackerrank', norm):
        tips.append({"icon":"🏅","title":"Add Certifications",
                     "body":"Free certs from Google, AWS, or HackerRank add instant credibility."})
    if not tips:
        tips.append({"icon":"✅","title":"Resume Looks Great!",
                     "body":"No major gaps. Tailor keywords from each job description for best ATS results."})
    return tips


def build_reco(matched):
    fe = matched & FRONTEND_SKILLS
    be = matched & BACKEND_SKILLS
    if len(fe) >= 3 and len(be) >= 3:
        return "🌟 Strong Full-Stack profile! Excellent fit for Full-Stack Developer roles."
    if len(fe) >= 3:
        return "🎨 Great fit for Frontend Developer. Strong UI/UX and client-side skills detected."
    if len(be) >= 3:
        return "⚙️ Great fit for Backend Developer. Solid server-side and data skills detected."
    if len(matched) >= 2:
        return "📈 Decent match. Strengthening one more skill area will boost your profile significantly."
    return "🔧 Needs improvement in key technical skills. Focus on core technologies first."


# ═══════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════

@app.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/register")
def register_page():
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/api/register", methods=["POST"])
def api_register():
    d = request.get_json(force=True) or {}
    username = (d.get("username") or "").strip()
    email    = (d.get("email") or "").strip()
    password = (d.get("password") or "").strip()

    if not all([username, email, password]):
        return jsonify({"error":"All fields are required."}), 400
    if len(username) < 3:
        return jsonify({"error":"Username must be at least 3 characters."}), 400
    if len(password) < 6:
        return jsonify({"error":"Password must be at least 6 characters."}), 400
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error":"Invalid email address."}), 400

    ok, msg = db_register(username, email, password)
    if not ok:
        return jsonify({"error": msg}), 409
    return jsonify({"message": msg}), 201


@app.route("/api/login", methods=["POST"])
def api_login():
    d = request.get_json(force=True) or {}
    username = (d.get("username") or "").strip()
    password = (d.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error":"Username and password are required."}), 400

    user = db_get_user(username)
    if not user or user["password"] != hash_pw(password):
        return jsonify({"error":"Invalid username or password."}), 401

    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    session["role"]     = user["role"]
    return jsonify({"message":"Login successful.","username":user["username"],"role":user["role"]})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message":"Logged out."})


@app.route("/api/me")
def api_me():
    if "user_id" not in session:
        return jsonify({"authenticated":False})
    return jsonify({"authenticated":True,"username":session["username"],"role":session["role"]})


# ═══════════════════════════════════════════
# MAIN ROUTES
# ═══════════════════════════════════════════

@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    uploaded = request.files.get("resume")
    if not uploaded or uploaded.filename == "":
        return jsonify({"error":"No resume file uploaded."}), 400

    job_desc = request.form.get("job_description","").strip()
    if not job_desc:
        return jsonify({"error":"Job description cannot be empty."}), 400

    fname = uploaded.filename.lower()
    if fname.endswith(".pdf"):
        raw = uploaded.read()
        if not raw:
            return jsonify({"error":"Uploaded PDF is empty."}), 400
        try:
            resume_text = extract_pdf(raw)
        except ValueError as e:
            return jsonify({"error":str(e)}), 400
        if not resume_text:
            return jsonify({"error":"PDF has no extractable text (scanned PDF not supported)."}), 400
    elif fname.endswith(".txt"):
        try:
            resume_text = uploaded.read().decode("utf-8", errors="ignore").strip()
        except Exception:
            return jsonify({"error":"Could not read text file."}), 400
        if not resume_text:
            return jsonify({"error":"Text file is empty."}), 400
    else:
        return jsonify({"error":"Invalid file type. Upload PDF or TXT only."}), 400

    # Skill matching
    resume_skills = find_skills(resume_text)
    jd_skills     = find_skills(job_desc)

    if jd_skills:
        matched     = resume_skills & jd_skills
        missing     = jd_skills - resume_skills
        skill_score = round((len(matched) / len(jd_skills)) * 60, 2)
    else:
        matched     = resume_skills
        missing     = set()
        skill_score = 60.0 if resume_skills else 0.0

    matched_list = sorted(matched)
    missing_list = sorted(missing)

    edu_score = score_section(resume_text, EDUCATION_KW, 20, 3)
    exp_score = score_section(resume_text, EXPERIENCE_KW, 20, 4)
    exp_level = detect_level(resume_text)
    bonus     = exp_level["bonus"]

    final_score = round(min(skill_score + edu_score + exp_score + bonus, 100.0), 1)
    reco        = build_reco(matched)
    skill_gap   = build_gap(missing_list, jd_skills)
    suggestions = build_suggestions(resume_text, missing_list, exp_level, edu_score, exp_score)

    db_save(session["user_id"], final_score, skill_score, edu_score,
            exp_score, bonus, matched_list, missing_list, reco)

    return jsonify({
        "score":            final_score,
        "skill_score":      skill_score,
        "education_score":  edu_score,
        "experience_score": exp_score,
        "level_bonus":      bonus,
        "matched_skills":   matched_list,
        "missing_skills":   missing_list,
        "recommendation":   reco,
        "experience_level": exp_level,
        "skill_gap":        skill_gap,
        "suggestions":      suggestions,
    })


@app.route("/history")
@login_required
def history():
    return jsonify(db_history(session["user_id"]))


# ═══════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    print("\n✅  RecruitIQ v2 running → http://127.0.0.1:5000\n")
    app.run(debug=True)
