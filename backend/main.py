
@app.post("/topics")
def extract_topics():

    if not vector_store.chunks:
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF first"
        )

    all_topics = []
    batch_size = 10
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
                model="llama-3.1-8b-instant",
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
                response_format={"type": "json_object"}
            )

            result = json.loads(
                response.choices[0].message.content
            )

            all_topics.extend(result.get("units", []))

            print(
                f"Processed batch "
                f"{start // batch_size + 1}"
            )

            if start + batch_size < len(chunks):
                time.sleep(2)

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
                    existing["subtopics"]
                    + topic.get("subtopics", [])
                ))

                existing["pages"] = sorted(set(
                    existing["pages"]
                    + topic.get("pages", [])
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

