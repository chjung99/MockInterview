from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")


class MockInterview:
    def __init__(self, filepath):
        self.filepath = filepath
        self.questions = self.load_questions()
        self.current_questions = []
        self.mandatory_sheets = ["필수"]  # Replace with your mandatory sheet names

    def load_questions(self):
        xl = pd.ExcelFile(self.filepath)
        questions = {}
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)  # Use header=None to include the first row as data
            questions[sheet] = df.iloc[:, 0].tolist()  # assuming questions are in the first column
        return questions

    def draw_random_questions(self, num_questions):
        self.current_questions.clear()

        mandatory_questions = []
        for sheet in self.mandatory_sheets:
            if sheet in self.questions:
                q_list = self.questions[sheet]
                if q_list:
                    mandatory_questions.append(q_list[0])  # First question
                    mandatory_questions.append(q_list[-1])  # Last question

        available_questions = []
        for sheet, q_list in self.questions.items():
            if sheet not in self.mandatory_sheets:
                if len(q_list) >= num_questions:
                    available_questions.extend(random.sample(q_list, num_questions))
                else:
                    available_questions.extend(random.sample(q_list, len(q_list)))

        self.current_questions = [mandatory_questions[0]] + available_questions + [mandatory_questions[-1]]

    def get_next_question(self):
        if not self.current_questions:
            return "No more questions available."
        return self.current_questions.pop(0)


interview = MockInterview('your_excel_file.xlsx')  # Replace with your Excel file path


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "question": ""})


@app.post("/next", response_class=HTMLResponse)
async def get_next_question(request: Request):
    question = interview.get_next_question()
    return templates.TemplateResponse("index.html", {"request": request, "question": question})


@app.post("/draw", response_class=HTMLResponse)
async def draw_questions(request: Request, num_questions: int = Form(...)):
    interview.draw_random_questions(num_questions)
    return templates.TemplateResponse("index.html",
                                      {"request": request, "question": "Questions drawn. Press 'Next' to start."})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
