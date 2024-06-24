import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load the model and tokenizer
base_model = "codellama/CodeLlama-34b-hf"

# Load the model without quantization
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    torch_dtype=torch.float32,  # Use float32 instead of float16
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(base_model, padding_side="left")
tokenizer.pad_token_id = tokenizer.eos_token_id

# Load the fine-tuned adapter
output_dir = "/home/model/lstcheck/"
model = PeftModel.from_pretrained(model, output_dir)
model.eval()

# Function to extract schema from SQLite database
def extract_schema_sqlite(filepath):
    conn = sqlite3.connect(filepath)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    schema = "\n".join(row[0] for row in cursor.fetchall())
    conn.close()
    return schema

# Function to clean and format SQL query
def clean_and_format_query(query):
    if not query.strip().endswith(';'):
        query += ';'
    keywords = ["select", "from", "where", "insert", "into", "values", "update", "set", "delete", "create", "table", "drop", "alter", "join", "inner", "left", "right", "full", "on", "group", "by", "having", "order", "asc", "desc", "and", "or", "not", "in", "is", "null", "like", "between", "exists", "distinct"]
    formatted_query = " ".join([word.upper() if word.lower() in keywords else word for word in query.split()])
    return formatted_query

# Function to execute SQL query
def execute_sql_query(query, conn):
    query = clean_and_format_query(query)
    try:
        query_result = pd.read_sql_query(query, conn)
        return query_result
    except Exception as e:
        return str(e)

# Function to generate text from SQL query result
def generate_text_from_result(query_result, user_question):
    result_str = query_result.to_string(index=False)
    prompt = f"""
    Given the SQL query result and the user's question, generate a natural language description.
    ### User Question:
    {user_question}
    ### SQL Query Result:
    {result_str}
    ### Natural Language Description:
    """
    model_input = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True).to(model.device)
    with torch.no_grad():
        output_tokens = model.generate(**model_input, max_new_tokens=150, pad_token_id=tokenizer.eos_token_id)
        generated_text = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
    return generated_text.split("### Natural Language Description:")[-1].strip()

# Example usage:
if _name_ == "_main_":
    # Example SQLite database file path
    db_filepath = "example.db"
    
    # Extract schema
    schema = extract_schema_sqlite(db_filepath)
    print(f"Database Schema:\n{schema}")

    # User question
    user_question = "What is the total sales for the last quarter?"

    # Generate SQL query
    prompt = f"""
    You are a powerful text-to-SQL model. Your job is to answer questions about a database. You are given a question and context regarding one or more tables.
    You must output the SQL query that answers the question.
    ### Input:
    {user_question}
    ### Context:
    {schema}
    ### Response:
    """
    model_input = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True).to(model.device)
    with torch.no_grad():
        output_tokens = model.generate(**model_input, max_new_tokens=100, pad_token_id=tokenizer.eos_token_id)
        generated_text = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
    sql_query = generated_text.split("### Response:\n")[-1].strip()
    print(f"Generated SQL Query:\n{sql_query}")

    # Execute SQL query
    conn = sqlite3.connect(db_filepath)
    result = execute_sql_query(sql_query, conn)
    conn.close()

    if isinstance(result, str):
        print(f"Error: {result}")
    else:
        print(f"Query Result:\n{result}")

        # Generate natural language description
        interpreted_result = generate_text_from_result(result, user_question)
        print(f"Natural Language Description:\n{interpreted_result}")