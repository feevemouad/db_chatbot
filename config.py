from langchain_ollama import ChatOllama

SELECTED_DBS = ["postgres", "oracle", "mysql"]

class Config:
    llm = ChatOllama(model="llama3.1", temperature=0.0, top_p=0.1)
    db_uri = "postgresql://postgres:postgres@localhost/lotterydb"
    selected_db = "postgres"
    if selected_db not in SELECTED_DBS:
        raise Exception(
            f"Selected DB {selected_db} not recognized. The possible values are: {SELECTED_DBS}."
        )


cfg = Config()
