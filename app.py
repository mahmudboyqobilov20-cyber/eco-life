import os, sqlite3, secrets
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "ecolife.db"))

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            excerpt TEXT NOT NULL, body TEXT NOT NULL, category TEXT NOT NULL,
            image TEXT NOT NULL, read_time INTEGER NOT NULL DEFAULT 4,
            author_id INTEGER, published INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER NOT NULL, article_id INTEGER NOT NULL,
            PRIMARY KEY(user_id, article_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
        );
        """)
        count = c.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        if count == 0:
            samples = [
            ("Tabiatni asrash — kelajakni asrash", "Har kuni qiladigan kichik tanlovlarimiz sayyoramiz kelajagiga ta’sir qiladi.", "Ekologiya", "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1200&q=85", 5,
             "Tabiat bizga toza havo, suv, oziq-ovqat va yashash uchun zarur bo‘lgan ko‘plab ne’matlarni beradi. Uni asrash faqat yirik tashkilotlarning emas, har birimizning vazifamizdir. Chiqindini saralash, suvni tejash, daraxt ekish va bir martalik plastikdan kamroq foydalanish orqali ijobiy o‘zgarish boshlash mumkin."),
            ("Plastik chiqindilarni kamaytirishning 7 yo‘li", "Oddiy odatlar orqali plastikdan foydalanishni sezilarli kamaytirish mumkin.", "Qayta ishlash", "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?auto=format&fit=crop&w=1200&q=85", 6,
             "Qayta foydalaniladigan sumka va suv idishini tanlang. Xarid qilayotganda ortiqcha qadoqlardan qoching, mahsulotni imkon qadar uzoq ishlating va mahalliy qayta ishlash qoidalarini o‘rganing. Eng yaxshi chiqindi — paydo bo‘lishining oldi olingan chiqindidir."),
            ("Shaharlarimizda yashil hududlar nega muhim?", "Daraxtlar issiqni kamaytiradi, havoni yaxshilaydi va odamlar uchun dam olish joylarini yaratadi.", "Yashil hayot", "https://images.unsplash.com/photo-1472396961693-142e6e269027?auto=format&fit=crop&w=1200&q=85", 4,
             "Yashil hududlar shahar hayotining muhim qismidir. Daraxtlar soyasi haroratni pasaytiradi, qushlar va hasharotlar uchun yashash muhitini yaratadi. Mahalliy ko‘chatlarni ekish, mavjud daraxtlarni parvarish qilish va bog‘larni toza saqlash hamjamiyat uchun foydalidir."),
            ("Suvni tejash: uyda boshlanadigan o‘zgarish", "Suvdan oqilona foydalanish tabiiy resurslarni asrashga yordam beradi.", "Suv va iqlim", "https://images.unsplash.com/photo-1437482078695-73f5ca6c96e2?auto=format&fit=crop&w=1200&q=85", 3,
             "Suvni tejash uchun oqayotgan jo‘mraklarni tuzating, tish yuvayotganda suvni yopib qo‘ying va bog‘ni salqin paytda sug‘oring. Suv resurslari cheklangan hududlarda har bir tejalgan litrning ahamiyati bor.")
            ]
            now = datetime.utcnow().isoformat()
            c.executemany("INSERT INTO articles(title,excerpt,body,category,image,read_time,created_at) VALUES(?,?,?,?,?,?,?)",
                [(t,e,b,cat,img,rt,now) for t,e,cat,img,rt,b in samples])

def current_user():
    uid = session.get("user_id")
    if not uid: return None
    with db() as c:
        return c.execute("SELECT id,name,email,is_admin FROM users WHERE id=?", (uid,)).fetchone()

@app.context_processor
def inject_user():
    return {"current_user": current_user()}

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user["is_admin"]:
            flash("Bu bo‘lim faqat administrator uchun.", "error")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sql = "SELECT a.*, (SELECT COUNT(*) FROM likes l WHERE l.article_id=a.id) AS likes FROM articles a WHERE a.published=1"
    params = []
    if q:
        sql += " AND (a.title LIKE ? OR a.excerpt LIKE ? OR a.body LIKE ?)"
        params += [f"%{q}%"] * 3
    if category and category != "Barchasi":
        sql += " AND a.category=?"; params.append(category)
    sql += " ORDER BY a.created_at DESC"
    with db() as c:
        articles = c.execute(sql, params).fetchall()
        categories = [r["category"] for r in c.execute("SELECT DISTINCT category FROM articles WHERE published=1 ORDER BY category").fetchall()]
        article_count = c.execute("SELECT COUNT(*) FROM articles WHERE published=1").fetchone()[0]
        user_count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return render_template("index.html", articles=articles, categories=categories, selected=category, q=q, article_count=article_count, user_count=user_count)

@app.route("/article/<int:article_id>")
def article(article_id):
    with db() as c:
        item = c.execute("SELECT a.*,u.name AS author FROM articles a LEFT JOIN users u ON u.id=a.author_id WHERE a.id=? AND a.published=1", (article_id,)).fetchone()
        if not item: abort(404)
        likes = c.execute("SELECT COUNT(*) FROM likes WHERE article_id=?", (article_id,)).fetchone()[0]
        liked = bool(current_user() and c.execute("SELECT 1 FROM likes WHERE article_id=? AND user_id=?", (article_id, session["user_id"])).fetchone())
    return render_template("article.html", article=item, likes=likes, liked=liked)

@app.route("/like/<int:article_id>", methods=["POST"])
def like(article_id):
    if not current_user(): return jsonify({"ok": False, "message": "Yoqtirish uchun tizimga kiring."}), 401
    with db() as c:
        exists = c.execute("SELECT 1 FROM likes WHERE user_id=? AND article_id=?", (session["user_id"], article_id)).fetchone()
        if exists: c.execute("DELETE FROM likes WHERE user_id=? AND article_id=?", (session["user_id"], article_id))
        else: c.execute("INSERT OR IGNORE INTO likes(user_id,article_id) VALUES(?,?)", (session["user_id"], article_id))
        total = c.execute("SELECT COUNT(*) FROM likes WHERE article_id=?", (article_id,)).fetchone()[0]
    return jsonify({"ok": True, "liked": not bool(exists), "likes": total})

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name=request.form.get("name","").strip()
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        if not name or not email or len(password)<8:
            flash("Ism va emailni kiriting. Parol kamida 8 belgidan iborat bo‘lsin.", "error")
        else:
            try:
                with db() as c:
                    c.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",
                              (name,email,generate_password_hash(password),datetime.utcnow().isoformat()))
                flash("Hisob yaratildi. Endi tizimga kiring.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Bu email avval ro‘yxatdan o‘tgan.", "error")
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        with db() as c: user=c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"],password):
            session.clear(); session["user_id"]=user["id"]
            flash("Xush kelibsiz!", "success")
            return redirect(url_for("admin") if user["is_admin"] else url_for("index"))
        flash("Email yoki parol noto‘g‘ri.", "error")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear(); flash("Tizimdan chiqdingiz.", "success")
    return redirect(url_for("index"))

@app.route("/admin", methods=["GET","POST"])
@admin_required
def admin():
    if request.method == "POST":
        title=request.form.get("title","").strip()
        excerpt=request.form.get("excerpt","").strip()
        body=request.form.get("body","").strip()
        category=request.form.get("category","Ekologiya").strip()
        image=request.form.get("image","").strip() or "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1200&q=85"
        try: read_time=max(1,min(30,int(request.form.get("read_time","4"))))
        except ValueError: read_time=4
        if not title or not excerpt or not body:
            flash("Sarlavha, qisqa matn va maqola matnini to‘ldiring.", "error")
        else:
            with db() as c:
                c.execute("INSERT INTO articles(title,excerpt,body,category,image,read_time,author_id,created_at) VALUES(?,?,?,?,?,?,?,?)",
                          (title,excerpt,body,category,image,read_time,session["user_id"],datetime.utcnow().isoformat()))
            flash("Maqola muvaffaqiyatli qo‘shildi.", "success")
            return redirect(url_for("admin"))
    with db() as c:
        articles=c.execute("SELECT id,title,category,created_at,published FROM articles ORDER BY created_at DESC").fetchall()
        users=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return render_template("admin.html", articles=articles, users=users)

@app.route("/admin/delete/<int:article_id>", methods=["POST"])
@admin_required
def delete_article(article_id):
    with db() as c: c.execute("DELETE FROM articles WHERE id=?", (article_id,))
    flash("Maqola o‘chirildi.", "success")
    return redirect(url_for("admin"))

@app.route("/health")
def health():
    return {"status":"ok","app":"ECO LIFE"}

def bootstrap():
    init_db()
    # Create an admin account on first run only, using environment variables in production.
    admin_email=os.environ.get("ADMIN_EMAIL","admin@ecolife.uz").lower()
    admin_password=os.environ.get("ADMIN_PASSWORD","ChangeMe123!")
    with db() as c:
        if not c.execute("SELECT id FROM users WHERE email=?", (admin_email,)).fetchone():
            c.execute("INSERT INTO users(name,email,password_hash,is_admin,created_at) VALUES(?,?,?,?,?)",
                      ("ECO LIFE Admin",admin_email,generate_password_hash(admin_password),1,datetime.utcnow().isoformat()))

bootstrap()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
