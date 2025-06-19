from transformers import pipeline
import PyPDF2
def summarize_pdf(pdf_path, max_length=150, min_length=50):
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

        if not text.strip():
            return "Could not extract text from PDF"
        summarizer = pipeline("summarization", model="MBZUAI/LaMini-Flan-T5-248M")
        max_chunk = 1000
        chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]

        summaries = []
        for chunk in chunks[:3]:
            if len(chunk.strip()) > 50:
                try:
                    summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
                    summaries.append(summary[0]['summary_text'])
                except:
                    continue

        return " ".join(summaries) if summaries else "Could not generate summary"

    except ImportError:
        return "Transformers library not installed. Run: pip install transformers torch"
    except Exception as e:
        return f"Error with Hugging Face model: {str(e)}"
