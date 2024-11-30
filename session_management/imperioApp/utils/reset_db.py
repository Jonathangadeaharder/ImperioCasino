from .. import db  # Relative import

def reset_database():
    db.drop_all()
    db.create_all()
    # Optionally, add initial data here

if __name__ == '__main__':
    reset_database()
    print("Database reset completed.")
