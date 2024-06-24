from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load the model and tokenizer
base_model = "codellama/CodeLlama-34b-hf"
quant_config = BitsAndBytesConfig(load_in_8bit=True)
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    quantization_config=quant_config,
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(base_model, padding_side="left")
tokenizer.pad_token_id = tokenizer.eos_token_id

# Load the fine-tuned adapter
output_dir = "/home/model/lstcheck/"
model = PeftModel.from_pretrained(model, output_dir)
model.eval()

def extract_schema_sqlite(filepath):
    conn = sqlite3.connect(filepath)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    schema = "\n".join(row[0] for row in cursor.fetchall())
    conn.close()
    return schema

# Include other necessary functions here

@app.route('/upload_database', methods=['POST'])
def upload_database():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.db'):
        filename = 'uploaded_database.db'
        file.save(filename)
        return jsonify({'message': 'Database uploaded successfully'}), 200
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/process_question', methods=['POST'])
def process_question():
    user_question = request.json['question']
    db_filepath = "uploaded_database.db"
    
    if not os.path.exists(db_filepath):
        return jsonify({'error': 'No database uploaded yet'}), 400
    
    # Extract schema
    schema = extract_schema_sqlite(db_filepath)
    
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
    
    # Execute SQL query
    conn = sqlite3.connect(db_filepath)
    result = execute_sql_query(sql_query, conn)
    conn.close()
    
    if isinstance(result, str):
        return jsonify({'error': result})
    else:
        # Generate natural language description
        interpreted_result = generate_text_from_result(result, user_question)
        return jsonify({
            'query': sql_query,
            'result': result.to_dict('records'),
            'interpretation': interpreted_result
        })

if __name__ == '__main__':
    app.run(debug=True)