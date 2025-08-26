from flask import Flask, render_template_string, request
import csv
import os
from transformers import pipeline

app = Flask(__name__)

# File to store reports
DB_FILE = "fraud_reports.csv"

# Initialize CSV if not exists
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Type", "Detail", "Description"])

# Load AI model once (zero-shot classification works well here)
try:
    classifier = pipeline("zero-shot-classification", model="yiyanghkust/finbert-tone")
    AI_AVAILABLE = True
except:
    AI_AVAILABLE = False
    print("AI model could not be loaded. Using basic analysis only.")

# ---------- Offer Analyzer Logic ----------
def analyze_offer(text):
    text_lower = text.lower()

    # Red flags
    red_keywords = ["double money", "guaranteed return", "crypto doubling",
                    "ponzi", "multi level", "10% monthly", "20% monthly", "risk free"]
    for word in red_keywords:
        if word in text_lower:
            return "RED - Not Safe ❌"

    # Suspicious (Yellow)
    yellow_keywords = ["fast profit", "investment scheme", "limited offer",
                       "get rich", "quick money", "unrealistic"]
    for word in yellow_keywords:
        if word in text_lower:
            return "YELLOW - Suspicious ⚠️"

    # If contains high monthly return %
    if "%" in text_lower:
        try:
            num = int(text_lower.split("%")[0].split()[-1])
            if num >= 5:
                return "RED - Not Safe ❌"
        except:
            pass

    return "GREEN - Likely Safe ✅"

def ai_analyze_offer(text):
    if not AI_AVAILABLE:
        return "AI analysis not available. Using basic analysis.", analyze_offer(text)
    
    labels = ["Safe investment", "Suspicious offer", "Fraudulent scheme"]
    result = classifier(text, candidate_labels=labels)
    best = result["labels"][0]
    score = result["scores"][0]
    
    if "Fraudulent" in best:
        return f"RED - Likely Fraudulent ❌ (confidence: {round(score*100, 2)}%)"
    elif "Suspicious" in best:
        return f"YELLOW - Suspicious ⚠️ (confidence: {round(score*100, 2)}%)"
    else:
        return f"GREEN - Likely Safe ✅ (confidence: {round(score*100, 2)}%)"

# ---------- Templates (All in One File for Simplicity) ----------
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>FraudShield MVP</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        nav a { margin: 10px; text-decoration: none; padding: 6px 12px; background: #007BFF; color: white; border-radius: 6px; }
        nav a:hover { background: #0056b3; }
        .box { background: white; padding: 20px; margin-top: 20px; border-radius: 10px; box-shadow: 0px 2px 6px rgba(0,0,0,0.1); }
        input, textarea { width: 100%; padding: 8px; margin: 6px 0; }
        button { padding: 8px 14px; background: green; color: white; border: none; border-radius: 6px; cursor: pointer; }
        button:hover { background: darkgreen; }
        .toggle-btn { background: #6c757d; }
        .toggle-btn:hover { background: #5a6268; }
        .ai-active { background: #17a2b8; }
        .ai-active:hover { background: #138496; }
    </style>
</head>
<body>
    <h1>FraudShield - Digital Safe for Your Funds</h1>
    <nav>
        <a href="/">Search</a>
        <a href="/report">Report</a>
        <a href="/analyze">Offer Analyzer</a>
    </nav>

    <div class="box">
        {{ content|safe }}
    </div>
</body>
</html>
"""


@app.route("/")
def home():
    content = """
    <h2>Search Fraud Check</h2>
    <form method="post" action="/search">
        <input type="text" name="query" placeholder="Enter phone/UPI/website" required>
        <button type="submit">Search</button>
    </form>
    """
    return render_template_string(TEMPLATE, content=content)


@app.route("/search", methods=["POST"])
def search():
    query = request.form["query"].lower()
    results = []

    with open(DB_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if query in row["Detail"].lower():
                results.append(row)

    if results:
        content = f"<h2>Search Results for '{query}'</h2><ul>"
        for r in results:
            content += f"<li><b>{r['Type']}</b> - {r['Detail']} : {r['Description']}</li>"
        content += "</ul>"
    else:
        content = f"<h2>No fraud reports found for '{query}' ✅</h2>"

    return render_template_string(TEMPLATE, content=content)


@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        ftype = request.form["type"]
        detail = request.form["detail"]
        desc = request.form["description"]

        with open(DB_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([ftype, detail, desc])

        content = "<h2>✅ Report submitted successfully!</h2>"
    else:
        content = """
        <h2>Report Fraud</h2>
        <form method="post">
            <input type="text" name="type" placeholder="Type (Phone/UPI/Website)" required>
            <input type="text" name="detail" placeholder="Detail (e.g. Number/ID)" required>
            <textarea name="description" placeholder="Description" required></textarea>
            <button type="submit">Submit</button>
        </form>
        """

    return render_template_string(TEMPLATE, content=content)


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    use_ai = request.args.get('ai', '0') == '1'
    
    if request.method == "POST":
        offer = request.form["offer"]
        use_ai = request.form.get('use_ai', '0') == '1'
        
        if use_ai:
            result = ai_analyze_offer(offer)
            analysis_type = "AI Analysis"
        else:
            result = analyze_offer(offer)
            analysis_type = "Basic Analysis"
            
        content = f"""
        <h2>Offer Analysis</h2>
        <p><strong>Offer:</strong> {offer}</p>
        <p><strong>Analysis Type:</strong> {analysis_type}</p>
        <h3>Result: {result}</h3>
        <form method="post">
            <textarea name="offer" placeholder="Enter offer text (e.g. Invest 10 lakhs, 10% monthly return)" required>{offer}</textarea>
            <input type="hidden" name="use_ai" value="{1 if use_ai else 0}">
            <button type="submit" class="{'ai-active' if use_ai else ''}" onclick="this.form.querySelector('input[name=use_ai]').value='{1 if not use_ai else 0}'">
                {'Switch to Basic Analysis' if use_ai else 'Switch to AI Analysis'}
            </button>
            <button type="submit">Re-analyze</button>
        </form>
        """
    else:
        ai_param = '1' if use_ai else '0'
        content = f"""
        <h2>Offer Analyzer</h2>
        <form method="post">
            <textarea name="offer" placeholder="Enter offer text (e.g. Invest 10 lakhs, 10% monthly return)" required></textarea>
            <input type="hidden" name="use_ai" value="{ai_param}">
            <button type="submit" class="{'ai-active' if use_ai else 'toggle-btn'}" onclick="this.form.querySelector('input[name=use_ai]').value='{1 if not use_ai else 0}'">
                {'Switch to Basic Analysis' if use_ai else 'Switch to AI Analysis'}
            </button>
            <button type="submit">Analyze</button>
        </form>
        """
        
        if not AI_AVAILABLE:
            content += "<p style='color: red;'>Note: AI analysis is currently unavailable. Using basic analysis only.</p>"

    return render_template_string(TEMPLATE, content=content)


if __name__ == "__main__":
    app.run(debug=True)