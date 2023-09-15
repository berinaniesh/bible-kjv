# The following code is licensed under "The Unlicese"
# For more details, see http://unlicense.org/

import psycopg
import glob
import json
from tqdm import tqdm
import subprocess

conn = psycopg.connect(dbname="bibledev2")
cur = conn.cursor()


def reset_db():
    global conn
    global cur
    conn.close()
    subprocess.run(["./reset_db.sh"], shell=True, capture_output=True)
    conn = psycopg.connect(dbname="bibledev2")
    cur = conn.cursor()


def load_json(jason):
    with open(jason) as f:
        return json.loads(f.read())


book_names = load_json("Books.json")
books = glob.glob("*.json")
books.remove("Books.json")
books_json = [load_json(book) for book in books]


def get_chapters(name):
    for book_json in books_json:
        if book_json["book"] == name:
            return book_json["chapters"]

    return "Invalid"


def push_kjv():
    lang_id = cur.execute(
        """
                 INSERT INTO "Language" ("name") VALUES ('English') RETURNING "id"
                 """
    ).fetchone()[0]
    translation_id = cur.execute(
        """
                                  INSERT INTO "Translation" ("language_id", "name", "full_name", "year", "license", "description") VALUES (%s, %s, %s, %s, %s, %s) RETURNING "id"
                                  """,
        (
            lang_id,
            "KJV",
            "King James Version",
            "1611, revised 1769",
            "Public Domain",
            "https://en.wikipedia.org/wiki/King_James_Version",
        ),
    ).fetchone()[0]
    for book in book_names:
        cur.execute(
            """
                    INSERT INTO "TranslationBookName" ("translation_id", "book_id", "name", "long_name") VALUES 
                    (%s, (SELECT id from "Book" WHERE "name"=%s), %s, (SELECT "long_name" from "Book" WHERE "name"=%s))
                    """,
            (translation_id, book, book, book),
        )
    conn.commit()
    return translation_id


def insert_verses(t_id):
    for i in tqdm(range(len(book_names))):
        book_id = cur.execute(
            """
                              SELECT id from "Book" WHERE name=%s
                              """,
            (book_names[i],),
        ).fetchone()[0]
        chapters = get_chapters(book_names[i])
        for chapter in chapters:
            chapter_number = int(chapter["chapter"])
            chapter_id = cur.execute(
                """
                                     SELECT id from "Chapter" WHERE book_id=%s and chapter_number=%s
                                     """,
                (book_id, chapter_number),
            ).fetchone()[0]
            for verse in chapter["verses"]:
                verse_number = int(verse["verse"])
                verse_text = verse["text"]
                verse_id = cur.execute(
                    """SELECT id from "Verse" where chapter_id=%s and verse_number=%s""",
                    (chapter_id, verse_number),
                ).fetchone()[0]
                cur.execute(
                    """INSERT INTO "VerseText" ("translation_id", "verse_id", "verse") VALUES (%s, %s, %s)""",
                    (t_id, verse_id, verse_text),
                )
    conn.commit()


reset_db()

t_id = push_kjv()
insert_verses(t_id)

conn.close()
