
# GapFinder AI – AI-Powered Personalized Learning Assistant

## Project Overview

GapFinder AI is an AI-powered personalized learning platform designed to identify what students don't know.

Instead of studying every topic equally, students can upload their study materials, take AI-generated quizzes, identify weak areas, and receive personalized revision plans.

The main goal is to help students focus on topics that need improvement.

## Problem Statement

Students often spend equal time revising all topics without knowing their actual knowledge gaps. GapFinder AI addresses this problem by analyzing quiz performance and generating topic-level feedback and revision recommendations.

## Key Features

1. **PDF Upload:** Upload study materials in PDF format.
2. **Topic Extraction:** Automatically extract important topics from uploaded materials.
3. **AI Chat Assistant:** Ask questions about the uploaded study material.
4. **Quiz Generation:** Generate questions based on the uploaded content.
5. **Quiz Evaluation:** Evaluate student answers and provide explanations.
6. **Knowledge Gap Report:** Identify weak areas based on quiz performance.
7. **Personalized Revision Plan:** Generate prioritized revision tasks with estimated study time.

## Technology Stack

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend
- Python
- FastAPI

### AI and Machine Learning
- Groq LLM API
- Retrieval-Augmented Generation (RAG)
- TF-IDF
- Scikit-learn

### PDF Processing
- PyPDF

### Deployment
- Frontend: Vercel
- Backend: Render

## How It Works

1. Student uploads a PDF study material.
2. Backend extracts text and divides it into smaller chunks.
3. TF-IDF-based retrieval helps identify relevant content.
4. Groq LLM generates topic-related responses and quiz questions using retrieved context.
5. Student attempts the generated quiz.
6. Backend evaluates answers and identifies weak areas.
7. GapFinder AI generates a personalized revision plan.

### Core Workflow

Upload Material → Extract Topics → Generate Quiz → Evaluate Answers → Identify Knowledge Gaps → Personalized Revision Plan

## Project Structure

```text
GapFinder-AI/
│
├── backend/
│   ├── main.py
│   ├── rag.py
│   ├── vector_store.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── package.json
│   └── ...
│
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/nagalakshmi-madhavi/GapFinder-AI.git
cd GapFinder-AI
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the backend folder:

```env
GROQ_API_KEY=your_groq_api_key
```

Start the backend:

```bash
uvicorn main:app --reload
```

Backend API documentation:

http://127.0.0.1:8000/docs

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the application:

http://localhost:3000

## Live Deployment

- **Frontend:** https://gap-finder-ai-ten.vercel.app/
- **Backend API:** https://gapfinder-ai-4bom.onrender.com/
- **API Documentation:** https://gapfinder-ai-4bom.onrender.com/docs

## GitHub Repository

https://github.com/nagalakshmi-madhavi/GapFinder-AI

## Future Enhancements

- Student login and authentication.
- Progress tracking across multiple quiz attempts.
- Past question paper analysis.
- Exam importance-based topic prioritization.
- Teacher dashboard and class-level analytics.
- Spaced repetition and revision reminders.

## Conclusion

GapFinder AI transforms traditional studying into a personalized learning experience by identifying knowledge gaps and helping students focus on the topics they need to improve.

**Upload → Test → Diagnose → Revise → Improve**
