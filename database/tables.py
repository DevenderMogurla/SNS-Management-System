from database.connection import DatabaseConnection, getLastError


# =========================================================
# TABLE QUERIES
# =========================================================

USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users(
    userid BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashpassword VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


NOTES_TABLE = """
CREATE TABLE IF NOT EXISTS notes(
    notesid BIGINT AUTO_INCREMENT PRIMARY KEY,
    userid BIGINT,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY(userid) REFERENCES users(userid)
        ON DELETE CASCADE
);
"""


FILES_TABLE = """
CREATE TABLE IF NOT EXISTS files(
    fileid BIGINT AUTO_INCREMENT PRIMARY KEY,
    userid BIGINT,
    originalname VARCHAR(255) NOT NULL,
    storedname VARCHAR(255) NOT NULL,
    mimetype VARCHAR(255) NOT NULL
        DEFAULT 'application/octet-stream',
    size BIGINT NOT NULL DEFAULT 0,
    path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(userid) REFERENCES users(userid)
        ON DELETE CASCADE
);
"""


# =========================================================
# REQUIRED FILE COLUMNS
# =========================================================

FILES_REQUIRED_COLUMNS = {

    "userid":
        "BIGINT",

    "originalname":
        "VARCHAR(255) NOT NULL DEFAULT ''",

    "storedname":
        "VARCHAR(255) NOT NULL DEFAULT ''",

    "mimetype":
        "VARCHAR(255) NOT NULL DEFAULT 'application/octet-stream'",

    "size":
        "BIGINT NOT NULL DEFAULT 0",

    "path":
        "VARCHAR(255) NOT NULL DEFAULT ''",

    "created_at":
        "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
}


# =========================================================
# GET TABLE COLUMNS
# =========================================================

def getColumns(cursor, table):

    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        """,
        (table,)
    )

    columns = set()

    for row in cursor.fetchall():

        name = row[0]

        if isinstance(name, (bytes, bytearray)):
            name = name.decode()

        columns.add(name.lower())

    return columns


# =========================================================
# REPAIR FILES TABLE
# =========================================================

def migrateFilesTable(cursor):

    changes = []

    columns = getColumns(cursor, "files")

    # =====================================================
    # OLD ORIGINAL NAME TYPO
    # orignalname -> originalname
    # =====================================================

    if (
        "orignalname" in columns
        and
        "originalname" not in columns
    ):

        cursor.execute(
            """
            ALTER TABLE files
            CHANGE COLUMN orignalname
            originalname VARCHAR(255) NOT NULL
            """
        )

        changes.append(
            "renamed orignalname -> originalname"
        )

        columns = getColumns(cursor, "files")


    # =====================================================
    # OLD MIME TYPE COLUMN
    # mime_type -> mimetype
    # =====================================================

    if (
        "mime_type" in columns
        and
        "mimetype" not in columns
    ):

        cursor.execute(
            """
            ALTER TABLE files
            CHANGE COLUMN mime_type
            mimetype VARCHAR(255)
            NOT NULL
            DEFAULT 'application/octet-stream'
            """
        )

        changes.append(
            "renamed mime_type -> mimetype"
        )

        columns = getColumns(cursor, "files")


    # =====================================================
    # BOTH mime_type AND mimetype EXIST
    # =====================================================

    elif (
        "mime_type" in columns
        and
        "mimetype" in columns
    ):

        # Copy old values into the correct column
        cursor.execute(
            """
            UPDATE files
            SET mimetype = mime_type
            WHERE
                mime_type IS NOT NULL
                AND
                (
                    mimetype IS NULL
                    OR
                    mimetype = ''
                    OR
                    mimetype = 'application/octet-stream'
                )
            """
        )

        # Remove old column
        cursor.execute(
            """
            ALTER TABLE files
            DROP COLUMN mime_type
            """
        )

        changes.append(
            "copied mime_type -> mimetype and removed mime_type"
        )

        columns = getColumns(cursor, "files")


    # =====================================================
    # ADD MISSING COLUMNS
    # =====================================================

    for column, definition in FILES_REQUIRED_COLUMNS.items():

        if column not in columns:

            cursor.execute(
                f"""
                ALTER TABLE files
                ADD COLUMN {column} {definition}
                """
            )

            changes.append(
                f"added {column}"
            )


    # =====================================================
    # MAKE SURE mimetype IS NOT NULL WITH DEFAULT
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE files
        MODIFY COLUMN mimetype
        VARCHAR(255)
        NOT NULL
        DEFAULT 'application/octet-stream'
        """
    )


    # =====================================================
    # MAKE SURE originalname IS NOT NULL
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE files
        MODIFY COLUMN originalname
        VARCHAR(255)
        NOT NULL
        DEFAULT ''
        """
    )


    # =====================================================
    # MAKE SURE storedname IS NOT NULL
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE files
        MODIFY COLUMN storedname
        VARCHAR(255)
        NOT NULL
        DEFAULT ''
        """
    )


    # =====================================================
    # MAKE SURE size IS NOT NULL
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE files
        MODIFY COLUMN size
        BIGINT
        NOT NULL
        DEFAULT 0
        """
    )


    # =====================================================
    # MAKE SURE path IS NOT NULL
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE files
        MODIFY COLUMN path
        VARCHAR(255)
        NOT NULL
        DEFAULT ''
        """
    )


    return changes


# =========================================================
# CREATE TABLES
# =========================================================

def createTables():

    db_config = DatabaseConnection()

    if db_config is None:

        return (
            "Database connection failed: "
            + getLastError()
        )

    cursor = None

    try:

        cursor = db_config.cursor()

        # Create users
        cursor.execute(USERS_TABLE)

        # Create notes
        cursor.execute(NOTES_TABLE)

        # Create files
        cursor.execute(FILES_TABLE)

        # Repair old files table
        changes = migrateFilesTable(cursor)

        # Save changes
        db_config.commit()


        if changes:

            return (
                "Tables created | "
                "files table repaired: "
                + ", ".join(changes)
            )


        return "Tables created successfully"


    except Exception as e:

        db_config.rollback()

        return (
            "Something wrong in "
            "database/tables.py-createTables: "
            + str(e)
        )


    finally:

        if cursor:
            cursor.close()

        db_config.close()