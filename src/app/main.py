import dal
import schemas
from fastapi import Depends, FastAPI, HTTPException
from settings import SessionLocal
from sqlalchemy.orm import Session

# Create tables if they don't exist (though Alembic is preferred)
# models_db.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/register/student", response_model=schemas.StudentRegister)
def register_student(student: schemas.StudentRegister, db: Session = Depends(get_db)):
    # Check if user exists logic could be added here
    return dal.create_student(db=db, student=student)


@app.post("/register/teacher", response_model=schemas.TeacherRegister)
def register_teacher(teacher: schemas.TeacherRegister, db: Session = Depends(get_db)):
    # Check if user exists logic could be added here
    return dal.create_teacher(db=db, teacher=teacher)


@app.post("/tests/", response_model=schemas.TestResponse)
def create_test_endpoint(test: schemas.TestCreate, db: Session = Depends(get_db)):
    return dal.create_test(db=db, test=test)


@app.get("/tests/{test_id}/questions", response_model=list[schemas.QuestionResponse])
def read_test_questions(test_id: str, db: Session = Depends(get_db)):
    questions = dal.get_questions_by_test_id(db, test_id)
    return questions


@app.post("/questions/", response_model=schemas.QuestionResponse)
def create_question(question: schemas.QuestionCreate, db: Session = Depends(get_db)):
    return dal.create_question(db=db, question=question)


@app.post("/classes/", response_model=schemas.ClassResponse)
def create_class(class_: schemas.ClassCreate, db: Session = Depends(get_db)):
    return dal.create_class(db=db, class_=class_)


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: str, db: Session = Depends(get_db)):
    db_user = dal.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
