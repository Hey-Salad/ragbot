#!/usr/bin/env python3
"""
Test PDF upload and query functionality
"""

from user_rag_system import UserRAGSystem
import PyPDF2
import io

def test_pdf_processing():
    """Test PDF processing with user RAG system"""
    print("🧪 Testing PDF Processing\n")
    
    # Initialize user RAG system
    user_rag = UserRAGSystem()
    
    # Create a test user first
    test_phone = "+1234567890"
    user = user_rag.user_manager.get_or_create_user(test_phone, "Test User")
    test_user_id = user["user_id"]
    print(f"✅ Created test user: {test_user_id}\n")
    
    # Create a sample PDF-like text (simulating extracted PDF content)
    sample_pdf_text = """
    Machine Learning Best Practices
    
    1. Data Preprocessing
    Always clean and normalize your data before training. This includes:
    - Handling missing values
    - Scaling features
    - Encoding categorical variables
    
    2. Model Selection
    Choose the right algorithm for your problem:
    - Classification: Random Forest, SVM, Neural Networks
    - Regression: Linear Regression, Gradient Boosting
    - Clustering: K-Means, DBSCAN
    
    3. Hyperparameter Tuning
    Use techniques like Grid Search or Random Search to optimize model parameters.
    
    4. Cross-Validation
    Always validate your model using k-fold cross-validation to ensure generalization.
    
    5. Feature Engineering
    Create meaningful features from raw data to improve model performance.
    """
    
    print("📄 Adding sample PDF content to user's knowledge base...")
    metadata = {
        "source": "test_upload",
        "type": "pdf",
        "filename": "ml_best_practices.pdf"
    }
    
    result = user_rag.add_document_for_user(test_user_id, sample_pdf_text, metadata)
    print(f"✅ {result}\n")
    
    # Test queries
    test_queries = [
        "What are the best practices for data preprocessing?",
        "Which algorithms should I use for classification?",
        "Tell me about cross-validation",
        "What is feature engineering?"
    ]
    
    print("🤖 Testing queries against uploaded PDF:\n")
    for query in test_queries:
        print(f"❓ Question: {query}")
        response = user_rag.query_with_context(test_user_id, query)
        print(f"💬 Answer: {response}\n")
        print("-" * 80 + "\n")
    
    # Get stats
    print("📊 User Statistics:")
    stats = user_rag.get_user_stats(test_user_id)
    print(f"Total documents: {stats.get('total_documents', 0)}")
    print(f"Total messages: {stats.get('total_messages', 0)}")
    
    print("\n✅ PDF processing test complete!")

if __name__ == "__main__":
    test_pdf_processing()
