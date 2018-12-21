from sqlalchemy.orm import sessionmaker
import database_schema

DBSession = sessionmaker(bind=database_schema.engine)
session = DBSession()

categories = [
    'Soccer',
    'Basketball',
    'Baseball',
    'Frisbee',
    'Snowboarding',
    'Rock Climbing',
    'Football',
    'Skating',
    'Hockey',
]

for name in categories:
    c = database_schema.Category()
    c.name = name
    session.add(c)
session.commit()
