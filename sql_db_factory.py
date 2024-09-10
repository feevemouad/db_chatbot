from sql_analyzer.config import cfg
from langchain.sql_database import SQLDatabase

def sql_db_factory() -> SQLDatabase:
    if cfg.selected_db in ["postgres", "oracle", "mysql"]:
        return SQLDatabase.from_uri(cfg.db_uri, view_support=True)
    else:
        raise Exception(f"Could not create sql database factory: {cfg.selected_db}")


if __name__ == "__main__":
    sql_database = sql_db_factory()