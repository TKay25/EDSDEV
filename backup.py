            select_query = '''
                SELECT * FROM login
                WHERE EmployeeNumber = %s AND   Password = %s
            '''
    
            login_data = (email, password)
            connection.reconnect()
            cursor = connection.cursor()
            cursor.execute(select_query, login_data)
            row = cursor.fetchone()
    
            if row:
                query = f"SELECT id, firstname, surname, email, privileges, leaveapprovername, currentleavedaysbalance FROM {table_name} WHERE email = %s;"
                cursor.execute(query, (email_to_search,))
                result = cursor.fetchall()

                # Process the results
                for row in result:
                    print(row)