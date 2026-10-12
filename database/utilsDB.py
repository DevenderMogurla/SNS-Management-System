from database.connection import (
    DatabaseConnection,
    getLastError
)


# =========================================================
# COMMON QUERY HELPER
# =========================================================

def runQuery(
    name,
    query,
    params=(),
    fetch=None,
    ok="",
    missing=""
):

    db_config = DatabaseConnection()

    if db_config is None:

        return (
            False,
            "Database connection failed: "
            + getLastError()
        )

    cursor = None

    try:

        cursor = db_config.cursor(
            dictionary=True
        )

        cursor.execute(
            query,
            params
        )

        # =================================================
        # FETCH ONE
        # =================================================

        if fetch == "one":

            row = cursor.fetchone()

            if row:

                return True, row

            return False, missing

        # =================================================
        # FETCH ALL
        # =================================================

        if fetch == "all":

            rows = cursor.fetchall()

            return True, rows

        # =================================================
        # INSERT / UPDATE / DELETE
        # =================================================

        db_config.commit()

        return True, ok

    except Exception as e:

        db_config.rollback()

        return (
            False,
            f"Something wrong in {name}(): {e}"
        )

    finally:

        if cursor:

            cursor.close()

        db_config.close()


# =========================================================
# USERS
# =========================================================

def getUserDataByEmail(email: str):

    return runQuery(
        "getUserDataByEmail",

        """
        SELECT *
        FROM users
        WHERE email = %s
        """,

        (email,),

        fetch="one",

        missing="Email does not exist"
    )


def insertUserRecord(
    email: str,
    username: str,
    hash_password: str
):

    return runQuery(
        "insertUserRecord",

        """
        INSERT INTO users
        (
            email,
            username,
            hashpassword
        )
        VALUES
        (
            %s,
            %s,
            %s
        )
        """,

        (
            email,
            username,
            hash_password
        ),

        ok="Registered Successfully"
    )


def updatePassword(
    email: str,
    hash_password: str
):

    return runQuery(
        "updatePassword",

        """
        UPDATE users
        SET hashpassword = %s
        WHERE email = %s
        """,

        (
            hash_password,
            email
        ),

        ok="Password Updated Successfully"
    )


# =========================================================
# NOTES
# =========================================================

def insertNote(
    userid: int,
    title: str,
    content: str
):

    return runQuery(
        "insertNote",

        """
        INSERT INTO notes
        (
            userid,
            title,
            content
        )
        VALUES
        (
            %s,
            %s,
            %s
        )
        """,

        (
            userid,
            title,
            content
        ),

        ok="Note added successfully"
    )


def getNotesByUser(
    userid: int,
    notesid: int = None
):

    if notesid is not None:

        return runQuery(
            "getNotesByUser",

            """
            SELECT *
            FROM notes
            WHERE userid = %s
            AND notesid = %s
            """,

            (
                userid,
                notesid
            ),

            fetch="one",

            missing="Note not found"
        )

    return runQuery(
        "getNotesByUser",

        """
        SELECT *
        FROM notes
        WHERE userid = %s
        ORDER BY updated_at DESC
        """,

        (userid,),

        fetch="all"
    )


# =========================================================
# SEARCH NOTES
# =========================================================

def searchNotes(
    userid: int,
    search: str
):

    search_value = "%" + search + "%"

    return runQuery(
        "searchNotes",

        """
        SELECT *
        FROM notes
        WHERE userid = %s
        AND
        (
            title LIKE %s
            OR content LIKE %s
        )
        ORDER BY updated_at DESC
        """,

        (
            userid,
            search_value,
            search_value
        ),

        fetch="all"
    )


# =========================================================
# TOTAL NOTES COUNT
# =========================================================

def getNotesCount(userid: int):

    return runQuery(
        "getNotesCount",

        """
        SELECT COUNT(*) AS total_notes
        FROM notes
        WHERE userid = %s
        """,

        (userid,),

        fetch="one",

        missing="Unable to count notes"
    )


def updateNote(
    notesid: int,
    userid: int,
    title: str,
    content: str
):

    return runQuery(
        "updateNote",

        """
        UPDATE notes
        SET
            title = %s,
            content = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE
            notesid = %s
            AND userid = %s
        """,

        (
            title,
            content,
            notesid,
            userid
        ),

        ok="Note updated successfully"
    )


def deleteNote(
    notesid: int,
    userid: int
):

    return runQuery(
        "deleteNote",

        """
        DELETE FROM notes
        WHERE
            notesid = %s
            AND userid = %s
        """,

        (
            notesid,
            userid
        ),

        ok="Note deleted successfully"
    )


# =========================================================
# FILES
# =========================================================

def insertFileRecord(
    userid: int,
    originalname: str,
    storedname: str,
    mimetype: str,
    size: int,
    path: str
):

    return runQuery(
        "insertFileRecord",

        """
        INSERT INTO files
        (
            userid,
            originalname,
            storedname,
            mimetype,
            size,
            path
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,

        (
            userid,
            originalname,
            storedname,
            mimetype,
            size,
            path
        ),

        ok="File saved successfully"
    )


def getFilesByUser(userid: int):

    return runQuery(
        "getFilesByUser",

        """
        SELECT *
        FROM files
        WHERE userid = %s
        ORDER BY created_at DESC
        """,

        (userid,),

        fetch="all"
    )


# =========================================================
# SEARCH FILES
# =========================================================

def searchFiles(
    userid: int,
    search: str
):

    search_value = "%" + search + "%"

    return runQuery(
        "searchFiles",

        """
        SELECT *
        FROM files
        WHERE userid = %s
        AND originalname LIKE %s
        ORDER BY created_at DESC
        """,

        (
            userid,
            search_value
        ),

        fetch="all"
    )


# =========================================================
# TOTAL FILES COUNT
# =========================================================

def getFilesCount(userid: int):

    return runQuery(
        "getFilesCount",

        """
        SELECT COUNT(*) AS total_files
        FROM files
        WHERE userid = %s
        """,

        (userid,),

        fetch="one",

        missing="Unable to count files"
    )


# =========================================================
# GET FILE BY ID
# =========================================================

def getFileById(
    fileid: int,
    userid: int
):

    return runQuery(
        "getFileById",

        """
        SELECT *
        FROM files
        WHERE
            fileid = %s
            AND userid = %s
        """,

        (
            fileid,
            userid
        ),

        fetch="one",

        missing="File not found"
    )


# =========================================================
# UPDATE FILE
# =========================================================

def updateFile(
    fileid: int,
    userid: int,
    originalname: str
):

    return runQuery(
        "updateFile",

        """
        UPDATE files
        SET originalname = %s
        WHERE
            fileid = %s
            AND userid = %s
        """,

        (
            originalname,
            fileid,
            userid
        ),

        ok="File updated successfully"
    )


# =========================================================
# DELETE FILE
# =========================================================

def deleteFile(
    fileid: int,
    userid: int
):

    return runQuery(
        "deleteFile",

        """
        DELETE FROM files
        WHERE
            fileid = %s
            AND userid = %s
        """,

        (
            fileid,
            userid
        ),

        ok="File deleted successfully"
    )