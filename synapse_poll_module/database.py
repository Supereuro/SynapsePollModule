from psycopg2.extras import execute_values, RealDictCursor

CREATE_POLLS = """CREATE TABLE IF NOT EXISTS polls
(id SERIAL PRIMARY KEY, title TEXT, description TEXT, owner_user TEXT, room_id TEXT, ended BOOLEAN DEFAULT false,
 archived BOOLEAN DEFAULT false, favoritetext TEXT, favoritecount INTEGER);"""
CREATE_OPTIONS = """CREATE TABLE IF NOT EXISTS options
(id SERIAL PRIMARY KEY, option_text TEXT, poll_id INTEGER);"""
CREATE_VOTES = """CREATE TABLE IF NOT EXISTS votes (user_name TEXT, option_id INTEGER, userchoice BOOLEAN,
CONSTRAINT votekey UNIQUE (user_name, option_id));"""
CREATE_PARTICIPANTS = """CREATE TABLE IF NOT EXISTS participants (id SERIAL PRIMARY KEY, user TEXT, poll_id INTEGER);"""
SELECT_ALL_POLLS = "SELECT * FROM polls;"
SELECT_POLL = "SELECT * FROM polls WHERE polls.id = %s;"
SELECT_POLLID_FROM_OPTION = """SELECT poll_id FROM polls 
JOIN options on polls.option_id == options.option_id 
WHERE polls.id = %s;"""
SELECT_POLL_WITH_OPTIONS = """SELECT * FROM polls
JOIN options ON polls.id = options.poll_id
WHERE polls.id = %s;"""
SELECT_OPTIONS = """SELECT o.id,o.option_text,o.poll_id, coalesce(votes.votes,'[]')as votes 
FROM options o
left JOIN lateral(select json_agg(json_build_object('user_name', votes.user_name, 'option_id',votes.option_id,
'userchoice', votes.userchoice)) as votes from votes where votes.option_id = o.id ) votes on true 
WHERE poll_id = %s;"""
SELECT_OPTIONS_FAVORITE = """select option_text,count(*) from options join votes on options.id = votes.option_id 
and votes.userchoice = 't' where options.poll_id = %s group by option_text;"""
INSERT_POLL_RETURN_ID = """INSERT INTO polls (title, description, owner_user, room_id, ended, archived) 
VALUES (%s, %s, %s, %s, DEFAULT, DEFAULT) RETURNING id; """
INSERT_OPTION = "INSERT INTO options (option_text, poll_id) VALUES %s;"
SELECT_VOTES = """SELECT * FROM votes WHERE votes.option_id = %s"""
INSERT_VOTE = """INSERT INTO votes (user_name, option_id, userchoice) VALUES (%s, %s, %s) ON CONFLICT 
(user_name, option_id) DO UPDATE SET userchoice = EXCLUDED.userchoice;"""
INSERT_PARTICIPANT = "INSERT INTO participants (user, poll_id) VALUES %s;"
UPDATE_POLL_FAVORITE = """UPDATE polls SET favoritetext = %s, favoritecount = %s WHERE id = %s;"""
DELETE_FROM_VOTES = """DELETE FROM votes where option_id IN (SELECT id FROM options WHERE poll_id = %s);"""
DELETE_FROM_OPTIONS = """DELETE FROM options where poll_id = %s;"""
DELETE_POLL = """DELETE FROM polls WHERE id = %s;"""


def create_tables(connection):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_POLLS)
            cursor.execute(CREATE_OPTIONS)
            cursor.execute(CREATE_VOTES)


def get_polls(connection):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(SELECT_ALL_POLLS)
            return cursor.fetchall()


def get_poll(connection, poll_id):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(SELECT_POLL, (poll_id,))
            return cursor.fetchall()


def delete_poll(connection, pollid):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(DELETE_FROM_VOTES, [pollid])
            cursor.execute(DELETE_FROM_OPTIONS, [pollid])
            cursor.execute(DELETE_POLL, [pollid])


def get_options(connection, poll_id):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(SELECT_OPTIONS, (poll_id,))
            return cursor.fetchall()


def get_votes(connection, poll_id):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(SELECT_VOTES, (poll_id,))
            return cursor.fetchall()


def create_poll(connection, title, description, owner, roomid, options):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_POLL_RETURN_ID, (title, description, owner, roomid))

            poll_id = cursor.fetchone()[0]
            option_values = [(option_text, poll_id) for option_text in options]

            execute_values(cursor, INSERT_OPTION, option_values)


def add_poll_vote(connection, user, option_id, userchoice, pollid):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_VOTE, (user, option_id, userchoice))

            cursor.execute(SELECT_OPTIONS_FAVORITE, [pollid])
            optionsfav = cursor.fetchall()
            favcount = 0
            favtext = ""
            if cursor.rowcount == 1:
                for row in optionsfav:
                    if row[1] > favcount:
                        favcount = row[1]
                        favtext = row[0]
                cursor.execute(UPDATE_POLL_FAVORITE, (favtext, favcount, pollid))
            elif cursor.rowcount > 1:
                for row in optionsfav:
                    if row[1] > favcount:
                        favcount = row[1]
                        favtext = row[0]
                    elif row[1] == favcount:
                        favcount = 0
                        favtext = ""
                        break
                cursor.execute(UPDATE_POLL_FAVORITE, (favtext, favcount, pollid))
            else:
                cursor.execute(UPDATE_POLL_FAVORITE, ("", 0, pollid))
