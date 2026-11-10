"use client";

import { useState } from "react";

const API =
 "https://gapfinder-ai-4bom.onrender.com";

type QuizQuestion = {
  question_id: string | number;
  question: string;
  options: Record<string, string>;
  page?: number;
};

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [topic, setTopic] = useState("Cryptographic Attacks");
  const [question, setQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState<any>(null);

  const [result, setResult] = useState<any>(null);
  const [gapReport, setGapReport] = useState<any>(null);
  const [revisionPlan, setRevisionPlan] = useState<any>(null);
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [evaluation, setEvaluation] = useState<any>(null);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function requestApi(
    path: string,
    options?: RequestInit
  ): Promise<any> {
    setLoading(true);
    setMessage("");
    setResult(null);

    try {
      const response = await fetch(`${API}${path}`, options);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || data.message || "Something went wrong."
        );
      }

      setMessage("Completed successfully!");
      return data;
    } catch (error: any) {
      setMessage(error.message || "Unable to connect to the backend.");
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function uploadPdf() {
    if (!file) {
      setMessage("Please select a PDF file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const data = await requestApi("/upload", {
      method: "POST",
      body: formData,
    });

    if (data) {
      setResult(data);
      setQuizQuestions([]);
      setAnswers({});
      setEvaluation(null);
      setChatAnswer(null);
    }
  }

  async function extractTopics() {
    const data = await requestApi("/topics", {
      method: "POST",
    });

    if (data) {
      setResult(data);
    }
  }

  async function generateQuiz() {
    if (!topic.trim()) {
      setMessage("Please enter a topic.");
      return;
    }

    setEvaluation(null);
    setAnswers({});

    const data = await requestApi("/quiz/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic: topic,
        number_of_questions: 5,
      }),
    });

    if (data) {
      setQuizQuestions(data.questions || []);
      setResult(data);

      if (!data.questions || data.questions.length === 0) {
        setMessage("No quiz questions were returned. Try another topic.");
      }
    }
  }

  async function submitQuiz() {
    if (quizQuestions.length === 0) {
      setMessage("Generate a quiz first.");
      return;
    }

    if (Object.keys(answers).length !== quizQuestions.length) {
      setMessage("Please answer all questions before submitting.");
      return;
    }

    const data = await requestApi("/quiz/submit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        answers: answers,
      }),
    });

    if (data) {
      setEvaluation(data);
      setResult(data);
    }
  }
async function getGapReport() {
  const data = await requestApi("/gap-report");

  if (data) {
    setGapReport(data);
  }
}

async function getRevisionPlan() {
  const data = await requestApi("/revision-plan");

  if (data) {
    setRevisionPlan(data);
  }
}

  async function askQuestion() {
    if (!question.trim()) {
      setMessage("Please enter your question.");
      return;
    }

    setLoading(true);
    setMessage("");
    setChatAnswer(null);

    try {
      const response = await fetch(`${API}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        // The backend expects "message", not "question".
        body: JSON.stringify({
          message: question,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Chat request failed.");
      }

      setChatAnswer(data);
      setMessage("Answer received successfully!");
    } catch (error: any) {
      setMessage(error.message || "Unable to connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  function formatResult(data: any) {
    return JSON.stringify(data, null, 2);
  }

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-8 text-slate-800">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8 rounded-2xl bg-slate-900 px-6 py-8 text-white shadow">
          <h1 className="text-3xl font-bold">GapFinder AI</h1>
          <p className="mt-2 text-lg text-slate-200">
            Find what the student doesn't know.
          </p>
          <p className="mt-3 text-sm text-slate-300">
            Upload study materials, test your knowledge, identify weak
            topics, and improve your learning.
          </p>
        </header>

        {message && (
          <div className="mb-5 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
            {message}
          </div>
        )}

        {loading && (
          <div className="mb-5 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
            Please wait. Processing your request...
          </div>
        )}

        <div className="grid gap-5 md:grid-cols-2">
          {/* 1. Upload Study Material */}
          <section className="rounded-xl bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">
              1. Upload Study Material
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Upload your syllabus, textbook, or study notes in PDF format.
            </p>

            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="mt-5 block w-full rounded-lg border border-slate-300 p-2 text-sm"
            />

            {file && (
              <p className="mt-2 text-xs text-slate-500">
                Selected file: {file.name}
              </p>
            )}

            <button
              onClick={uploadPdf}
              disabled={loading || !file}
              className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Upload PDF
            </button>
          </section>

          {/* 2. Extract Topics */}
          <section className="rounded-xl bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">2. Extract Topics</h2>
            <p className="mt-2 text-sm text-slate-600">
              Identify important topics from your uploaded study material.
            </p>

            <button
              onClick={extractTopics}
              disabled={loading}
              className="mt-5 w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Extract Topics
            </button>

            <p className="mt-3 text-xs text-slate-500">
              Topic extraction may take a few minutes for large PDFs.
            </p>
          </section>

          {/* 3. Generate Quiz */}
          <section className="rounded-xl bg-white p-6 shadow-sm md:col-span-2">
            <h2 className="text-xl font-semibold">3. Generate Quiz</h2>
            <p className="mt-2 text-sm text-slate-600">
              Generate multiple-choice questions from your uploaded material.
            </p>

            <label className="mt-4 block text-sm font-medium">
              Enter topic
            </label>

            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Example: Cryptographic Attacks"
              className="mt-2 w-full rounded-lg border border-slate-300 p-3"
            />

            <button
              onClick={generateQuiz}
              disabled={loading}
              className="mt-4 rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Generate 5 Questions
            </button>

            {quizQuestions.length > 0 && (
              <div className="mt-6 space-y-5">
                <h3 className="text-lg font-semibold">Quiz Questions</h3>

                {quizQuestions.map((item, index) => {
                  const questionId = String(item.question_id);

                  return (
                    <div
                      key={questionId}
                      className="rounded-lg border border-slate-200 p-4"
                    >
                      <p className="font-medium">
                        {index + 1}. {item.question}
                      </p>

                      <div className="mt-3 space-y-2">
                        {Object.entries(item.options || {}).map(
                          ([optionKey, optionValue]) => (
                            <label
                              key={optionKey}
                              className="flex cursor-pointer items-start gap-3 rounded-lg p-2 hover:bg-slate-50"
                            >
                              <input
                                type="radio"
                                name={`question-${questionId}`}
                                value={optionKey}
                                checked={answers[questionId] === optionKey}
                                onChange={() =>
                                  setAnswers((previous) => ({
                                    ...previous,
                                    [questionId]: optionKey,
                                  }))
                                }
                                className="mt-1"
                              />
                              <span className="text-sm">
                                <strong>{optionKey}.</strong> {optionValue}
                              </span>
                            </label>
                          )
                        )}
                      </div>

                      {item.page && (
                        <p className="mt-2 text-xs text-slate-500">
                          Source: Page {item.page}
                        </p>
                      )}
                    </div>
                  );
                })}

                <button
                  onClick={submitQuiz}
                  disabled={loading}
                  className="w-full rounded-lg bg-green-600 px-5 py-3 font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Submit Quiz
                </button>
              </div>
            )}

            {evaluation && (
              <div className="mt-5 rounded-lg border border-green-200 bg-green-50 p-4">
                <h3 className="font-semibold text-green-900">
                  Quiz Evaluation
                </h3>
                <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-sm text-slate-700">
                  {formatResult(evaluation)}
                </pre>
              </div>
            )}
          </section>

          {/* 4. Knowledge Gap Report */}
          <section className="rounded-xl bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">
              4. Knowledge Gap Report
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Find your strong, medium, and weak topics based on quiz results.
            </p>

            <button
              onClick={getGapReport}
              disabled={loading}
              className="mt-5 w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Generate Gap Report
            </button>
                       {gapReport && (
              <div className="mt-5 rounded-lg border border-blue-200 bg-blue-50 p-4">
                <h3 className="text-lg font-bold text-blue-900">
                  Knowledge Gap Report
                </h3>

                <p className="mt-3"><strong>Topic:</strong> {gapReport.topic}</p>
                <p><strong>Score:</strong> {gapReport.score_percentage}%</p>
                <p><strong>Status:</strong> {gapReport.topic_status}</p>
                <p><strong>Total Questions:</strong> {gapReport.total_questions}</p>
                <p><strong>Correct Answers:</strong> {gapReport.correct_answers}</p>
                <p><strong>Wrong Answers:</strong> {gapReport.wrong_answers}</p>

                <p className="mt-3"><strong>Reason:</strong> {gapReport.reason}</p>
                <p className="mt-2"><strong>Recommendation:</strong> {gapReport.recommendation}</p>

                <h4 className="mt-4 font-semibold">Areas to Improve</h4>

                {gapReport.areas_to_improve?.map((item: any) => (
                  <div key={item.question_id} className="mt-3 rounded-lg bg-white p-3 text-sm">
                    <p><strong>Question:</strong> {item.question_id}</p>
                    <p><strong>Your Answer:</strong> {item.student_answer}</p>
                    <p><strong>Correct Answer:</strong> {item.correct_answer}</p>
                    <p><strong>Explanation:</strong> {item.explanation}</p>
                    <p><strong>Page:</strong> {item.page}</p>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* 5. Revision Plan */}
          <section className="rounded-xl bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">
              5. Personalized Revision Plan
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Get a revision plan based on your quiz performance.
            </p>

            <button
              onClick={getRevisionPlan}
              disabled={loading}
              className="mt-5 w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Generate Revision Plan
            </button>
                       {revisionPlan && (
              <div className="mt-5 rounded-lg border border-green-200 bg-green-50 p-4">
                <h3 className="text-lg font-bold text-green-900">
                  Personalized Revision Plan
                </h3>

                <p className="mt-3">
                  <strong>Topic:</strong> {revisionPlan.topic}
                </p>

                <p>
                  <strong>Current Status:</strong> {revisionPlan.current_status}
                </p>

                <p>
                  <strong>Current Score:</strong> {revisionPlan.current_score}%
                </p>

                <p>
                  <strong>Priority:</strong> {revisionPlan.priority}
                </p>

                <p>
                  <strong>Total Revision Time:</strong>{" "}
                  {revisionPlan.total_revision_time_minutes} minutes
                </p>

                <h4 className="mt-4 font-semibold">Revision Tasks</h4>

                {revisionPlan.revision_tasks?.map((task: any) => (
                  <div
                    key={task.step}
                    className="mt-3 rounded-lg bg-white p-3 text-sm"
                  >
                    <p><strong>Step {task.step}:</strong> {task.activity}</p>
                    <p><strong>Duration:</strong> {task.duration_minutes} minutes</p>
                  </div>
                ))}

                <p className="mt-3">
                  <strong>Retest Recommended:</strong>{" "}
                  {revisionPlan.retest_recommended ? "Yes" : "No"}
                </p>

                <p className="mt-2">
                  <strong>Exam Importance:</strong>{" "}
                  {revisionPlan.exam_importance}
                </p>
              </div>
            )}
          </section>

          {/* 6. Ask AI Assistant */}
          <section className="rounded-xl bg-white p-6 shadow-sm md:col-span-2">
            <h2 className="text-xl font-semibold">6. Ask AI Assistant</h2>
            <p className="mt-2 text-sm text-slate-600">
              Ask questions about your uploaded study material.
            </p>

            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Example: Explain the different types of security attacks."
              rows={3}
              className="mt-4 w-full rounded-lg border border-slate-300 p-3"
            />

            <button
              onClick={askQuestion}
              disabled={loading}
              className="mt-3 rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Ask Question
            </button>

            {chatAnswer && (
              <div className="mt-5 rounded-lg border border-blue-200 bg-blue-50 p-4">
                <h3 className="font-semibold">AI Assistant Answer</h3>

                <p className="mt-3 whitespace-pre-wrap text-sm leading-6">
                  {chatAnswer.answer ||
                    (typeof chatAnswer === "string"
                      ? chatAnswer
                      : formatResult(chatAnswer))}
                </p>

                {chatAnswer.sources && (
                  <div className="mt-4">
                    <h4 className="font-semibold text-sm">Sources</h4>
                    <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs">
                      {formatResult(chatAnswer.sources)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>

        {/* General API result */}
        {result && (
          <section className="mt-6 rounded-xl bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold">Latest Result</h2>
            <pre className="mt-3 max-h-96 overflow-auto rounded-lg bg-slate-900 p-4 text-xs text-green-300">
              {formatResult(result)}
            </pre>
          </section>
        )}

        <footer className="mt-8 text-center text-sm text-slate-500">
          GapFinder AI - Personalized Student Learning Assistant
        </footer>
      </div>
    </main>
  );
}
