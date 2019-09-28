import pandas as pd
import numpy as np
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.environ['DATABASE_URL'])
print(os.environ['DATABASE_URL'])
db = scoped_session(sessionmaker(bind=engine))

def start():
    """
    Function: Import 2 tables to Posgresql database (user, email_list)
    Input: movies.csv
    Output:
        1. user_df ---- empty table with columns username and password (for teachers)
        2. email_list_df ---- empty table with columns movie, user, rating and description
    """

    user_df = pd.DataFrame(columns=['first_name','last_name','email','email_password','password','email_type'], dtype = 'str')
    user_df.to_sql('users', engine, index=False, method='multi')

    email_list_df = pd.DataFrame(columns=['user_email', 'class', 'names', 'emails','total'], dtype='str')
    email_list_df.to_sql('email_lists', engine, index=False, method='multi')

start()
