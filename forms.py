from wtforms import Form, IntegerField, StringField, SubmitField, SelectField


class NewSetForm(Form):
    Name = StringField("Name")
    Submit = SubmitField("Submit")


class NewCardForm(Form):
    Term = StringField("Term")
    Definition = StringField("Definition")
    Submit = SubmitField("Submit")

class SubmitForm(Form):
    Submit = SubmitField("Submit")

class ChooseSetForm(Form):
    Choice = SelectField("Choose a flashcard set", choices=[])
    Submit = SubmitField("Submit")

class StudySetForm(Form):
    Answer = StringField("Answer")
    Submit = SubmitField("Submit")



