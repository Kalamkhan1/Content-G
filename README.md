
## Content-G

### Description
Content-G is an innovative AI-powered content generator designed to automatically convert educational books, articles, and research papers into narrated video summaries in local languages. Leveraging advanced AI models, vector databases, and animation libraries, the tool simplifies complex content into engaging and accessible educational videos.

The process includes:
1. Generating a summary of the provided concept, research paper, or article.
2. Creating a script based on the generated summary.
3. Translating the script into a local language and converting it into audio.
4. Generating animations using the Manim library based on the script.
5. Merging the audio and video to produce a complete narrated video summary.

### Technologies Used
- **LangChain**: For building and managing the conversational AI pipeline.
- **Gemini API**: Using Gemini Flash's latest model to create agentic AI.
- **RAG (Retrieval-Augmented Generation)**: For improving knowledge retrieval and summary generation.
- **Vector Database**: To store and retrieve contextually relevant data.
- **Manim**: For generating educational animations based on the generated scripts.
- **TranslatePy**: For translating scripts into local languages.
- **gTTS**: For converting translated text into speech.
- **MoviePy**: For merging audio and video into a single narrated video.

### Features
- Summarizes complex educational content into easily digestible scripts.
- Supports multilingual translation for wider accessibility.
- Automatically generates animations to visually explain concepts.
- Provides narrated video summaries that combine text, visuals, and audio seamlessly.

### Future Plans
- Fine-tuning the AI model for improved summarization and script generation.
- Incorporating **Stable Diffusion** for generating high-quality images to enhance animations.
- Developing a user-friendly interface for easier interaction.

### Installation
#### Requirements:
- Python 3.8+
- Dependencies: LangChain, Manim, MoviePy, gTTS, TranslatePy, vector database libraries, and Gemini API setup.

#### Steps:
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Content-G
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the Gemini API and vector database configuration.
4. Run the application:
   ```bash
   streamlit run app.py --server.fileWatcherType none
   ```
5. To use RAG, provide a file path of a pdf. (eg: C:/users/..../file.pdf) 
   NOTE: provide file path without apostrophes

### Authors and Acknowledgment
- Mohammed Abdul Kalam Khan
- Abdul Hai
- Mahammed Saadullah

### License
Apache License 2.0

### Project Status
Actively under development 

## Usage Example

check out the following files in repository
final_output.mp4

