from backend.statement_analyzer import parse_and_analyze_statement
print("Executing statement parser offline with Mock Data...")
MOCK_CSV = "Date,Narration,Withdrawal Amt.,Closing Balance\\n01/01/24,TEST SHOP,100,900"
res = parse_and_analyze_statement(csv_content=MOCK_CSV)
print("Status:", res.get("status"))
if res.get("status") == "error":
    print(res)
else:
    print("Test Success! Analysis generated.")

