from backend.statement_analyzer import parse_and_analyze_statement
print("Executing statement parser offline...")
res = parse_and_analyze_statement(file_path="backend/statement.csv")
print("Status:", res.get("status"))
if res.get("status") == "error":
    print(res)
