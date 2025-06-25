from transformers import pipeline
import PyPDF2

from langchain.text_splitter import RecursiveCharacterTextSplitter

def summarize_pdf(pdf_path, max_length=150, min_length=40):

    try:

        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            if not pdf_reader.pages:
                return "PDF is empty or could not be read."
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():
            return "Could not extract text from PDF."


        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len
        )
        chunks = text_splitter.split_text(text)

        if not chunks:
            return "Text was extracted, but could not be split into chunks."


        summarizer = pipeline("summarization", model="MBZUAI/LaMini-Flan-T5-248M")


        print(f"Summarizing {len(chunks)} chunks...")
        initial_summaries = []
        for i, chunk in enumerate(chunks):

            prompt = f"Summarize the following text:\n\n{chunk}"
            try:
                summary = summarizer(prompt, max_length=max_length, min_length=min_length, do_sample=False)
                initial_summaries.append(summary[0]['summary_text'])
                print(f"  - Summarized chunk {i+1}/{len(chunks)}")
            except Exception as e:
                print(f"  - Could not summarize chunk {i+1}. Error: {e}")
                continue

        if not initial_summaries:
            return "Could not generate any initial summaries from the chunks."


        print("\nSynthesizing the final summary...")
        combined_summaries = "\n".join(initial_summaries)


        final_summary_prompt = f"The following are several summaries from a long document. Please create a single, cohesive, and final summary that incorporates the key points from all of them.\n\n{combined_summaries}"

        final_summary_chunks = text_splitter.split_text(final_summary_prompt)

        final_summary_text = ""
        if final_summary_chunks:
            try:
                final_summary = summarizer(final_summary_chunks[0], max_length=300, min_length=100, do_sample=False)
                final_summary_text = final_summary[0]['summary_text']
            except Exception as e:
                return f"Error during final summarization: {e}"

        return final_summary_text if final_summary_text else "Could not generate a final summary."

    except FileNotFoundError:
        return f"Error: The file at {pdf_path} was not found."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
