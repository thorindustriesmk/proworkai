import pymssql

server = '168.119.151.119\\MSSQLSERVER2016'
database = 'ProWork-Social'
username = 'vefacom_ProWorkSocial'
password = 'K1~jvc204'
conn = pymssql.connect(server=server, database=database, user=username, password=password)
cursor = conn.cursor()
cursor.execute("SELECT * FROM Individuals")
result = cursor.fetchall()
# Process the query result as needed


for r in result:
    print(r)

cursor.close()
conn.close()
