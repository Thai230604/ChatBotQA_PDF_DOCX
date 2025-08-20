import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from creat_vector import get_retriever, get_current_file

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model='gpt-4o',
    temperature=0.5,
)

# Template for document-based chat
doc_template = """
Bạn là chuyên gia trả lời câu hỏi

Đây là một vài dữ liệu tham khảo:
{review}

Đây là câu hỏi để trả lời:
{question}
"""

# Template for general chat (no document)
general_template = """
Bạn là một AI assistant thông minh và hữu ích. Hãy trả lời câu hỏi một cách tự nhiên và thân thiện.

Câu hỏi: {question}
"""

doc_prompt = ChatPromptTemplate.from_template(doc_template)
general_prompt = ChatPromptTemplate.from_template(general_template)

doc_chain = doc_prompt | client
general_chain = general_prompt | client

def get_chat_response(question):
    """
    Get response from AI - either document-based or general chat
    """
    retriever = get_retriever()
    current_file = get_current_file()
    
    if retriever is not None and current_file is not None:
        try:
            reviews = retriever.invoke(question)
            result = doc_chain.invoke({"review": reviews, "question": question})
            return {
                "response": result.content,
                "has_document": True,
                "current_file": current_file,
                "success": True
            }
        except Exception as e:
            return {
                "response": f"Lỗi khi xử lý câu hỏi về tài liệu: {str(e)}",
                "has_document": True,
                "current_file": current_file,
                "success": False
            }
    else:
        try:
            result = general_chain.invoke({"question": question})
            return {
                "response": result.content,
                "has_document": False,
                "current_file": None,
                "success": True
            }
        except Exception as e:
            return {
                "response": f"Lỗi khi xử lý câu hỏi: {str(e)}",
                "has_document": False,
                "current_file": None,
                "success": False
            }

# For testing
if __name__ == "__main__":
    while True:
        print("--------------------------------")
        question = input("Ask your question (q to quit): ")
        print("\n")
        if question == "q":
            break
            
        response = get_chat_response(question)
        print(f"Has document: {response['has_document']}")
        if response['current_file']:
            print(f"Current file: {response['current_file']}")
        print(f"Response: {response['response']}")
        print("\n")