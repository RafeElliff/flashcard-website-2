from wtforms import Form, IntegerField, StringField, SubmitField, SelectField


class NewSetForm(Form):
    Name = StringField("Name")
    Submit = SubmitField("Submit")


class NewCardForm(Form):
    Term = StringField("Term")
    Definition = StringField("Definition")
    Submit = SubmitField("Submit")