from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import random
import uvicorn
from gtts import gTTS
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class MockInterview:
    def __init__(self, filepath):
        self.filepath = filepath
        self.questions = self.load_questions()
        self.current_questions = []
        self.mandatory_sheets = ["필수"]  # 필수 시트 이름을 설정하세요
        self.audio_dir = "static/audio"
        self.total_q_num = len(self.questions)
        os.makedirs(self.audio_dir, exist_ok=True)  # 오디오 파일을 저장할 디렉토리 생성

    def load_questions(self):
        xl = pd.ExcelFile(self.filepath)
        questions = {}
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)
            questions[sheet] = df.iloc[:, 0].tolist()
        return questions

    def draw_random_questions(self, num_questions):
        self.current_questions.clear()

        mandatory_questions = []
        for sheet in self.mandatory_sheets:
            if sheet in self.questions:
                q_list = self.questions[sheet]
                if q_list:
                    mandatory_questions.append(q_list[0])
                    mandatory_questions.append(q_list[-1])

        available_questions = []
        for sheet, q_list in self.questions.items():
            if sheet not in self.mandatory_sheets:
                if len(q_list) >= num_questions:
                    available_questions.extend(random.sample(q_list, num_questions))
                else:
                    available_questions.extend(random.sample(q_list, len(q_list)))

        self.current_questions = [mandatory_questions[0]] + available_questions + [mandatory_questions[-1]]

        # 오디오 파일 생성
        for i, question in enumerate(self.current_questions):
            self.generate_audio(question, f"question_{i}.mp3")

    def generate_audio(self, text, filename):
        tts = gTTS(text, lang='ko')  # 한국어로 설정
        filepath = os.path.join(self.audio_dir, filename)
        tts.save(filepath)

    def get_next_question(self):
        if not self.current_questions:
            return "더 이상 질문이 없습니다.", ""
        question = self.current_questions.pop(0)
        audio_file = f"/audio/question_{len(self.questions) - len(self.current_questions)}.mp3"
        return question, audio_file


interview = MockInterview('your_excel_file.xlsx')  # Replace with your Excel file path


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "question": "", "audio_file": ""})

@app.post("/next", response_class=HTMLResponse)
async def get_next_question(request: Request):
    question, audio_file = interview.get_next_question()
    return templates.TemplateResponse("index.html", {"request": request, "question": question, "audio_file": audio_file})
@app.post("/draw", response_class=HTMLResponse)
async def draw_questions(request: Request, num_questions: int = Form(...)):
    interview.draw_random_questions(num_questions)
    return templates.TemplateResponse("index.html", {"request": request, "question": "질문이 뽑혔습니다. '다음'을 눌러 시작하세요.", "audio_file": ""})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
