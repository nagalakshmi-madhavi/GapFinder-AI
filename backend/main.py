
import os
import json
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from groq import Groq
from dotenv import load_dotenv

from rag import extract_pdf_text
from vector_store import VectorStore


# Load API key
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("Groq API key is missing. Check your .env file.")

client = Groq(api_key=api_key)


# Create FastAPI application
app = FastAPI(
    title="GapFinder AI",
    description="AI-powered student knowledge gap analysis platform",
    version="1.0.0"
)


# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
   allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://gap-finder-ai-ten.vercel.app"
],
    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class ChatRequest(BaseModel):
    message: str


class QuizRequest(BaseModel):
    topic: str
    number_of_questions: int = Field(default=5, ge=1, le=10)


class QuizSubmitRequest(BaseModel):
    answers: dict[str, str]


# Initialize storage
vector_store = VectorStore()

latest_quiz = []
latest_quiz_topic = ""
latest_evaluation = None


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to GapFinder AI"
    }


# Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# PDF upload endpoint
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    global latest_quiz
    global latest_quiz_topic
    global latest_evaluation

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file"
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty"
        )

    try:
        chunks = extract_pdf_text(file_bytes)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No readable text found in this PDF"
            )

        vector_store.add_documents(chunks)

        # Clear previous quiz and evaluation
        latest_quiz = []
        latest_quiz_topic = ""
        latest_evaluation = None

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(error)}"
        )

    return {
        "filename": file.filename,
        "total_chunks": len(chunks),
        "total_pages": len(set(chunk["page"] for chunk in chunks)),
        "message": "PDF uploaded and indexed successfully"
    }


# Extract topics from uploaded study material
@app.post("/topics")
def extract_topics():

    if not vector_store.chunks:
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF first"
        )

    all_topics = []
    batch_size = 5
    chunks = vector_store.chunks

    try:
        for start in range(0, len(chunks), batch_size):

            batch = chunks[start:start + batch_size]

            context = ""

            for item in batch:
                context += (
                    f"\n[Page {item['page']}]\n"
                    f"{item['text']}\n"
                )

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an academic syllabus analyzer. "
                            "Extract units, topics and subtopics ONLY "
                            "from the provided document. "
                            "Do not invent topics or page numbers. "
                            "Return valid JSON only in this format: "
                            '{"units":[{"unit":"Unit name",'
                            '"topics":[{"topic":"Topic name",'
                            '"subtopics":["Subtopic 1"],'
                            '"pages":[1,2]}]}]}'
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            "Extract topics from this document section. "
                            "Preserve the original page numbers.\n"
                            + context
                        )
                    }
                ],
                response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "topic_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "units": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "unit": {"type": "string"},
                            "topics": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "topic": {"type": "string"},
                                        "subtopics": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "pages": {
                                            "type": "array",
                                            "items": {"type": "integer"}
                                        }
                                    },
                                    "required": [
                                        "topic", "subtopics", "pages"
                                    ],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["unit", "topics"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["units"],
            "additionalProperties": False
        }
    }
}
            )

            result = json.loads(
                response.choices[0].message.content
            )

            all_topics.extend(result.get("units", []))

            print(f"Processed batch {start // batch_size + 1}")

            if start + batch_size < len(chunks):
                time.sleep(25)

        # Merge duplicate units and topics
        merged_units = {}

        for unit in all_topics:

            unit_name = unit.get("unit", "Other Topics")

            if unit_name not in merged_units:
                merged_units[unit_name] = {}

            for topic in unit.get("topics", []):

                topic_name = topic.get("topic", "Unknown Topic")

                if topic_name not in merged_units[unit_name]:
                    merged_units[unit_name][topic_name] = {
                        "topic": topic_name,
                        "subtopics": [],
                        "pages": []
                    }

                existing = merged_units[unit_name][topic_name]

                existing["subtopics"] = list(dict.fromkeys(
                    existing["subtopics"] + topic.get("subtopics", [])
                ))

                existing["pages"] = sorted(set(
                    existing["pages"] + topic.get("pages", [])
                ))

        final_units = []

        for unit_name, topics in merged_units.items():
            final_units.append({
                "unit": unit_name,
                "topics": list(topics.values())
            })

        return {
            "message": "Complete document topic extraction successful",
            "total_chunks_processed": len(chunks),
            "total_units": len(final_units),
            "topic_map": {
                "units": final_units
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Topic extraction failed: {str(error)}"
        )


# RAG-based chatbot
@app.post("/chat")
def chat(request: ChatRequest):

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a message"
        )

    results = vector_store.search(
        request.message,
        top_k=4
    )

    if not results:
        return {
            "answer": (
                "Please upload a readable PDF first. "
                "I need study material to answer your question."
            )
        }

    context = ""

    for item in results:
        context += (
            f"\n[Page {item['page']}]\n"
            f"{item['text']}\n"
        )

    try:
        response = client.chat.completions.create(
           model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are GapFinder AI, a student study assistant. "
                        "Answer questions ONLY using the provided document context. "
                        "Do not use outside knowledge. "
                        "If the answer is not available in the context, "
                        "clearly say that the uploaded material does not contain "
                        "enough information to answer. "
                        "Include page citations such as [Page 2] in your answer."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Document context:\n{context}\n\n"
                        f"Student question: {request.message}"
                    )
                }
            ]
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": [
                {
                    "page": item["page"],
                    "similarity": round(item["score"], 3)
                }
                for item in results
            ]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"AI response failed: {str(error)}"
        )


# Quiz generation endpoint
@app.post("/quiz/generate")
def generate_quiz(request: QuizRequest):

    global latest_quiz
    global latest_quiz_topic
    global latest_evaluation

    if not request.topic.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a topic"
        )

    results = vector_store.search(
        request.topic,
        top_k=8
    )

    if not results:
        raise HTTPException(
            status_code=400,
            detail="Please upload study material first"
        )

    context = ""

    for item in results:
        context += (
            f"\n[Page {item['page']}]\n"
            f"{item['text']}\n"
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an educational quiz generator. "
                        "Generate MCQ questions ONLY from the provided study material. "
                        "Do not use outside knowledge. "
                        "Generate exactly the requested number of questions. "
                        "Each question must have exactly four options. "
                        "Only one option must be correct. "
                        "Include a short explanation and source page. "
                        "Return valid JSON only in this format: "
                        '{"questions":[{"question":"Question",'
                        '"options":{"A":"Option 1","B":"Option 2",'
                        '"C":"Option 3","D":"Option 4"},'
                        '"correct_answer":"A",'
                        '"explanation":"Explanation",'
                        '"page":1}]}'
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate exactly {request.number_of_questions} "
                        f"MCQ questions about {request.topic}.\n"
                        f"Study material:\n{context}"
                    )
                }
            ],
            response_format={"type": "json_object"}
        )

        quiz = json.loads(
            response.choices[0].message.content
        )

        questions = quiz.get("questions", [])

        if len(questions) != request.number_of_questions:
            raise ValueError(
                "AI did not generate the requested number of questions"
            )

        for question in questions:

            if not all(
                key in question
                for key in [
                    "question",
                    "options",
                    "correct_answer",
                    "explanation",
                    "page"
                ]
            ):
                raise ValueError(
                    "Generated question has missing fields"
                )

            if set(question["options"].keys()) != {"A", "B", "C", "D"}:
                raise ValueError(
                    "Each question must have exactly four options"
                )

            if question["correct_answer"] not in ["A", "B", "C", "D"]:
                raise ValueError("Invalid correct answer")

        # Save quiz internally
        latest_quiz = questions
        latest_quiz_topic = request.topic.strip()

        # Clear previous evaluation
        latest_evaluation = None

        # Hide correct answers from student
        student_questions = []

        for index, question in enumerate(questions):

            student_questions.append({
                "question_id": str(index + 1),
                "question": question["question"],
                "options": question["options"],
                "page": question["page"]
            })

        return {
            "topic": latest_quiz_topic,
            "total_questions": len(student_questions),
            "questions": student_questions
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Quiz generation failed: {str(error)}"
        )


# Answer evaluation endpoint
@app.post("/quiz/submit")
def submit_quiz(request: QuizSubmitRequest):

    global latest_evaluation

    if not latest_quiz:
        raise HTTPException(
            status_code=400,
            detail="Please generate a quiz first"
        )

    score = 0
    results = []

    for index, question in enumerate(latest_quiz):

        question_id = str(index + 1)

        student_answer = request.answers.get(
            question_id, ""
        ).strip().upper()

        if student_answer not in ["A", "B", "C", "D", ""]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid answer for question {question_id}"
            )

        correct_answer = question["correct_answer"].strip().upper()

        is_correct = student_answer == correct_answer

        if is_correct:
            score += 1

        results.append({
            "question_id": question_id,
            "student_answer": student_answer or "Not answered",
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": question["explanation"],
            "page": question["page"]
        })

    total = len(latest_quiz)
    percentage = round((score / total) * 100, 2)

    # Save evaluation for gap analysis
    latest_evaluation = {
        "topic": latest_quiz_topic,
        "total_questions": total,
        "correct_answers": score,
        "wrong_answers": total - score,
        "score_percentage": percentage,
        "results": results
    }

    return latest_evaluation


# Gap analysis endpoint
@app.get("/gap-report")
def gap_report():

    if latest_evaluation is None:
        raise HTTPException(
            status_code=400,
            detail="Please generate and submit a quiz first"
        )

    score = latest_evaluation["score_percentage"]

    if score < 40:
        status = "Weak"
        reason = (
            "The student answered less than 40% correctly. "
            "This topic needs focused revision and additional practice."
        )
        recommendation = (
            "Study the topic from the beginning, understand its basic concepts, "
            "and practise simple questions."
        )

    elif score < 75:
        status = "Medium"
        reason = (
            "The student has partial understanding but needs improvement "
            "in some concepts."
        )
        recommendation = (
            "Revise the concepts related to incorrect answers and practise "
            "more application-based questions."
        )

    else:
        status = "Strong"
        reason = (
            "The student answered at least 75% correctly and shows "
            "good understanding of this topic."
        )
        recommendation = (
            "Maintain understanding through quick revision and attempt "
            "more challenging questions."
        )

    weak_questions = []

    for item in latest_evaluation["results"]:
        if not item["is_correct"]:
            weak_questions.append({
                "question_id": item["question_id"],
                "student_answer": item["student_answer"],
                "correct_answer": item["correct_answer"],
                "explanation": item["explanation"],
                "page": item["page"]
            })

    return {
        "topic": latest_evaluation["topic"],
        "score_percentage": score,
        "topic_status": status,
        "reason": reason,
        "recommendation": recommendation,
        "total_questions": latest_evaluation["total_questions"],
        "correct_answers": latest_evaluation["correct_answers"],
        "wrong_answers": latest_evaluation["wrong_answers"],
        "areas_to_improve": weak_questions
    }


# Adaptive revision plan endpoint
@app.get("/revision-plan")
def revision_plan():

    if latest_evaluation is None:
        raise HTTPException(
            status_code=400,
            detail="Please submit a quiz before generating a revision plan"
        )

    report = gap_report()

    status = report["topic_status"]
    topic = report["topic"]

    if status == "Weak":

        tasks = [
            {
                "step": 1,
                "activity": f"Study the basic concepts of {topic}.",
                "duration_minutes": 30
            },
            {
                "step": 2,
                "activity": "Review explanations for all incorrect answers.",
                "duration_minutes": 20
            },
            {
                "step": 3,
                "activity": "Practise basic questions from the uploaded material.",
                "duration_minutes": 20
            },
            {
                "step": 4,
                "activity": "Take another quiz on the same topic.",
                "duration_minutes": 15
            }
        ]

    elif status == "Medium":

        tasks = [
            {
                "step": 1,
                "activity": f"Revise important concepts in {topic}.",
                "duration_minutes": 20
            },
            {
                "step": 2,
                "activity": "Study the explanations for incorrect answers.",
                "duration_minutes": 15
            },
            {
                "step": 3,
                "activity": "Practise application-based questions.",
                "duration_minutes": 20
            },
            {
                "step": 4,
                "activity": "Take another quiz on the same topic.",
                "duration_minutes": 15
            }
        ]

    else:

        tasks = [
            {
                "step": 1,
                "activity": f"Quickly revise the main concepts of {topic}.",
                "duration_minutes": 10
            },
            {
                "step": 2,
                "activity": "Practise advanced questions from the material.",
                "duration_minutes": 20
            },
            {
                "step": 3,
                "activity": "Take another quiz to maintain your progress.",
                "duration_minutes": 15
            }
        ]

    return {
        "topic": topic,
        "current_status": status,
        "current_score": report["score_percentage"],
        "priority": (
            "High" if status == "Weak"
            else "Medium" if status == "Medium"
            else "Low"
        ),
        "total_revision_time_minutes": sum(
            task["duration_minutes"] for task in tasks
        ),
        "revision_tasks": tasks,
        "retest_recommended": True,
        "exam_importance": (
            "Not yet available. Upload past question papers "
            "to analyse actual exam frequency."
        )
    }

