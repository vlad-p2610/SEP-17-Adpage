from chdb import session

sess = session.Session("./chdb_data")   # creates the folder if missing

sess.query("CREATE DATABASE IF NOT EXISTS mydb")
sess.query("""
    CREATE TABLE IF NOT EXISTS mydb.mytable (
        id UInt32,
        name String,
        value Float64
    ) ENGINE = MergeTree ORDER BY id
""")
sess.query("""
    INSERT INTO mydb.mytable VALUES
    (1, 'a', 1.5), (2, 'b', 2.5), (3, 'c', 3.5)
""")

df = sess.query("SELECT * FROM mydb.mytable", "DataFrame")
print(df)