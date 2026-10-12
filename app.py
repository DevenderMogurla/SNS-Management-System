import os
import uuid
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash,
    session,
    url_for,
    send_from_directory
)

from werkzeug.utils import secure_filename

from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
    SignatureExpired
)

from database import (
    createTables,

    getUserDataByEmail,
    insertUserRecord,
    updatePassword,

    insertNote,
    getNotesByUser,
    searchNotes,
    getNotesCount,
    updateNote,
    deleteNote,

    insertFileRecord,
    getFilesByUser,
    searchFiles,
    getFilesCount,
    getFileById,
    updateFile,
    deleteFile
)

from utils import (
    SendEmail,
    EmailTemapltes,
    generate_otp,
    generateHashPassword,
    verifyHashPassword
)


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "devender"
)


# =========================================================
# UPLOAD CONFIGURATION
# =========================================================

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "uploads"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# ALLOWED FILE TYPES
# =========================================================

ALLOWED_EXTENSIONS = {
    "pdf",
    "txt",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "csv",
    "jpg",
    "jpeg",
    "png",
    "gif",
    "ppt",
    "pptx",
    "py",
    "html",
    "css",
    "js",
    "json",
    "zip"
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


def fail(
    message,
    endpoint,
    **values
):

    flash(
        message,
        "err"
    )

    return redirect(
        url_for(
            endpoint,
            **values
        )
    )


def success(
    message,
    endpoint,
    **values
):

    flash(
        message,
        "msg"
    )

    return redirect(
        url_for(
            endpoint,
            **values
        )
    )


def login_required(view):

    @wraps(view)
    def wrapper(
        *args,
        **kwargs
    ):

        if "id" not in session:

            return redirect(
                url_for("login")
            )

        return view(
            *args,
            **kwargs
        )

    return wrapper


def removeFile(path):

    try:

        if os.path.exists(path):

            os.remove(path)

    except Exception as e:

        print(
            "File cleanup error:",
            e
        )


# =========================================================
# PASSWORD RESET TOKEN
# =========================================================

serializer = URLSafeTimedSerializer(
    app.secret_key
)


def generateToken(email):

    return serializer.dumps(
        email,
        salt="reset-password"
    )


def validateToken(token):

    try:

        return serializer.loads(
            token,
            max_age=600,
            salt="reset-password"
        )

    except SignatureExpired:

        return fail(
            "URL Time expired",
            "forgot_password"
        )

    except BadSignature:

        return fail(
            "Invalid URL",
            "forgot_password"
        )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "home.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "GET":

        return render_template(
            "register.html"
        )

    email = request.form.get(
        "email"
    )

    name = request.form.get(
        "name"
    )

    password = request.form.get(
        "password"
    )

    confirm_password = request.form.get(
        "confirm_password"
    )

    if not email or not name or not password:

        return fail(
            "All fields are required.",
            "register"
        )

    if password != confirm_password:

        return fail(
            "Password doesn't match",
            "register"
        )

    status, user = getUserDataByEmail(
        email=email
    )

    if status:

        return fail(
            "User Email Already Exists",
            "register"
        )

    otp = generate_otp()

    status, msg = SendEmail(
        to_email=email,
        subject="SNS Registration OTP",
        body=EmailTemapltes.OTPEmailTempalte(
            otp=otp,
            username=name
        )
    )

    if not status:

        return fail(
            msg,
            "register"
        )

    session.clear()

    session["register_name"] = name
    session["register_email"] = email
    session["register_password"] = password
    session["register_otp"] = otp

    return redirect(
        url_for("verifyotp")
    )


# =========================================================
# VERIFY OTP
# =========================================================

@app.route(
    "/verifyotp",
    methods=["GET", "POST"]
)
def verifyotp():

    if request.method == "GET":

        return render_template(
            "verifyotp.html"
        )

    entered_otp = request.form.get(
        "otp"
    )

    stored_otp = session.get(
        "register_otp"
    )

    if not stored_otp:

        return fail(
            "OTP session expired. Please register again.",
            "register"
        )

    try:

        entered_otp = int(
            entered_otp
        )

    except (
        TypeError,
        ValueError
    ):

        return fail(
            "Invalid OTP",
            "verifyotp"
        )

    if entered_otp != stored_otp:

        return fail(
            "Invalid OTP",
            "verifyotp"
        )

    hash_password = generateHashPassword(
        session["register_password"]
    )

    status, msg = insertUserRecord(
        email=session["register_email"],
        username=session["register_name"],
        hash_password=hash_password
    )

    if not status:

        return fail(
            msg,
            "register"
        )

    session.clear()

    return success(
        "Registration successful. Please login.",
        "login"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "GET":

        return render_template(
            "login.html"
        )

    email = request.form.get(
        "email"
    )

    password = request.form.get(
        "password"
    )

    if not email or not password:

        return fail(
            "Email and password are required.",
            "login"
        )

    status, user = getUserDataByEmail(
        email=email
    )

    if not status:

        return fail(
            user,
            "login"
        )

    if not verifyHashPassword(
        password=password,
        hash_password=user["hashpassword"]
    ):

        return fail(
            "Incorrect password! Try again.",
            "login"
        )

    session.clear()

    session["id"] = user["userid"]
    session["email"] = user["email"]
    session["name"] = user["username"]

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "GET":

        return render_template(
            "forgot_password.html"
        )

    email = request.form.get(
        "email"
    )

    if not email:

        return fail(
            "Email is required.",
            "forgot_password"
        )

    status, user = getUserDataByEmail(
        email=email
    )

    if not status:

        return fail(
            user,
            "forgot_password"
        )

    token = generateToken(
        email
    )

    reset_link = url_for(
        "reset_password",
        token=token,
        _external=True
    )

    status, msg = SendEmail(
        to_email=email,
        subject="Reset password SNS app",
        body=EmailTemapltes.resetpasswordEmaliTemplate(
            username=user["username"],
            url=reset_link
        )
    )

    if not status:

        return fail(
            msg,
            "forgot_password"
        )

    return success(
        "Password reset link sent to your email.",
        "login"
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    email = validateToken(
        token
    )

    if not isinstance(
        email,
        str
    ):

        return email

    if request.method == "GET":

        return render_template(
            "reset_password.html",
            token=token
        )

    new_password = request.form.get(
        "password"
    )

    confirm_password = request.form.get(
        "confirm_password"
    )

    if not new_password:

        flash(
            "Password is required.",
            "err"
        )

        return render_template(
            "reset_password.html",
            token=token
        )

    if new_password != confirm_password:

        flash(
            "Password doesn't match",
            "err"
        )

        return render_template(
            "reset_password.html",
            token=token
        )

    status, msg = updatePassword(
        email=email,
        hash_password=generateHashPassword(
            new_password
        )
    )

    if not status:

        flash(
            msg,
            "err"
        )

        return render_template(
            "reset_password.html",
            token=token
        )

    return success(
        "Password Updated Successfully",
        "login"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route(
    "/dashboard",
    methods=["GET", "POST"]
)
@login_required
def dashboard():

    # Search
    search = request.args.get(
        "search",
        ""
    ).strip()

    # =====================================================
    # NOTES + FILES
    # =====================================================

    if search:

        note_status, notes = searchNotes(
            userid=session["id"],
            search=search
        )

        file_status, files = searchFiles(
            userid=session["id"],
            search=search
        )

        if not note_status:
            notes = []

        if not file_status:
            files = []

    else:

        note_status, notes = getNotesByUser(
            userid=session["id"]
        )

        file_status, files = getFilesByUser(
            userid=session["id"]
        )

        if not note_status:
            notes = []

        if not file_status:
            files = []

    # =====================================================
    # TOTAL COUNTS
    # =====================================================

    note_count_status, total_notes = getNotesCount(
        userid=session["id"]
    )

    file_count_status, total_files = getFilesCount(
        userid=session["id"]
    )

    if not note_count_status:
        total_notes = 0

    if not file_count_status:
        total_files = 0

    # =====================================================
    # DASHBOARD
    # =====================================================

    return render_template(
        "dashboard.html",

        name=session["name"],

        notes=notes,
        files=files,

        search=search,

        total_notes=total_notes,
        total_files=total_files
    )


# =========================================================
# NOTES
# =========================================================

@app.route("/notes")
@login_required
def mynotes():

    search = request.args.get(
        "search",
        ""
    ).strip()

    if search:

        status, notes = searchNotes(
            userid=session["id"],
            search=search
        )

    else:

        status, notes = getNotesByUser(
            userid=session["id"]
        )

    if not status:

        flash(
            notes,
            "err"
        )

        notes = []

    return render_template(
        "notes.html",
        notes=notes,
        search=search
    )


# =========================================================
# ADD NOTE
# =========================================================

@app.route(
    "/notes/addnotes",
    methods=["GET", "POST"]
)
@login_required
def addnote():

    if request.method == "GET":

        return render_template(
            "addnotes.html"
        )

    title = request.form.get(
        "title"
    )

    content = request.form.get(
        "content"
    )

    if not title or not content:

        return fail(
            "Title and content are required",
            "addnote"
        )

    status, msg = insertNote(
        userid=session["id"],
        title=title,
        content=content
    )

    if not status:

        return fail(
            msg,
            "addnote"
        )

    return success(
        "Note saved successfully.",
        "mynotes"
    )


# =========================================================
# VIEW NOTE
# =========================================================

@app.route(
    "/viewnote/<int:note_id>"
)
@login_required
def viewnote(note_id):

    status, note = getNotesByUser(
        userid=session["id"],
        notesid=note_id
    )

    if not status:

        return fail(
            note,
            "mynotes"
        )

    return render_template(
        "viewnotes.html",
        note=note
    )


# =========================================================
# EDIT NOTE
# =========================================================

@app.route(
    "/editnote/<int:note_id>",
    methods=["GET", "POST"]
)
@login_required
def editnote(note_id):

    if request.method == "GET":

        status, note = getNotesByUser(
            userid=session["id"],
            notesid=note_id
        )

        if not status:

            return fail(
                note,
                "mynotes"
            )

        return render_template(
            "editnotes.html",
            note=note
        )

    title = request.form.get(
        "title"
    )

    content = request.form.get(
        "content"
    )

    if not title or not content:

        return fail(
            "Title and content are required",
            "editnote",
            note_id=note_id
        )

    status, msg = updateNote(
        notesid=note_id,
        userid=session["id"],
        title=title,
        content=content
    )

    if not status:

        return fail(
            msg,
            "editnote",
            note_id=note_id
        )

    return success(
        "Note updated and saved successfully.",
        "viewnote",
        note_id=note_id
    )


# =========================================================
# DELETE NOTE
# =========================================================

@app.route(
    "/deletenote/<int:note_id>"
)
@login_required
def deletenote(note_id):

    status, msg = deleteNote(
        notesid=note_id,
        userid=session["id"]
    )

    if not status:

        return fail(
            msg,
            "mynotes"
        )

    return success(
        "Note deleted successfully.",
        "mynotes"
    )


# =========================================================
# FILES
# =========================================================

@app.route(
    "/files",
    methods=["GET", "POST"]
)
@login_required
def files():

    # =====================================================
    # UPLOAD
    # =====================================================

    if request.method == "POST":

        uploaded_file = request.files.get(
            "file"
        )

        if not uploaded_file or not uploaded_file.filename:

            return fail(
                "Please select a file.",
                "files"
            )

        original_name = secure_filename(
            uploaded_file.filename
        )

        if not original_name:

            return fail(
                "Invalid file name.",
                "files"
            )

        if not allowed_file(
            original_name
        ):

            return fail(
                "This file type is not allowed.",
                "files"
            )

        extension = os.path.splitext(
            original_name
        )[1].lower()

        stored_name = (
            str(uuid.uuid4())
            + extension
        )

        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            stored_name
        )

        try:

            uploaded_file.save(
                file_path
            )

            file_size = os.path.getsize(
                file_path
            )

        except Exception as e:

            print(
                "File save error:",
                e
            )

            return fail(
                "Unable to save file.",
                "files"
            )

        mimetype = (
            uploaded_file.mimetype
            or "application/octet-stream"
        )

        status, msg = insertFileRecord(

            userid=session["id"],

            originalname=original_name,

            storedname=stored_name,

            mimetype=mimetype,

            size=file_size,

            path=file_path
        )

        if not status:

            removeFile(
                file_path
            )

            return fail(
                msg,
                "files"
            )

        return success(
            "File uploaded and saved successfully.",
            "files"
        )

    # =====================================================
    # SEARCH FILES
    # =====================================================

    search = request.args.get(
        "search",
        ""
    ).strip()

    if search:

        status, user_files = searchFiles(
            userid=session["id"],
            search=search
        )

    else:

        status, user_files = getFilesByUser(
            userid=session["id"]
        )

    if not status:

        flash(
            user_files,
            "err"
        )

        user_files = []

    return render_template(
        "files.html",
        files=user_files,
        search=search
    )


# =========================================================
# DOWNLOAD FILE
# =========================================================

@app.route(
    "/files/download/<int:file_id>"
)
@login_required
def download_file(file_id):

    status, file_data = getFileById(
        fileid=file_id,
        userid=session["id"]
    )

    if not status:

        return fail(
            file_data,
            "files"
        )

    if not os.path.exists(
        file_data["path"]
    ):

        return fail(
            "Physical file not found.",
            "files"
        )

    return send_from_directory(

        os.path.dirname(
            file_data["path"]
        ),

        file_data["storedname"],

        as_attachment=True,

        download_name=file_data["originalname"]
    )


# =========================================================
# EDIT FILE
# =========================================================

@app.route(
    "/files/edit/<int:file_id>",
    methods=["GET", "POST"]
)
@login_required
def editfile(file_id):

    status, file_data = getFileById(
        fileid=file_id,
        userid=session["id"]
    )

    if not status:

        return fail(
            file_data,
            "files"
        )

    if request.method == "GET":

        return render_template(
            "editfile.html",
            file=file_data
        )

    new_name = request.form.get(
        "filename"
    )

    if not new_name:

        return fail(
            "File name is required.",
            "editfile",
            file_id=file_id
        )

    new_name = secure_filename(
        new_name
    )

    if not new_name:

        return fail(
            "Invalid file name.",
            "editfile",
            file_id=file_id
        )

    status, msg = updateFile(
        fileid=file_id,
        userid=session["id"],
        originalname=new_name
    )

    if not status:

        return fail(
            msg,
            "editfile",
            file_id=file_id
        )

    return success(
        "File updated and saved successfully.",
        "files"
    )


# =========================================================
# DELETE FILE
# =========================================================

@app.route(
    "/files/delete/<int:file_id>"
)
@login_required
def delete_file(file_id):

    status, file_data = getFileById(
        fileid=file_id,
        userid=session["id"]
    )

    if not status:

        return fail(
            file_data,
            "files"
        )

    status, msg = deleteFile(
        fileid=file_id,
        userid=session["id"]
    )

    if not status:

        return fail(
            msg,
            "files"
        )

    removeFile(
        file_data["path"]
    )

    return success(
        "File deleted successfully.",
        "files"
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print(
        createTables()
    )

    app.run(
        debug=True
    )