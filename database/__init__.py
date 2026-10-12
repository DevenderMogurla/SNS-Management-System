from database.tables import createTables

from database.utilsDB import (
    # USERS
    getUserDataByEmail,
    insertUserRecord,
    updatePassword,

    # NOTES
    insertNote,
    getNotesByUser,
    searchNotes,
    getNotesCount,
    updateNote,
    deleteNote,

    # FILES
    insertFileRecord,
    getFilesByUser,
    searchFiles,
    getFilesCount,
    getFileById,
    updateFile,
    deleteFile
)