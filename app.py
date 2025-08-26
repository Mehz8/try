import streamlit as st
import csv
import os
import re
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

# Page configuration
st.set_page_config(
    page_title="FraudShield - Digital Safe for Your Funds",
    page_icon="🛡️",
    layout="wide"
)

# File to store reports
DB_FILE = "fraud_reports.csv"

# Initialize CSV if not exists
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Type", "Detail", "Description"])

# Load AI model (with caching to avoid reloading on every interaction)
@st.cache_resource
def load_fraud_model():
    try:
        # Using a distilled model that's smaller and faster
        model_name = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
        classifier = pipeline("text-classification", 
                             model=model_name,
                             tokenizer=model_name)
        return classifier
    except Exception as e:
        st.sidebar.warning(f"AI model could not be loaded: {str(e)}")
        return None

# AI-powered fraud analysis using Transformers
def ai_transformers_analysis(text):
    """
    Analyze text using Hugging Face Transformers model
    """
    try:
        classifier = load_fraud_model()
        if classifier is None:
            return "AI model not available. Using basic analysis.", []
        
        # Perform classification
        result = classifier(text)
        label = result[0]['label']
        score = result[0]['score']
        
        # Map model outputs to fraud risk levels
        if label == "negative":
            return f"RED - High Fraud Risk ❌ (confidence: {score:.2%})", []
        elif label == "neutral":
            return f"YELLOW - Moderate Risk ⚠️ (confidence: {score:.2%})", []
        else:
            return f"GREEN - Low Risk ✅ (confidence: {score:.2%})", []
            
    except Exception as e:
        return f"Analysis error: {str(e)}", []

# Lightweight AI simulation (fallback)
def lightweight_ai_analysis(text):
    """
    A simplified AI-like analysis using pattern matching and heuristics
    """
    text_lower = text.lower()
    
    # Score based on fraud indicators
    score = 0
    indicators = []
    
    # High return promises
    high_return_terms = ["% return", "double your", "triple your", "10x", "100%", "guaranteed", "risk-free"]
    for term in high_return_terms:
        if term in text_lower:
            score += 2
            indicators.append(f"High return promise: '{term}'")
    
    # Urgency language
    urgency_terms = ["limited time", "act now", "today only", "don't miss out", "once in a lifetime"]
    for term in urgency_terms:
        if term in text_lower:
            score += 1
            indicators.append(f"Creates urgency: '{term}'")
    
    # Request for personal information
    personal_info_terms = ["bank details", "password", "credit card", "social security", "personal information"]
    for term in personal_info_terms:
        if term in text_lower:
            score += 3
            indicators.append(f"Requests personal info: '{term}'")
    
    # Crypto scams
    crypto_terms = ["crypto", "bitcoin", "blockchain", "nft", "etherium"]
    for term in crypto_terms:
        if term in text_lower:
            score += 1
            indicators.append(f"Involves cryptocurrency: '{term}'")
    
    # Investment jargon
    investment_terms = ["investment", "portfolio", "return on investment", "roi", "dividend"]
    for term in investment_terms:
        if term in text_lower:
            score += 1
            indicators.append(f"Investment-related: '{term}'")
    
    # Determine risk level
    if score >= 5:
        confidence = min(95, 70 + score * 5)
        return f"RED - Likely Fraudulent ❌ (confidence: {confidence}%)", indicators
    elif score >= 3:
        confidence = min(85, 50 + score * 10)
        return f"YELLOW - Suspicious ⚠️ (confidence: {confidence}%)", indicators
    else:
        confidence = max(60, 100 - score * 8)
        return f"GREEN - Likely Safe ✅ (confidence: {confidence}%)", indicators

# Basic Offer Analyzer Logic
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
            # Extract numbers before % sign
            parts = text_lower.split("%")
            if parts:
                numbers = re.findall(r'\d+', parts[0])
                if numbers:
                    num = int(numbers[-1])
                    if num >= 5:
                        return "RED - Not Safe ❌"
        except:
            pass

    return "GREEN - Likely Safe ✅"

# Main app
def main():
    st.title("FraudShield - Digital Safe for Your Funds 🛡️")
    
    # Display model status in sidebar
    model = load_fraud_model()
    if model:
        st.sidebar.success("🤖 AI Model Loaded Successfully")
    else:
        st.sidebar.warning("⚠️ Using Lightweight Analysis (AI model not available)")
    
    # Navigation
    menu = ["Search", "Report", "Offer Analyzer"]
    choice = st.sidebar.selectbox("Navigation", menu)
    
    # Search page
    if choice == "Search":
        st.header("Search Fraud Database")
        query = st.text_input("Enter phone number, UPI ID, or website to search")
        
        if st.button("Search"):
            if query:
                results = []
                try:
                    with open(DB_FILE, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if query.lower() in row["Detail"].lower():
                                results.append(row)
                    
                    if results:
                        st.success(f"Found {len(results)} report(s) for '{query}'")
                        df = pd.DataFrame(results)
                        st.dataframe(df)
                    else:
                        st.success(f"No fraud reports found for '{query}' ✅")
                except Exception as e:
                    st.error(f"Error reading database: {str(e)}")
            else:
                st.warning("Please enter a search query")
    
    # Report page
    elif choice == "Report":
        st.header("Report Fraud")
        
        with st.form("report_form"):
            ftype = st.selectbox("Type", ["Phone", "UPI", "Website", "Other"])
            detail = st.text_input("Detail (e.g., Number/ID)")
            desc = st.text_area("Description")
            
            submitted = st.form_submit_button("Submit Report")
            
            if submitted:
                if detail and desc:
                    try:
                        with open(DB_FILE, "a", newline="", encoding="utf-8") as f:
                            writer = csv.writer(f)
                            writer.writerow([ftype, detail, desc])
                        st.success("✅ Report submitted successfully!")
                    except Exception as e:
                        st.error(f"Error saving report: {str(e)}")
                else:
                    st.warning("Please fill in all required fields")
    
    # Offer Analyzer page
    elif choice == "Offer Analyzer":
        st.header("Offer Analyzer")
        
        analysis_options = ["Basic Analysis", "AI Analysis"]
        if model:
            analysis_options.append("Transformers AI Analysis")
        
        analysis_type = st.radio("Analysis Type", analysis_options)
        
        offer = st.text_area("Enter offer text (e.g., Invest 10 lakhs, 10% monthly return)", height=100)
        
        if st.button("Analyze Offer"):
            if offer:
                if analysis_type == "Transformers AI Analysis" and model:
                    with st.spinner("🤖 AI is analyzing the offer..."):
                        result, indicators = ai_transformers_analysis(offer)
                    st.subheader("Analysis Result")
                    
                    if "RED" in result:
                        st.error(result)
                    elif "YELLOW" in result:
                        st.warning(result)
                    else:
                        st.success(result)
                    
                elif analysis_type == "AI Analysis":
                    result, indicators = lightweight_ai_analysis(offer)
                    st.subheader("Analysis Result")
                    
                    if "RED" in result:
                        st.error(result)
                    elif "YELLOW" in result:
                        st.warning(result)
                    else:
                        st.success(result)
                    
                    if indicators:
                        st.subheader("Detection Indicators")
                        for indicator in indicators:
                            st.write(f"- {indicator}")
                else:
                    result = analyze_offer(offer)
                    st.subheader("Analysis Result")
                    
                    if "RED" in result:
                        st.error(result)
                    elif "YELLOW" in result:
                        st.warning(result)
                    else:
                        st.success(result)
            else:
                st.warning("Please enter an offer to analyze")

# Run the app
if __name__ == "__main__":
    main()